"""
邮件发送模块（基于 Resend）。

需要在环境变量中配置：
  RESEND_API_KEY   — Resend API key（必填）
  EMAIL_FROM       — 发件人地址，如 noreply@urea-king.com（必填）
  SITE_URL         — 本站完整域名，用于生成邮件链接，如 https://urea-king-staging.onrender.com
                     （不配置则回退到 POKER_URL，再回退到默认值）
"""

import logging
import os
from html import escape as html_escape

import resend

from core import settings

logger = logging.getLogger(__name__)

resend.api_key = os.environ.get("RESEND_API_KEY", "")
_FROM = os.environ.get("EMAIL_FROM", "noreply@urea-king.com")
# SITE_URL 专门用于邮件链接，与首页 POKER 按钮跳转用的 POKER_URL 独立
_POKER_URL = (
    os.environ.get("SITE_URL")
    or os.environ.get("POKER_URL", "https://poker.urea-king.com")
).rstrip("/")

# 测试环境必须配置自己的地址：否则验证、重置链接会默认指向线上网站，
# 测试库里生成的令牌被发往线上（线上找不到，链接失效），也容易把人引到错误的网站
if settings.IS_STAGING and not (os.environ.get("SITE_URL") or os.environ.get("POKER_URL")):
    raise RuntimeError("Staging requires SITE_URL (or POKER_URL) so email links point to the staging site.")


def dispatch(background_tasks, send_func, *args):
    """
    有 background_tasks 时放到响应返回之后再发，否则立即发送。
    找回密码、重发验证用它：响应时间不再因"是否真的发了邮件"而不同，
    别人无法从快慢判断邮箱是否注册。
    """
    if background_tasks is not None:
        background_tasks.add_task(send_func, *args)
    else:
        send_func(*args)


def mask_email(address: str) -> str:
    """日志里只记录打码后的邮箱，如 pe***@osu.edu。"""
    local, _, domain = (address or "").partition("@")
    if not domain:
        return "***"
    return f"{local[:2]}***@{domain}"


def _send(to: str, subject: str, html: str) -> bool:
    """底层发送，返回是否成功。"""
    if not resend.api_key:
        logger.warning("RESEND_API_KEY 未配置，跳过邮件发送（to=%s）", mask_email(to))
        return False
    try:
        resend.Emails.send({
            "from": _FROM,
            "to": [to],
            "subject": subject,
            "html": html,
        })
        return True
    except Exception as e:
        logger.error("邮件发送失败 to=%s: %s", mask_email(to), e)
        return False


def send_verify_email(to: str, token: str, username: str = "") -> bool:
    """发送邮箱验证邮件（中英双语）。写明是哪个账号，同一个邮箱有多个账号在等验证时不会混淆。"""
    link = f"{_POKER_URL}/verify-email?token={token}"
    account_line = (
        f'<p>账号 / Account：<strong>{html_escape(username)}</strong><br>'
        '<span style="color:#888;font-size:13px;">如果这不是你注册的账号，请不要点击。'
        " If this isn't the account you registered, don't click.</span></p>"
        if username else ""
    )
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:32px;">
      <h2 style="letter-spacing:2px;">UREAKING POKER</h2>
      <p>感谢注册！请点击下方链接验证您的邮箱：<br>
         <span style="color:#888;font-size:13px;">Thank you for registering! Please click the link below to verify your email:</span>
      </p>
      {account_line}
      <p style="margin:24px 0;">
        <a href="{link}"
           style="background:#111;color:#fff;padding:12px 28px;border-radius:8px;
                  text-decoration:none;font-weight:bold;font-size:15px;">
          验证邮箱 / Verify Email
        </a>
      </p>
      <p style="color:#888;font-size:13px;">
        链接 15 分钟内有效，且只能使用一次。如果您没有注册过 Ureaking Poker，请忽略此邮件。<br>
        The link is valid for 15 minutes and can only be used once. If you did not register for Ureaking Poker, please ignore this email.
      </p>
    </div>
    """
    return _send(to, "验证您的 Ureaking Poker 邮箱 / Verify Your Ureaking Poker Email", html)


def send_reset_password(to: str, token: str) -> bool:
    """发送密码重置邮件（中英双语）。"""
    link = f"{_POKER_URL}/reset-password?token={token}"
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:32px;">
      <h2 style="letter-spacing:2px;">UREAKING POKER</h2>
      <p>我们收到了您的密码重置请求，请点击下方链接设置新密码：<br>
         <span style="color:#888;font-size:13px;">We received a password reset request. Please click the link below to set a new password:</span>
      </p>
      <p style="margin:24px 0;">
        <a href="{link}"
           style="background:#111;color:#fff;padding:12px 28px;border-radius:8px;
                  text-decoration:none;font-weight:bold;font-size:15px;">
          重置密码 / Reset Password
        </a>
      </p>
      <p style="color:#888;font-size:13px;">
        链接 15 分钟内有效，且只能使用一次。如果您没有发起过密码重置请求，请忽略此邮件。<br>
        The link is valid for 15 minutes and can only be used once. If you did not request a password reset, please ignore this email.
      </p>
    </div>
    """
    return _send(to, "重置您的 Ureaking Poker 密码 / Reset Your Ureaking Poker Password", html)


def send_change_email_confirm(to: str, token: str, username: str = "") -> bool:
    """更换邮箱：发到新邮箱的确认链接（中英双语）。"""
    link = f"{_POKER_URL}/verify-email?token={token}"
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:32px;">
      <h2 style="letter-spacing:2px;">UREAKING POKER</h2>
      <p>账号 <strong>{html_escape(username)}</strong> 申请把登录邮箱更换为这个邮箱。请点击下方链接确认：<br>
         <span style="color:#888;font-size:13px;">The account <strong>{html_escape(username)}</strong> asked to use this address as its email. Please click the link below to confirm:</span>
      </p>
      <p style="margin:24px 0;">
        <a href="{link}"
           style="background:#111;color:#fff;padding:12px 28px;border-radius:8px;
                  text-decoration:none;font-weight:bold;font-size:15px;">
          确认更换邮箱 / Confirm Email Change
        </a>
      </p>
      <p style="color:#888;font-size:13px;">
        链接 30 分钟内有效，且只能使用一次。确认之前原邮箱继续有效。如果不是你本人操作，请忽略此邮件。<br>
        The link is valid for 30 minutes and can only be used once. Your current email stays in use until you confirm. If you didn't request this, please ignore this email.
      </p>
    </div>
    """
    return _send(to, "确认更换 Ureaking Poker 邮箱 / Confirm Your New Ureaking Poker Email", html)


def send_email_changed_notice(to: str, username: str, new_email: str) -> bool:
    """更换邮箱生效后，通知原邮箱（新邮箱只显示打码后的地址）。"""
    masked = html_escape(mask_email(new_email))
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:32px;">
      <h2 style="letter-spacing:2px;">UREAKING POKER</h2>
      <p>账号 <strong>{html_escape(username)}</strong> 的登录邮箱已更换为 <strong>{masked}</strong>，以后找回密码的邮件会发到新邮箱。<br>
         <span style="color:#888;font-size:13px;">The email of account <strong>{html_escape(username)}</strong> has been changed to <strong>{masked}</strong>. Password reset emails will go to the new address from now on.</span>
      </p>
      <p style="color:#888;font-size:13px;">
        如果不是你本人操作，你的账号可能已被他人登录，请尽快联系管理员。<br>
        If you didn't do this, someone else may have signed in to your account. Please contact the administrator as soon as possible.
      </p>
    </div>
    """
    return _send(to, "你的 Ureaking Poker 邮箱已更换 / Your Ureaking Poker Email Was Changed", html)

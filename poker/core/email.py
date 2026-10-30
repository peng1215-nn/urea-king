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


def send_verify_email(to: str, token: str) -> bool:
    """发送邮箱验证邮件（中英双语）。"""
    link = f"{_POKER_URL}/verify-email?token={token}"
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:32px;">
      <h2 style="letter-spacing:2px;">UREAKING POKER</h2>
      <p>感谢注册！请点击下方链接验证您的邮箱：<br>
         <span style="color:#888;font-size:13px;">Thank you for registering! Please click the link below to verify your email:</span>
      </p>
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

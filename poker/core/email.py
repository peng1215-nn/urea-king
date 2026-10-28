"""
邮件发送模块（基于 Resend）。

需要在环境变量中配置：
  RESEND_API_KEY   — Resend API key（必填）
  EMAIL_FROM       — 发件人地址，如 noreply@urea-king.com（必填）
  POKER_URL        — 用于生成邮件中的链接，如 https://poker.urea-king.com
"""

import logging
import os

import resend

logger = logging.getLogger(__name__)

resend.api_key = os.environ.get("RESEND_API_KEY", "")
_FROM = os.environ.get("EMAIL_FROM", "noreply@urea-king.com")
_POKER_URL = os.environ.get("POKER_URL", "https://poker.urea-king.com").rstrip("/")


def _send(to: str, subject: str, html: str) -> bool:
    """底层发送，返回是否成功。"""
    if not resend.api_key:
        logger.warning("RESEND_API_KEY 未配置，跳过邮件发送（to=%s）", to)
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
        logger.error("邮件发送失败 to=%s: %s", to, e)
        return False


def send_verify_email(to: str, token: str) -> bool:
    """发送邮箱验证邮件。"""
    link = f"{_POKER_URL}/verify-email?token={token}"
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:32px;">
      <h2 style="letter-spacing:2px;">UREAKING POKER</h2>
      <p>感谢注册！请点击下方链接验证您的邮箱：</p>
      <p style="margin:24px 0;">
        <a href="{link}"
           style="background:#fff;color:#111;padding:12px 28px;border-radius:8px;
                  text-decoration:none;font-weight:bold;font-size:15px;">
          验证邮箱
        </a>
      </p>
      <p style="color:#888;font-size:13px;">链接 15 分钟内有效，且只能使用一次。<br>
         如果您没有注册过 Ureaking Poker，请忽略此邮件。</p>
    </div>
    """
    return _send(to, "验证您的 Ureaking Poker 邮箱", html)


def send_reset_password(to: str, token: str) -> bool:
    """发送密码重置邮件。"""
    link = f"{_POKER_URL}/reset-password?token={token}"
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:32px;">
      <h2 style="letter-spacing:2px;">UREAKING POKER</h2>
      <p>我们收到了您的密码重置请求，请点击下方链接设置新密码：</p>
      <p style="margin:24px 0;">
        <a href="{link}"
           style="background:#fff;color:#111;padding:12px 28px;border-radius:8px;
                  text-decoration:none;font-weight:bold;font-size:15px;">
          重置密码
        </a>
      </p>
      <p style="color:#888;font-size:13px;">链接 15 分钟内有效，且只能使用一次。<br>
         如果您没有发起过密码重置请求，请忽略此邮件。</p>
    </div>
    """
    return _send(to, "重置您的 Ureaking Poker 密码", html)

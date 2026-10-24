"""
账号相关的安全小工具：登录状态与密码绑定、统一耗时的密码校验。
"""

import hashlib
import hmac

from passlib.context import CryptContext

from core import settings


# 全站唯一的密码哈希配置；其他地方都从这里导入，不要另建
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# 用户名不存在时也做一次同样耗时的校验，避免通过响应时间判断用户名是否存在
_DUMMY_HASH = pwd_context.hash("dummy-password-for-timing")


def password_fingerprint(password_hash):
    """
    由密码哈希派生的短指纹，登录时存进会话。
    密码一旦修改（本人修改、管理员重置、注销），指纹就变了，
    所有设备上的旧登录都会在下一次请求时失效。
    用会话密钥做 HMAC：会话内容虽然有签名但可被读取，不直接暴露哈希。
    """
    key = settings.SESSION_SECRET_KEY.encode()
    return hmac.new(key, (password_hash or "").encode(), hashlib.sha256).hexdigest()[:32]


def fingerprint_matches(password_hash, fingerprint):
    if not fingerprint:
        return False
    return hmac.compare_digest(password_fingerprint(password_hash), fingerprint)


def verify_user_password(user, password):
    """user 为 None 时也执行一次哈希校验，再返回 False。"""
    if user is None:
        pwd_context.verify(password or "", _DUMMY_HASH)
        return False
    return pwd_context.verify(password or "", user.password_hash)

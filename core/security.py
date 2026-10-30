"""
账号相关的安全小工具：登录状态与密码绑定、统一耗时的密码校验。
"""

import hashlib
import hmac

import bcrypt

from core import settings


def _verify_pbkdf2_sha256(password: str, hashed: str) -> bool:
    """兼容迁移前 passlib pbkdf2_sha256 哈希的校验。
    格式：$pbkdf2-sha256$rounds$salt$hash（base64url，无填充）
    """
    try:
        import hashlib as _hl
        import base64
        parts = hashed.split("$")
        # $pbkdf2-sha256$rounds$salt$digest — 分割后 ['', 'pbkdf2-sha256', rounds, salt, digest]
        if len(parts) != 5 or parts[1] != "pbkdf2-sha256":
            return False
        rounds = int(parts[2])
        # passlib 用 base64url（ab64）：把 "." 换回 "+"，再补 "=" 填充
        def ab64_decode(s):
            s = s.replace(".", "+")
            pad = (4 - len(s) % 4) % 4
            return base64.b64decode(s + "=" * pad)
        salt = ab64_decode(parts[3])
        expected = ab64_decode(parts[4])
        dk = _hl.pbkdf2_hmac("sha256", password.encode(), salt, rounds)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


class _BcryptContext:
    """bcrypt 封装，提供与 passlib CryptContext 相同的 .hash() / .verify() 接口。
    验证时兼容迁移前的 pbkdf2_sha256 哈希，新哈希全部用 bcrypt。
    """

    ROUNDS = 12

    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(self.ROUNDS)).decode()

    def verify(self, password: str, hashed: str) -> bool:
        try:
            if (hashed or "").startswith("$pbkdf2-sha256$"):
                return _verify_pbkdf2_sha256(password, hashed)
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except Exception:
            return False


# 全站唯一的密码哈希配置；其他地方都从这里导入，不要另建
pwd_context = _BcryptContext()

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

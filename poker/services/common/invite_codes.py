"""
邀请码由系统生成，不再由局头或管理员手填：手填的码往往很短（如 "1"、"abc"），容易被猜中。

12 位，字符取自 31 个不易混淆的大写字母和数字（去掉 0/O、1/I/L），约 59 位随机性，
按全站每 15 分钟最多 300 次猜码计算，猜中一个码需要几十亿年。
"""

import secrets

from poker.models import InvitationCode


ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 12


def generate_invite_code(db):
    """生成一个库里还不存在的邀请码（重复的概率极低，仍然检查一下）。"""
    for _ in range(10):
        code = "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))
        if db.query(InvitationCode.id).filter(InvitationCode.code == code).first() is None:
            return code
    raise RuntimeError("could not generate a unique invite code")


def normalize_invite_code(db, code):
    """
    用户输入的邀请码：先按原样查（兼容以前手填的码），查不到再按大写查，
    这样输入系统生成的码时不用在意大小写。
    """
    code = (code or "").strip()
    if not code:
        return code
    if db.query(InvitationCode.id).filter(InvitationCode.code == code).first() is not None:
        return code
    upper = code.upper()
    if upper != code and db.query(InvitationCode.id).filter(InvitationCode.code == upper).first() is not None:
        return upper
    return code


def invite_code_is_available(code):
    """这个邀请码是否存在且未使用（全站猜码上限触发时，用来放行真实有效的邀请码）。"""
    from database import SessionLocal

    db = SessionLocal()
    try:
        code = normalize_invite_code(db, code)
        if not code:
            return False
        row = db.query(InvitationCode.is_used).filter(InvitationCode.code == code).first()
        return row is not None and int(row[0]) == 0
    finally:
        db.close()

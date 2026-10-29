"""
空数据库的第一个管理员账号（主要给测试环境用）。

在启动命令里运行：python -m poker.scripts.bootstrap_admin
- 没有设置 BOOTSTRAP_ADMIN_USERNAME / BOOTSTRAP_ADMIN_PASSWORD 时什么都不做；
- 数据库里已经有任何管理员时什么都不做（所以线上即使误设了也不会生效）；
- 否则创建管理员组（组代码 0）和这个管理员账号。
"""

import os
import re
import sys

from database import SessionLocal
from core.security import pwd_context
from core.validators import check_password
from core.models import UserModule
from poker.models import Group, User, UserGroupRole


ADMIN_GROUP_CODE = "0"
USERNAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{4,}$")


def bootstrap_admin(username, password):
    """返回 'created' | 'skipped_exists' | 'invalid_username' | 'invalid_password' | 'username_taken'。"""
    if not USERNAME_PATTERN.match(username or ""):
        return "invalid_username"
    if check_password(password):
        return "invalid_password"

    db = SessionLocal()
    try:
        if db.query(UserGroupRole.id).filter(UserGroupRole.role == "admin").first():
            return "skipped_exists"

        if db.query(User.id).filter(User.username == username).first():
            return "username_taken"

        group = db.query(Group).filter(Group.group_code == ADMIN_GROUP_CODE).first()
        if group is None:
            group = Group(group_code=ADMIN_GROUP_CODE, group_name="管理员")
            db.add(group)
            db.flush()

        user = User(
            username=username,
            password_hash=pwd_context.hash(password),
            nickname=username,
            is_active=1,
            email_verified=1,  # 管理员账号跳过邮箱验证
        )
        db.add(user)
        db.flush()

        db.add(UserGroupRole(user_id=user.id, group_id=group.id, role="admin"))
        db.add(UserModule(user_id=user.id, module="poker"))
        db.commit()
        return "created"
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main():
    username = os.getenv("BOOTSTRAP_ADMIN_USERNAME", "").strip()
    password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")

    if not username or not password:
        print("bootstrap_admin: not configured, skipped")
        return 0

    result = bootstrap_admin(username, password)
    print(f"bootstrap_admin: {result}")
    # 配置写错时让启动失败，部署日志里能直接看到原因
    return 1 if result.startswith("invalid") or result == "username_taken" else 0


if __name__ == "__main__":
    sys.exit(main())

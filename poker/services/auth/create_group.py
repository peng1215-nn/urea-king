"""用户自助创建组（测试功能）。每个用户最多作为局头创建 1 个组。"""

import secrets
import string

from core.errors import safe_error
from core.time import now_columbus_naive
from core.validators import check_name
from database import SessionLocal
from poker.models import Group, User, UserGroupRole
from poker.services.admin.audit_log import write_audit_log

GROUP_NAME_MAX = 50


def _gen_group_code(db) -> str:
    """生成唯一 group_code（8 位大写字母+数字）。"""
    chars = string.ascii_uppercase + string.digits
    for _ in range(20):
        code = "".join(secrets.choice(chars) for _ in range(8))
        if not db.query(Group).filter(Group.group_code == code).first():
            return code
    raise RuntimeError("无法生成唯一 group_code")


def create_group_service(request, user_id: int, group_name: str):
    group_name = group_name.strip()

    if not group_name:
        return {"success": False, "error_code": "createGroupNameRequired"}

    group_name, name_error = check_name(group_name, GROUP_NAME_MAX)
    if name_error:
        return {
            "success": False,
            "error_code": (
                "createGroupNameTooLong"
                if name_error == "too_long"
                else "createGroupNameInvalid"
            ),
        }

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.email_verified:
            return {"success": False, "error_code": "createGroupNotVerified"}

        # 检查该用户是否已经作为局头创建过组
        existing = (
            db.query(Group)
            .filter(Group.created_by_user_id == user_id)
            .first()
        )
        if existing:
            return {"success": False, "error_code": "createGroupAlreadyOwner"}

        group_code = _gen_group_code(db)

        new_group = Group(
            group_code=group_code,
            group_name=group_name,
            invite_code_limit=17,
            created_by_user_id=user_id,
            created_at=now_columbus_naive(),
        )
        db.add(new_group)
        db.flush()

        # 创建者自动成为该组的 organizer
        role = UserGroupRole(
            user_id=user_id,
            group_id=new_group.id,
            role="organizer",
        )
        db.add(role)
        db.commit()

        write_audit_log(
            request=request,
            action="CREATE_GROUP",
            target_type="group",
            target_id=new_group.id,
            old_value=None,
            new_value=f"group_code={group_code}, group_name={group_name}",
            operator_id=user_id,
            operator_username=user.username,
        )

        return {
            "success": True,
            "group_code": group_code,
            "group_name": group_name,
            "group_id": new_group.id,
        }

    except Exception as e:
        safe_error(e)
        db.rollback()
        return {"success": False, "error_code": "createGroupFailed"}

    finally:
        db.close()

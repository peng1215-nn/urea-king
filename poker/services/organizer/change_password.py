"""
局头资料页上的组名：查看与修改。
（昵称、密码在 poker/services/common/account.py，各身份共用。）
"""

from database import SessionLocal
from poker.core.errors import safe_error
from poker.core.validators import GROUP_NAME_MAX, check_name
from poker.models import Group


def get_group_info_service(group_id: int):
    db = SessionLocal()
    try:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            return {"success": False, "message": "groupNotFound"}
        return {"success": True, "group_name": group.group_name or ""}
    finally:
        db.close()


def update_group_name_service(group_id: int, group_name: str):
    # 与管理员修改组名使用同一套校验
    group_name, name_error = check_name(group_name, GROUP_NAME_MAX)
    if name_error == "too_long":
        return {"success": False, "message": "groupNameTooLong"}
    if name_error:
        return {"success": False, "message": "groupNameInvalid"}
    if not group_name:
        return {"success": False, "message": "groupNameRequired"}

    db = SessionLocal()
    try:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            return {"success": False, "message": "groupNotFound"}
        group.group_name = group_name
        db.commit()
        return {"success": True, "message": "groupNameUpdateSuccess"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}
    finally:
        db.close()

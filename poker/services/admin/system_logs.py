from math import ceil
from database import SessionLocal
from poker.models import PokerAuditLog
from core.models import PlatformUser
from sqlalchemy import or_


def get_audit_logs_service(action=None, username=None, page=1, page_size=20):
    db = SessionLocal()
    try:
        page = max(int(page), 1)
        page_size = int(page_size)
        if page_size not in [5, 10, 20]:
            page_size = 5

        query = (
            db.query(PokerAuditLog, PlatformUser)
            .outerjoin(PlatformUser, PokerAuditLog.operator_id == PlatformUser.id)
        )
        if action:
            query = query.filter(PokerAuditLog.action == action)
        if username:
            keyword = f"%{username}%"
            query = query.filter(
                or_(
                    PokerAuditLog.operator_username.ilike(keyword),
                    PlatformUser.nickname.ilike(keyword),
                )
            )

        total = query.count()
        logs = query.order_by(PokerAuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        total_pages = ceil(total / page_size) if total > 0 else 1

        return {
            "success": True,
            "logs": [
                {
                    "id": log.id,
                    "operator_id": log.operator_id,
                    "operator_username": log.operator_username,
                    "operator_nickname": user.nickname if user and user.nickname else "",
                    "action": log.action,
                    "target_type": log.target_type,
                    "target_id": log.target_id,
                    "old_value": log.old_value,
                    "new_value": log.new_value,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
                }
                for log, user in logs
            ],
            "pagination": {"page": page, "page_size": page_size, "total": total, "total_pages": total_pages},
        }
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        db.close()

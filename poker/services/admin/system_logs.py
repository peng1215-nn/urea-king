import csv
import io
from math import ceil
from database import SessionLocal
from poker.models import AuditLog
from poker.models import User
from sqlalchemy import or_
from utils.time import now_columbus_naive
from poker.core.errors import safe_error


def _build_filtered_query(db, action=None, username=None):
    query = db.query(
        AuditLog,
        User,
    ).outerjoin(
        User,
        AuditLog.operator_id == User.id,
    )

    if action:
        query = query.filter(
            AuditLog.action == action
        )

    if username:
        keyword = f"%{username}%"
        query = query.filter(
            or_(
                AuditLog.operator_username.ilike(keyword),
                User.nickname.ilike(keyword),
            )
        )

    return query


def get_audit_logs_service(
    action=None,
    username=None,
    page=1,
    page_size=20,
):
    db = SessionLocal()

    try:
        page = max(int(page), 1)
        page_size = int(page_size)

        if page_size not in [
            5,
            10,
            20,
        ]:
            page_size = 5

        query = _build_filtered_query(db, action, username)

        total = query.count()

        logs = query.order_by(
            AuditLog.created_at.desc()
        ).offset(
            (page - 1) * page_size
        ).limit(
            page_size
        ).all()

        total_pages = ceil(total / page_size) if total > 0 else 1

        return {
            "success": True,
            "logs": [
                {
                    "id": log.id,
                    "operator_id": log.operator_id,
                    "operator_username": log.operator_username,
                    "operator_nickname": (
                        user.nickname
                        if user and user.nickname
                        else ""
                    ),
                    "action": log.action,
                    "target_type": log.target_type,
                    "target_id": log.target_id,
                    "old_value": log.old_value,
                    "new_value": log.new_value,
                    "ip_address": log.ip_address,
                    "created_at": (
                        log.created_at.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        if log.created_at
                        else ""
                    ),
                }
                for log, user in logs
            ],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
            },
        }

    except Exception as e:
        return {
            "success": False,
            "message": safe_error(e),
        }

    finally:
        db.close()


CSV_HEADERS = [
    "id",
    "operator_username",
    "operator_nickname",
    "action",
    "target_type",
    "target_id",
    "old_value",
    "new_value",
    "created_at",
    "ip_address",
]


def _csv_safe(value):
    """防止 Excel 把以 = + - @ 开头的内容当公式执行。"""
    if value is None:
        return ""
    text = str(value)
    if text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + text
    return text


def export_audit_logs_csv_service(action=None, username=None):
    """按当前筛选条件导出全部匹配日志，返回带 BOM 的 CSV 文本。"""
    db = SessionLocal()

    try:
        rows = _build_filtered_query(
            db, action, username
        ).order_by(
            AuditLog.created_at.desc()
        ).all()

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(CSV_HEADERS)

        for log, user in rows:
            writer.writerow([
                log.id,
                _csv_safe(log.operator_username),
                _csv_safe(user.nickname if user and user.nickname else ""),
                _csv_safe(log.action),
                _csv_safe(log.target_type),
                log.target_id if log.target_id is not None else "",
                _csv_safe(log.old_value),
                _csv_safe(log.new_value),
                log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
                _csv_safe(log.ip_address),
            ])

        return "\ufeff" + buffer.getvalue()

    finally:
        db.close()


def export_filename():
    return "system_logs_" + now_columbus_naive().strftime("%Y%m%d_%H%M%S") + ".csv"


MAX_BULK_DELETE = 500


def delete_audit_logs_service(ids):
    """按 id 批量删除系统日志，返回实际删除条数。"""
    clean_ids = sorted({int(i) for i in (ids or [])})

    if not clean_ids:
        return {"success": False, "message": "noLogsSelected"}

    if len(clean_ids) > MAX_BULK_DELETE:
        return {"success": False, "message": "tooManyLogsSelected"}

    db = SessionLocal()

    try:
        deleted = db.query(AuditLog).filter(
            AuditLog.id.in_(clean_ids)
        ).delete(synchronize_session=False)

        db.commit()

        return {"success": True, "deleted": deleted}

    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}

    finally:
        db.close()

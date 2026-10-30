from core.time import now_columbus_naive

from database import SessionLocal
from poker.models import AuditLog
import logging


def get_client_ip(request):
    forwarded_for = request.headers.get(
        "x-forwarded-for"
    )

    if forwarded_for:
        return forwarded_for.split(",")[-1].strip()

    if request.client:
        return request.client.host

    return None


def write_audit_log(
    request,
    action,
    target_type,
    target_id=None,
    old_value=None,
    new_value=None,
    operator_id=None,
    operator_username=None,
    db=None,
):
    """
    写一条审计日志。调用方已经开着数据库会话时传 db=，复用同一个连接：
    否则同一个请求会同时占用两个连接，并发高时连接池被占满、互相等待。
    """
    own_session = db is None
    if own_session:
        db = SessionLocal()

    try:
        log = AuditLog(
            operator_id=operator_id,
            operator_username=operator_username,
            action=action,
            target_type=target_type,
            target_id=target_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=get_client_ip(request),
            created_at=now_columbus_naive(),
        )

        db.add(log)
        db.commit()

    except Exception as error:
        db.rollback()
        logging.getLogger("poker.audit").error("failed to write audit log", exc_info=error)

    finally:
        if own_session:
            db.close()
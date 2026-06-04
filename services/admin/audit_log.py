from datetime import datetime
from utils.time import now_columbus_naive

from database import SessionLocal
from models import AuditLog


def get_client_ip(request):
    forwarded_for = request.headers.get(
        "x-forwarded-for"
    )

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

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
):
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
        print("AUDIT LOG ERROR:", error)

    finally:
        db.close()
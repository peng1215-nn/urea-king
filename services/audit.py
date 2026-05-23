import json

from database import SessionLocal
from models import AuditLog


def create_audit_log(
    request,
    action,
    target_type,
    target_id=None,
    old_value=None,
    new_value=None,
):
    db = SessionLocal()

    try:

        operator_id = request.session.get(
            "user_id"
        )

        operator_username = request.session.get(
            "username"
        )

        ip_address = None

        if request.client:
            ip_address = request.client.host

        log = AuditLog(
            operator_id=operator_id,
            operator_username=operator_username,
            action=action,
            target_type=target_type,
            target_id=target_id,

            old_value=json.dumps(
                old_value,
                ensure_ascii=False,
            ) if old_value else None,

            new_value=json.dumps(
                new_value,
                ensure_ascii=False,
            ) if new_value else None,

            ip_address=ip_address,
        )

        db.add(log)

        db.commit()

    finally:
        db.close()
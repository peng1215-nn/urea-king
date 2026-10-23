"""
健康检查：
- /healthz：进程存活即返回 200（给平台判断是否需要重启）
- /readyz：额外检查数据库连接，不可用时返回 503
"""

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from database import SessionLocal


router = APIRouter()

logger = logging.getLogger("poker.health")


@router.api_route("/healthz", methods=["GET", "HEAD"], include_in_schema=False)
def healthz():
    return {"status": "ok"}


@router.api_route("/readyz", methods=["GET", "HEAD"], include_in_schema=False)
def readyz():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except Exception:
        logger.exception("readiness check failed")
        return JSONResponse(
            {"status": "error", "database": "unavailable"},
            status_code=503,
        )
    finally:
        db.close()

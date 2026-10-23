from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse

from poker.services.auth.group_join import group_join_service
from poker.template_config import templates
from fastapi.responses import JSONResponse
from poker.core.rate_limit import group_join_failures_by_ip
from poker.services.admin.audit_log import get_client_ip


router = APIRouter()


@router.get(
    "/group-join",
    response_class=HTMLResponse,
)
def group_join_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth/group_join.html",
    )


@router.post("/group-join")
def group_join(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    invite_code: str = Form(...),
):
    ip = get_client_ip(request) or "unknown"
    wait = group_join_failures_by_ip.retry_after(ip)

    if wait:
        return JSONResponse(
            {
                "success": False,
                "message": "groupJoinTooManyAttempts",
                "retry_after": wait,
            },
            status_code=429,
        )

    result = group_join_service(
        request=request,
        username=username,
        password=password,
        invite_code=invite_code,
    )

    if not result.get("success"):
        group_join_failures_by_ip.hit(ip)

    return result
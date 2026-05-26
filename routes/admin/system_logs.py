from fastapi import APIRouter
from fastapi import Query
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from services.admin.system_logs import get_audit_logs_service
from template_config import templates
from services.common.common import add_no_cache_headers


router = APIRouter()


def require_admin(request: Request):
    return request.session.get("current_role") == "admin"


@router.get(
    "/system-logs",
    response_class=HTMLResponse,
)
def system_logs_page(request: Request):
    if not require_admin(request):
        return RedirectResponse(
            url="/login",
            status_code=302,
        )

    response = templates.TemplateResponse(
        request=request,
        name="admin/system_logs.html",
        context={
            "current_page": "system_logs",
        },
    )

    return add_no_cache_headers(response)


@router.get("/admin/audit-logs")
def get_audit_logs(
    request: Request,
    action: str = Query(default=""),
    username: str = Query(default=""),
    page: int = Query(default=1),
    page_size: int = Query(default=5),
):
    if not require_admin(request):
        return {
            "success": False,
            "message": "permissionDenied",
        }

    return get_audit_logs_service(
        action=action.strip(),
        username=username.strip(),
        page=page,
        page_size=page_size,
    )
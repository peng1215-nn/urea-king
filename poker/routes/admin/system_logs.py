from fastapi import APIRouter
from fastapi import Response
from pydantic import BaseModel
from fastapi import Query
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from poker.services.admin.system_logs import delete_audit_logs_service
from poker.services.admin.system_logs import export_audit_logs_csv_service
from poker.services.admin.system_logs import export_filename
from poker.services.admin.system_logs import get_audit_logs_service
from poker.services.admin.audit_log import write_audit_log
from poker.template_config import templates
from poker.services.common.common import add_no_cache_headers


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


@router.get("/admin/audit-logs/export")
def export_audit_logs(
    request: Request,
    action: str = Query(default=""),
    username: str = Query(default=""),
):
    if not require_admin(request):
        return Response(status_code=403)

    content = export_audit_logs_csv_service(
        action=action.strip(),
        username=username.strip(),
    )

    return Response(
        content=content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{export_filename()}"',
            "Cache-Control": "no-store",
        },
    )


class DeleteAuditLogsPayload(BaseModel):
    ids: list[int]


@router.post("/admin/audit-logs/delete")
def delete_audit_logs(
    request: Request,
    payload: DeleteAuditLogsPayload,
):
    if not require_admin(request):
        return {
            "success": False,
            "message": "permissionDenied",
        }

    result = delete_audit_logs_service(payload.ids)

    if result.get("success"):
        # 删除操作本身留痕，避免无声清除记录
        write_audit_log(
            request=request,
            action="DELETE_AUDIT_LOGS",
            target_type="audit_log",
            old_value=f"{result['deleted']} records",
            operator_id=request.session.get("user_id"),
            operator_username=request.session.get("username"),
        )

    return result

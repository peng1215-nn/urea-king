from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.services.admin.audit_log import write_audit_log
from core.services.admin.invite_management import (
    create_group_service,
    create_invitation_code_service,
    delete_group_service,
    delete_invitation_code_service,
    force_delete_group_service,
    get_deletable_group_options_service,
    get_group_options_service,
    get_unused_invitation_options_service,
)
from poker.services.common.common import add_no_cache_headers
from template_config import templates

router = APIRouter()


def require_admin(request: Request):
    return request.session.get("is_platform_admin") is True


@router.get("/invite-management", response_class=HTMLResponse)
def invite_management_page(request: Request):
    if not require_admin(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    response = templates.TemplateResponse(
        request=request,
        name="admin/invite_management.html",
        context={"current_page": "invite_management"},
    )
    return add_no_cache_headers(response)


@router.get("/admin/groups/options")
def get_group_options(request: Request):
    if not require_admin(request):
        return {"success": False, "message": "permissionDenied"}
    return get_group_options_service()


@router.get("/admin/groups/deletable-options")
def get_deletable_group_options(request: Request):
    if not require_admin(request):
        return {"success": False, "message": "permissionDenied"}
    return get_deletable_group_options_service()


@router.get("/admin/invitation-codes/options")
def get_unused_invitation_options(request: Request):
    if not require_admin(request):
        return {"success": False, "message": "permissionDenied"}
    return get_unused_invitation_options_service()


@router.post("/admin/groups/create")
def create_group(request: Request, group_code: str = Form(...), group_name: str = Form(...)):
    if not require_admin(request):
        return {"success": False, "message": "permissionDenied"}
    result = create_group_service(group_code=group_code, group_name=group_name)
    if result.get("success"):
        write_audit_log(
            request=request, action="CREATE_GROUP", target_type="group",
            target_id=result.get("group_id"), old_value=None,
            new_value=f"group_code={result.get('group_code')}, group_name={result.get('group_name')}",
            operator_id=request.session.get("user_id"), operator_username=request.session.get("username"),
        )
    return result


@router.post("/admin/groups/delete")
def delete_group(request: Request, group_id: int = Form(...)):
    if not require_admin(request):
        return {"success": False, "message": "permissionDenied"}
    result = delete_group_service(group_id=group_id)
    if result.get("success"):
        write_audit_log(
            request=request, action="DELETE_GROUP", target_type="group",
            target_id=group_id,
            old_value=f"group_code={result.get('group_code')}, group_name={result.get('group_name')}",
            new_value=None,
            operator_id=request.session.get("user_id"), operator_username=request.session.get("username"),
        )
    return result


@router.post("/admin/groups/force-delete")
def force_delete_group(request: Request, group_id: int = Form(...), group_code: str = Form(...)):
    if not require_admin(request):
        return {"success": False, "message": "permissionDenied"}
    result = force_delete_group_service(group_id, group_code.strip())
    if result.get("success"):
        write_audit_log(
            request=request, action="FORCE_DELETE_GROUP", target_type="group",
            target_id=group_id,
            old_value=f"group_code={result['group_code']}, group_name={result['group_name']}, counts={result['counts']}",
            new_value=None,
            operator_id=request.session.get("user_id"), operator_username=request.session.get("username"),
        )
    return result


@router.post("/admin/invitation-codes/create")
def create_invitation_code(
    request: Request,
    group_id: int = Form(...),
    role: str = Form(...),
):
    """Auto-generate an invite code for the given group."""
    if not require_admin(request):
        return {"success": False, "message": "permissionDenied"}
    result = create_invitation_code_service(group_id=group_id, role=role)
    if result.get("success"):
        code_info = result.get("code", {})
        write_audit_log(
            request=request, action="CREATE_INVITATION_CODE", target_type="invitation_code",
            target_id=code_info.get("id"), old_value=None,
            new_value=f"code={code_info.get('code')}, group_id={group_id}, role={role}",
            operator_id=request.session.get("user_id"), operator_username=request.session.get("username"),
        )
    return result


@router.post("/admin/invitation-codes/delete")
def delete_invitation_code(request: Request, invitation_id: int = Form(...)):
    if not require_admin(request):
        return {"success": False, "message": "permissionDenied"}
    result = delete_invitation_code_service(invitation_id=invitation_id)
    if result.get("success"):
        write_audit_log(
            request=request, action="DELETE_INVITATION_CODE", target_type="invitation_code",
            target_id=invitation_id,
            old_value=f"code={result.get('code')}, role={result.get('role')}",
            new_value=None,
            operator_id=request.session.get("user_id"), operator_username=request.session.get("username"),
        )
    return result

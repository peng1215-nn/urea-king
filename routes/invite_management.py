from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse

from services.audit_log import write_audit_log
from services.invite_management import create_group_service
from services.invite_management import create_invitation_code_service
from services.invite_management import delete_group_service
from services.invite_management import delete_invitation_code_service
from services.invite_management import get_deletable_group_options_service
from services.invite_management import get_group_options_service
from services.invite_management import get_unused_invitation_options_service
from template_config import templates


router = APIRouter()


def require_admin(request: Request):
    return request.session.get("current_role") == "admin"


@router.get(
    "/invite-management",
    response_class=HTMLResponse,
)
def invite_management_page(request: Request):
    if not require_admin(request):
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
        )

    return templates.TemplateResponse(
        request=request,
        name="admin/invite_management.html",
        context={
            "current_page": "invite_management",
        },
    )


@router.get("/admin/groups/options")
def get_group_options(request: Request):
    if not require_admin(request):
        return {
            "success": False,
            "message": "permissionDenied",
        }

    return get_group_options_service()


@router.get("/admin/groups/deletable-options")
def get_deletable_group_options(request: Request):
    if not require_admin(request):
        return {
            "success": False,
            "message": "permissionDenied",
        }

    return get_deletable_group_options_service()


@router.get("/admin/invitation-codes/options")
def get_unused_invitation_options(request: Request):
    if not require_admin(request):
        return {
            "success": False,
            "message": "permissionDenied",
        }

    return get_unused_invitation_options_service()


@router.post("/admin/groups/create")
def create_group(
    request: Request,
    group_code: str = Form(...),
    group_name: str = Form(...),
):
    if not require_admin(request):
        return {
            "success": False,
            "message": "permissionDenied",
        }

    result = create_group_service(
        group_code=group_code,
        group_name=group_name,
    )

    if result.get("success"):
        write_audit_log(
            request=request,
            action="CREATE_GROUP",
            target_type="group",
            target_id=result.get("group_id"),
            old_value=None,
            new_value=(
                f"group_code={result.get('group_code')}, "
                f"group_name={result.get('group_name')}"
            ),
            operator_id=request.session.get("user_id"),
            operator_username=request.session.get("username"),
        )

    return result


@router.post("/admin/groups/delete")
def delete_group(
    request: Request,
    group_id: int = Form(...),
):
    if not require_admin(request):
        return {
            "success": False,
            "message": "permissionDenied",
        }

    result = delete_group_service(
        group_id=group_id,
    )

    if result.get("success"):
        write_audit_log(
            request=request,
            action="DELETE_GROUP",
            target_type="group",
            target_id=group_id,
            old_value=(
                f"group_code={result.get('group_code')}, "
                f"group_name={result.get('group_name')}"
            ),
            new_value=None,
            operator_id=request.session.get("user_id"),
            operator_username=request.session.get("username"),
        )

    return result


@router.post("/admin/invitation-codes/create")
def create_invitation_code(
    request: Request,
    code: str = Form(...),
    group_id: int = Form(...),
    role: str = Form(...),
):
    if not require_admin(request):
        return {
            "success": False,
            "message": "permissionDenied",
        }

    result = create_invitation_code_service(
        code=code,
        group_id=group_id,
        role=role,
    )

    if result.get("success"):
        write_audit_log(
            request=request,
            action="CREATE_INVITATION_CODE",
            target_type="invitation_code",
            target_id=result.get("invite_id"),
            old_value=None,
            new_value=(
                f"code={result.get('code')}, "
                f"group_code={result.get('group_code')}, "
                f"role={result.get('role')}"
            ),
            operator_id=request.session.get("user_id"),
            operator_username=request.session.get("username"),
        )

    return result


@router.post("/admin/invitation-codes/delete")
def delete_invitation_code(
    request: Request,
    invitation_id: int = Form(...),
):
    if not require_admin(request):
        return {
            "success": False,
            "message": "permissionDenied",
        }

    result = delete_invitation_code_service(
        invitation_id=invitation_id,
    )

    if result.get("success"):
        write_audit_log(
            request=request,
            action="DELETE_INVITATION_CODE",
            target_type="invitation_code",
            target_id=invitation_id,
            old_value=(
                f"code={result.get('code')}, "
                f"group_code={result.get('group_code')}, "
                f"role={result.get('role')}"
            ),
            new_value=None,
            operator_id=request.session.get("user_id"),
            operator_username=request.session.get("username"),
        )

    return result
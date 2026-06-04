from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from services.admin.audit_log import write_audit_log
from services.common.common import add_no_cache_headers
from services.organizer.member_management import get_organizer_members_service
from services.organizer.member_management import remove_member_service
from template_config import templates


router = APIRouter()


def require_organizer(request: Request):
    return request.session.get("current_role") == "organizer"


def get_current_group_id(request: Request):
    return request.session.get("current_group_id")


@router.get(
    "/organizer-dashboard",
    response_class=HTMLResponse,
)
def organizer_dashboard(request: Request):
    if not require_organizer(request):
        return RedirectResponse(
            url="/login",
            status_code=302,
        )

    response = templates.TemplateResponse(
        request=request,
        name="organizer/dashboard.html",
        context={
            "current_page": "dashboard",
        },
    )

    return add_no_cache_headers(response)


@router.get(
    "/organizer-members",
    response_class=HTMLResponse,
)
def organizer_members_page(request: Request):
    if not require_organizer(request):
        return RedirectResponse(
            url="/login",
            status_code=302,
        )

    response = templates.TemplateResponse(
        request=request,
        name="organizer/member_management.html",
        context={
            "current_page": "member_management",
        },
    )

    return add_no_cache_headers(response)


@router.get("/organizer/members")
def organizer_members_api(request: Request):
    if not require_organizer(request):
        return {
            "success": False,
            "message": "无权限访问。",
        }

    group_id = get_current_group_id(request)

    if not group_id:
        return {
            "success": False,
            "message": "未选择组别，请重新登录。",
        }

    return get_organizer_members_service(group_id=int(group_id))


@router.post("/organizer/remove-member")
def remove_member(
    request: Request,
    target_user_id: int = Form(...),
):
    if not require_organizer(request):
        return {
            "success": False,
            "message": "无权限访问。",
        }

    group_id = get_current_group_id(request)

    if not group_id:
        return {
            "success": False,
            "message": "未选择组别，请重新登录。",
        }

    result = remove_member_service(
        group_id=int(group_id),
        target_user_id=target_user_id,
    )

    if result.get("success"):
        write_audit_log(
            request=request,
            action="REMOVE_GROUP_MEMBER",
            target_type="user_group_role",
            target_id=target_user_id,
            old_value=f"group_id={group_id}",
            new_value="removed",
            operator_id=request.session.get("user_id"),
            operator_username=request.session.get("username"),
        )

    return result


@router.get("/organizer/logout-to-join")
def logout_to_join(request: Request):
    request.session.clear()

    response = RedirectResponse(
        url="/group-join",
        status_code=302,
    )

    return response
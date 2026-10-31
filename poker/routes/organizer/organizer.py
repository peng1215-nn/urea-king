from core.middleware import clear_session_cache
from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from poker.services.admin.audit_log import write_audit_log
from poker.services.common.common import add_no_cache_headers
from poker.services.organizer.member_management import get_organizer_members_service
from poker.services.organizer.member_management import remove_member_service
from poker.services.organizer.member_management import save_member_alias_service
from poker.services.organizer.member_management import promote_member_service
from poker.services.organizer.member_management import step_down_organizer_service
from poker.template_config import templates


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
            "message": "permissionDenied",
        }

    group_id = get_current_group_id(request)

    if not group_id:
        return {
            "success": False,
            "message": "noGroupSelected",
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
            "message": "permissionDenied",
        }

    group_id = get_current_group_id(request)

    if not group_id:
        return {
            "success": False,
            "message": "noGroupSelected",
        }

    result = remove_member_service(
        group_id=int(group_id),
        target_user_id=target_user_id,
    )

    if result.get("success"):
        # 被操作的人（或整组成员）的旧登录状态立即失效，不等 15 秒缓存过期
        clear_session_cache()
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


@router.post("/organizer/promote-member")
def promote_member(request: Request, target_user_id: int = Form(...)):
    """把组内普通成员设为局头（每组最多 2 个局头）。"""
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_current_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}

    result = promote_member_service(group_id=int(group_id), target_user_id=target_user_id)
    if result.get("success"):
        # 被提拔的人当前的登录（还是普通成员身份）立即失效，重新登录后以局头身份进入
        clear_session_cache()
        write_audit_log(
            request=request,
            action="PROMOTE_ORGANIZER",
            target_type="user_group_role",
            target_id=target_user_id,
            old_value=f"group_id={group_id}, role=user",
            new_value="role=organizer",
            operator_id=request.session.get("user_id"),
            operator_username=request.session.get("username"),
        )
    return result


@router.post("/organizer/step-down")
def step_down(request: Request):
    """局头自己卸任，变回普通成员；卸任后需要重新登录。"""
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_current_group_id(request)
    user_id = request.session.get("user_id")
    if not group_id or not user_id:
        return {"success": False, "message": "noGroupSelected"}

    result = step_down_organizer_service(group_id=int(group_id), user_id=int(user_id))
    if result.get("success"):
        write_audit_log(
            request=request,
            action="STEP_DOWN_ORGANIZER",
            target_type="user_group_role",
            target_id=int(user_id),
            old_value=f"group_id={group_id}, role=organizer",
            new_value="role=user",
            operator_id=int(user_id),
            operator_username=request.session.get("username"),
        )
        request.session.clear()
        clear_session_cache()
    return result


@router.post("/organizer/save-member-alias")
def save_member_alias(
    request: Request,
    target_user_id: int = Form(...),
    alias: str = Form(""),
):
    if not require_organizer(request):
        return {"success": False, "message": "permissionDenied"}

    group_id = get_current_group_id(request)
    if not group_id:
        return {"success": False, "message": "noGroupSelected"}

    return save_member_alias_service(
        group_id=int(group_id),
        target_user_id=target_user_id,
        alias=alias,
    )


@router.get("/organizer/logout-to-join")
def logout_to_join(request: Request):
    request.session.clear()

    response = RedirectResponse(
        url="/group-join",
        status_code=302,
    )

    return response
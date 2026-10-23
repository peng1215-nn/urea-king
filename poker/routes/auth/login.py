from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from database import SessionLocal
from poker.models import Group
from poker.models import UserGroupRole
from poker.services.auth.login import login_user_service
from poker.template_config import templates
from fastapi.responses import JSONResponse
from poker.core.rate_limit import login_failures_by_account, login_failures_by_ip, login_failures_by_username, login_keys, username_key
from poker.services.admin.audit_log import get_client_ip


router = APIRouter()


def render_login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
    )


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render_login_page(request)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return render_login_page(request)


@router.post("/login")
def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    ip = get_client_ip(request) or "unknown"
    account_key, ip_key = login_keys(ip, username)
    name_key = username_key(username)

    wait = max(
        login_failures_by_account.retry_after(account_key),
        login_failures_by_ip.retry_after(ip_key),
        login_failures_by_username.retry_after(name_key),
    )

    if wait:
        return JSONResponse(
            {
                "success": False,
                "error_code": "loginTooManyAttempts",
                "retry_after": wait,
            },
            status_code=429,
        )

    result = login_user_service(
        request=request,
        username=username,
        password=password,
    )

    if result.get("success"):
        login_failures_by_account.reset(account_key)
        login_failures_by_username.reset(name_key)
    elif result.get("error_code") in ("loginUserNotFound", "loginPasswordIncorrect"):
        login_failures_by_account.hit(account_key)
        login_failures_by_ip.hit(ip_key)
        login_failures_by_username.hit(name_key)

    return result


@router.get("/group-select", response_class=HTMLResponse)
def group_select_page(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse(
            url="/login",
            status_code=302,
        )

    return templates.TemplateResponse(
        request=request,
        name="auth/group_select.html",
    )


@router.post("/select-group")
def select_group(
    request: Request,
    group_id: int = Form(...),
):
    db = SessionLocal()

    try:
        user_id = request.session.get("user_id")

        if not user_id:
            return {
                "success": False,
                "error_code": "loginRequired",
            }

        user_group_role = db.query(UserGroupRole).filter(
            UserGroupRole.user_id == user_id,
            UserGroupRole.group_id == group_id,
        ).first()

        if not user_group_role:
            return {
                "success": False,
                "error_code": "groupAccessDenied",
            }

        group = db.query(Group).filter(
            Group.id == group_id,
        ).first()

        if not group:
            return {
                "success": False,
                "error_code": "groupNotFound",
            }

        request.session["current_group_id"] = group.id
        request.session["current_group_code"] = group.group_code
        request.session["current_role"] = user_group_role.role

        redirect_url = "/user-dashboard"

        if user_group_role.role == "admin":
            redirect_url = "/admin-dashboard"

        elif user_group_role.role == "organizer":
            redirect_url = "/organizer-dashboard"

        return {
            "success": True,
            "role": user_group_role.role,
            "redirect_url": redirect_url,
        }

    finally:
        db.close()
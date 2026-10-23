from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from poker.services.auth.login import login_user_service
from poker.services.auth.login import select_group_service
from poker.template_config import templates
from fastapi.responses import JSONResponse
from poker.core.rate_limit import login_retry_after, record_login_failure, record_login_success
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
    wait = login_retry_after(ip, username)

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
        record_login_success(ip, username)
    elif result.get("error_code") == "loginInvalidCredentials":
        record_login_failure(ip, username)

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
    user_id = request.session.get("user_id")

    if not user_id:
        return {"success": False, "error_code": "loginRequired"}

    result = select_group_service(user_id=user_id, group_id=group_id)

    if result.get("success"):
        request.session["current_group_id"] = result.pop("group_id")
        request.session["current_group_code"] = result.pop("group_code")
        request.session["current_role"] = result["role"]

    return result

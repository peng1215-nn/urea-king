from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from poker.services.auth.login import login_user_service
from poker.services.auth.login import select_group_service, get_user_groups_service
from poker.template_config import templates
from fastapi.responses import JSONResponse
from poker.core.rate_limit import record_login_success, reserve_login_attempt
from poker.services.admin.audit_log import get_client_ip
from poker.services.admin.admin import record_login_page_view_service, record_login_success_service


router = APIRouter()


def render_login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
    )


# HEAD：在线监控、搜索引擎常用它检查页面是否存在
@router.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def home(request: Request):
    return render_login_page(request)


@router.get("/privacy", response_class=HTMLResponse)
def privacy_page(request: Request):
    """隐私说明（中英文），不需要登录。"""
    return templates.TemplateResponse(request=request, name="auth/privacy.html")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    record_login_page_view_service()
    return render_login_page(request)


@router.post("/login")
def login_user(
    request: Request,
    username: str = Form(..., max_length=50),
    password: str = Form(..., max_length=256),
):
    ip = get_client_ip(request) or "unknown"

    # 先按失败占用一次名额，再校验密码；并发的请求不能同时通过检查
    attempt = reserve_login_attempt(ip, username)
    if attempt.wait:
        return JSONResponse(
            {
                "success": False,
                "error_code": "loginTooManyAttempts",
                "retry_after": attempt.wait,
            },
            status_code=429,
        )

    result = login_user_service(
        request=request,
        username=username,
        password=password,
    )

    # 只有账号密码错误才算失败，其余情况退回名额
    if result.get("error_code") != "loginInvalidCredentials":
        attempt.release()

    if result.get("success"):
        record_login_success(ip, username)
        record_login_success_service()

    return result


@router.get("/group-select", response_class=HTMLResponse)
def group_select_page(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(
            url="/login",
            status_code=302,
        )

    groups = get_user_groups_service(user_id=user_id)

    import json
    return templates.TemplateResponse(
        request=request,
        name="auth/group_select.html",
        context={"server_groups": json.dumps(groups)},
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

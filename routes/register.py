from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from services.register import register_user_service
from template_config import templates


router = APIRouter()


def render_register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth/register.html",
    )


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return render_register_page(request)


@router.post("/register")
def register_user(
    request: Request,
    username: str = Form(...),
    nickname: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    invite_code: str = Form(...),
):
    return register_user_service(
        request=request,
        username=username,
        nickname=nickname,
        password=password,
        confirm_password=confirm_password,
        invite_code=invite_code,
    )
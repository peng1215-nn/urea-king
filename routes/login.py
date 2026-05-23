from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from template_config import templates

from services.login import login_user_service


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
    return login_user_service(
        request=request,
        username=username,
        password=password,
    )
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from poker.services.auth.reset_password import forgot_password_service, reset_password_service
from poker.template_config import templates

router = APIRouter()


@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth/forgot_password.html")


@router.post("/forgot-password")
def forgot_password(request: Request, email: str = Form(...)):
    result = forgot_password_service(email=email)
    return result


@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(request: Request, token: str = ""):
    return templates.TemplateResponse(
        request=request,
        name="auth/reset_password.html",
        context={"token": token},
    )


@router.post("/reset-password")
def reset_password(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    result = reset_password_service(
        token=token,
        new_password=new_password,
        confirm_password=confirm_password,
    )
    return result

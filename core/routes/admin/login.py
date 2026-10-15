"""Platform admin web login routes — /admin/login"""
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.services.admin.login import admin_login_service, admin_logout_service
from template_config import templates

router = APIRouter()


@router.get("/admin/login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    # If already logged in as platform admin, redirect to dashboard
    if request.session.get("is_platform_admin"):
        return RedirectResponse(url="/admin-dashboard", status_code=302)
    return templates.TemplateResponse(request=request, name="admin/login.html")


@router.post("/admin/login")
def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    return admin_login_service(request=request, username=username, password=password)


@router.get("/admin/logout")
def admin_logout(request: Request):
    admin_logout_service(request)
    return RedirectResponse(url="/admin/login", status_code=302)

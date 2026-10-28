from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from poker.services.auth.create_group import create_group_service
from poker.template_config import templates

router = APIRouter()


@router.get("/create-group", response_class=HTMLResponse)
def create_group_page(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(request=request, name="auth/create_group.html")


@router.post("/create-group")
def create_group(request: Request, group_name: str = Form(...)):
    user_id = request.session.get("user_id")
    if not user_id:
        return {"success": False, "error_code": "loginRequired"}

    result = create_group_service(
        request=request,
        user_id=user_id,
        group_name=group_name,
    )
    return result

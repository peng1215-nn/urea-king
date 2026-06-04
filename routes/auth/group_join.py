from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse

from services.auth.group_join import group_join_service
from template_config import templates


router = APIRouter()


@router.get(
    "/group-join",
    response_class=HTMLResponse,
)
def group_join_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth/group_join.html",
    )


@router.post("/group-join")
def group_join(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    invite_code: str = Form(...),
):
    return group_join_service(
        request=request,
        username=username,
        password=password,
        invite_code=invite_code,
    )
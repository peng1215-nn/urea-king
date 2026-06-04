from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from services.common.common import add_no_cache_headers
from template_config import templates


router = APIRouter()


def require_user(request: Request):
    return request.session.get("current_role") == "user"


@router.get("/user-dashboard", response_class=HTMLResponse)
def user_dashboard(request: Request):
    if not require_user(request):
        return RedirectResponse(url="/login", status_code=302)

    response = templates.TemplateResponse(
        request=request,
        name="user/dashboard.html",
        context={"current_page": "dashboard"},
    )
    return add_no_cache_headers(response)
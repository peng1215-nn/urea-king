from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from services.common.common import add_no_cache_headers
from template_config import templates


router = APIRouter()


def require_organizer(request: Request):
    return request.session.get("current_role") == "organizer"


@router.get(
    "/organizer-dashboard",
    response_class=HTMLResponse,
)
def organizer_dashboard(request: Request):
    if not require_organizer(request):
        return RedirectResponse(
            url="/login",
            status_code=302,
        )

    response = templates.TemplateResponse(
        request=request,
        name="organizer/dashboard.html",
        context={
            "current_page": "dashboard",
        },
    )

    return add_no_cache_headers(response)
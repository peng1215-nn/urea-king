from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from root.services.index import get_index_context, is_poker_host
from root.template_config import templates

router = APIRouter()


@router.get("/")
async def index(request: Request):
    host = request.headers.get("host", "")
    if is_poker_host(host):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(
        request,
        "index.html",
        get_index_context(),
    )

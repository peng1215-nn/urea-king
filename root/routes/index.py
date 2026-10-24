from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from root.services.index import get_index_context, should_redirect_to_poker
from root.template_config import templates

router = APIRouter()


# HEAD：在线监控、搜索引擎常用它检查页面是否存在
@router.api_route("/", methods=["GET", "HEAD"])
async def index(request: Request):
    host = request.headers.get("host", "")
    if should_redirect_to_poker(host):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(
        request,
        "index.html",
        get_index_context(),
    )

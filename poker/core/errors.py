"""
错误处理：
- safe_error()：在 except 块里调用，记录完整异常到日志，只把通用错误码返回给前端，
  避免把数据库报错、内部路径等细节暴露给用户。
- 全局异常处理器：浏览器请求返回自定义错误页，接口请求返回 JSON。
"""

import logging

from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse


logger = logging.getLogger("poker.error")


def safe_error(exc=None, message="operationFailed"):
    logger.error("operation failed", exc_info=exc if exc is not None else True)
    return message


def _wants_html(request):
    accept = request.headers.get("accept") or ""
    return request.method == "GET" and "text/html" in accept


_STATUS_MESSAGES = {
    404: "notFound",
    405: "methodNotAllowed",
}


def _render_error_page(request, status_code):
    from poker.template_config import templates

    return templates.TemplateResponse(
        request=request,
        name="common/error.html",
        context={"status_code": status_code},
        status_code=status_code,
    )


async def http_exception_handler(request, exc):
    if _wants_html(request) and exc.status_code in (404, 405):
        response = _render_error_page(request, exc.status_code)
    else:
        response = JSONResponse(
            {
                "success": False,
                "message": _STATUS_MESSAGES.get(exc.status_code, str(exc.detail)),
            },
            status_code=exc.status_code,
        )

    if getattr(exc, "headers", None):
        for name, value in exc.headers.items():
            response.headers[name] = value

    return response


async def unhandled_exception_handler(request, exc):
    # 异常细节已由请求日志中间件记录，这里只负责返回友好的结果
    if _wants_html(request):
        try:
            return _render_error_page(request, 500)
        except Exception:
            logger.exception("failed to render error page")

    return JSONResponse(
        {"success": False, "message": "operationFailed"},
        status_code=500,
    )


def register_exception_handlers(app):
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

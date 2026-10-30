"""
错误处理：
- safe_error()：在 except 块里调用，记录完整异常到日志，只把通用错误码返回给前端，
  避免把数据库报错、内部路径等细节暴露给用户。
- 全局异常处理器：浏览器请求返回自定义错误页，接口请求返回 JSON。
"""

import logging

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse


logger = logging.getLogger("core.error")


def safe_error(exc=None, message="operationFailed"):
    logger.error("operation failed", exc_info=exc if exc is not None else True)
    return message


def _wants_html(request):
    accept = request.headers.get("accept") or ""
    return request.method == "GET" and "text/html" in accept


_STATUS_MESSAGES = {
    404: "notFound",
    405: "methodNotAllowed",
    413: "requestTooLarge",
}


def _render_error_page(request, status_code):
    """错误页由模块在 register_exception_handlers() 时提供：(request, status_code) -> Response。"""
    renderer = getattr(request.app.state, "error_page_renderer", None)
    if renderer is None:
        raise RuntimeError("no error page renderer configured")
    return renderer(request, status_code)


async def http_exception_handler(request, exc):
    has_page = getattr(request.app.state, "error_page_renderer", None) is not None
    if _wants_html(request) and exc.status_code in (404, 405) and has_page:
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


async def validation_exception_handler(request, exc):
    # 参数缺失或格式不对（如金额填了字母）。默认的 422 会把参数名、类型和提交的原值带回去，
    # 这里只返回通用提示；细节写进日志方便排查。
    # 只记录出错的字段和原因，不记录提交的值（可能是密码）
    errors = [
        {"loc": list(error.get("loc", ())), "type": error.get("type")}
        for error in exc.errors()
    ]
    logger.info("request validation failed", extra={"path": request.url.path, "errors": errors})
    return JSONResponse(
        {"success": False, "message": "invalidRequest"},
        status_code=422,
    )


def register_exception_handlers(app, error_page_renderer=None):
    app.state.error_page_renderer = error_page_renderer
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

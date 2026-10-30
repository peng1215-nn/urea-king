"""
全局 HTTP 中间件：安全响应头、CSRF（来源校验）、会话有效性核对、请求日志。

在 main.py 中的注册顺序决定执行顺序，见 main.py 的注释。
"""

import logging
import threading
import time
import uuid
from urllib.parse import urlsplit

from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse, RedirectResponse

from core import settings
from core.settings import IS_PRODUCTION


logger = logging.getLogger("core.request")


# ───────────────────────── 安全响应头 ─────────────────────────

# 页面用到的外部资源：cdnjs（脚本、Font Awesome 样式与字体）、
# Google Fonts（首页）、Cloudinary（头像）。
# 脚本：不允许任何内联脚本（<script> 块、onclick 等），只运行本站和 cdnjs 的脚本文件。
#   页面上的点击等事件统一用 data-on-click 等属性，由 static/js/common/actions.js 分发。
#   tests/unit/test_no_inline_scripts.py 会检查有没有人重新写回内联脚本。
# 样式：仍允许内联样式（style="..."），内联样式无法执行代码，风险远小于内联脚本。
CONTENT_SECURITY_POLICY = "; ".join([
    "default-src 'self'",
    "script-src 'self' https://cdnjs.cloudflare.com",
    "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com",
    "font-src 'self' data: https://cdnjs.cloudflare.com https://fonts.gstatic.com",
    "img-src 'self' data: blob: https://res.cloudinary.com",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])

SECURITY_HEADERS = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
}

HSTS_VALUE = "max-age=15552000"


async def security_headers(request, call_next):
    response = await call_next(request)

    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)

    if IS_PRODUCTION:
        response.headers.setdefault("Strict-Transport-Security", HSTS_VALUE)

    return response


# ───────────────────────── CSRF：来源校验 ─────────────────────────

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _netloc(value):
    try:
        return urlsplit(value).netloc.lower()
    except ValueError:
        return ""


def is_same_origin_request(request):
    """
    对会修改数据的请求，要求 Origin（或 Referer）与本站主机一致。
    两者都没有时放行（非浏览器客户端）；浏览器跨站发起的请求一定带 Origin。
    """
    if request.method in SAFE_METHODS:
        return True

    source = request.headers.get("origin")

    if source is None:
        referer = request.headers.get("referer")
        if not referer:
            return True
        source = referer

    if source == "null":
        return False

    source_host = _netloc(source)

    allowed = {
        (request.headers.get("host") or "").lower(),
        (request.headers.get("x-forwarded-host") or "").split(",")[0].strip().lower(),
    }
    allowed.discard("")

    return source_host in allowed


async def origin_check(request, call_next):
    if not is_same_origin_request(request):
        logger.warning(
            "blocked cross-origin request",
            extra={
                "path": request.url.path,
                "origin": request.headers.get("origin"),
                "referer": request.headers.get("referer"),
            },
        )
        return JSONResponse(
            {"success": False, "message": "forbiddenOrigin"},
            status_code=403,
        )

    return await call_next(request)


# ───────────────────────── 会话有效性核对 ─────────────────────────

# 被禁用、被移出组或改过密码的账号，最多在这段时间后失去访问权限
# （改密码、重置密码的接口会主动清空缓存，立即生效）
SESSION_CHECK_TTL = 15

_session_cache = {}
_session_cache_lock = threading.Lock()

_SKIP_PREFIXES = ("/static", "/healthz", "/readyz")

# 各模块在 install_middleware() 时提供，存在 app.state 上（账号各模块独立，核对方式也由模块决定）：
#   public_paths：登录失效时也照常打开的页面
#   session_key：session -> 可哈希的键；返回 None 表示未登录，不核对
#   session_validator：键 -> 是否仍然有效


def _session_is_valid(key, validator):
    return validator(key)


def _cached_session_is_valid(key, validator):
    now = time.monotonic()

    with _session_cache_lock:
        cached = _session_cache.get(key)
        if cached and cached[1] > now:
            return cached[0]

    valid = _session_is_valid(key, validator)

    with _session_cache_lock:
        if len(_session_cache) > 5000:
            _session_cache.clear()
        _session_cache[key] = (valid, now + SESSION_CHECK_TTL)

    return valid


def clear_session_cache():
    with _session_cache_lock:
        _session_cache.clear()


def _wants_html(request):
    return request.method == "GET" and "text/html" in (request.headers.get("accept") or "")


# 登录时写入会话的时间戳键名（秒）。测试里可以替换 now_timestamp 模拟时间流逝。
LOGIN_AT_KEY = "login_at"


def now_timestamp():
    return int(time.time())


def _login_too_old(session):
    """
    登录超过 SESSION_ABSOLUTE_MAX_AGE 返回 True。
    上线前就已登录的会话没有登录时间：从这次请求开始计时，不把大家一次性踢下线。
    """
    login_at = session.get(LOGIN_AT_KEY)
    if not isinstance(login_at, int):
        session[LOGIN_AT_KEY] = now_timestamp()
        return False
    return now_timestamp() - login_at > settings.SESSION_ABSOLUTE_MAX_AGE


async def session_guard(request, call_next):
    path = request.url.path

    config = getattr(request.app.state, "session_guard", None)

    if path.startswith(_SKIP_PREFIXES) or config is None:
        return await call_next(request)

    key = config["session_key"](request.session)

    if key is not None:
        if _login_too_old(request.session):
            valid = False
        else:
            try:
                valid = await run_in_threadpool(_cached_session_is_valid, key, config["session_validator"])
            except Exception:
                # 数据库暂时不可用时不在这里拦截，后续处理自己会报错
                logger.exception("session check failed", extra={"path": path})
                valid = True

        if not valid:
            request.session.clear()

            if path not in config["public_paths"]:
                if _wants_html(request):
                    return RedirectResponse(url="/login", status_code=302)
                return JSONResponse(
                    {"success": False, "message": "sessionExpired"},
                    status_code=401,
                )

    return await call_next(request)


# ───────────────────────── 请求日志 ─────────────────────────

async def request_logging(request, call_next):
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
    started = time.perf_counter()
    path = request.url.path

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "unhandled error",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": path,
            },
        )
        raise

    response.headers["X-Request-ID"] = request_id

    if not path.startswith("/static") and path not in ("/healthz", "/readyz"):
        try:
            user_id = request.session.get("user_id")
        except AssertionError:
            user_id = None

        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                "user_id": user_id,
            },
        )

    return response


# ───────────────────────── 注册 ─────────────────────────

def install_middleware(app, domain_router=None, public_paths=(), session_key=None, session_validator=None):
    """
    Starlette 中后注册的在外层。请求进入时的执行顺序（外 → 内）：
      security_headers → SessionMiddleware → request_logging → domain_router
      → origin_check → session_guard → 路由

    session_key / session_validator / public_paths 由模块提供，见 poker/core/session.py。
    """
    if session_key is not None and session_validator is not None:
        app.state.session_guard = {
            "public_paths": frozenset(public_paths),
            "session_key": session_key,
            "session_validator": session_validator,
        }

    app.add_middleware(BaseHTTPMiddleware, dispatch=session_guard)
    app.add_middleware(BaseHTTPMiddleware, dispatch=origin_check)
    if domain_router is not None:
        app.add_middleware(BaseHTTPMiddleware, dispatch=domain_router)
    app.add_middleware(BaseHTTPMiddleware, dispatch=request_logging)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET_KEY,
        max_age=settings.SESSION_MAX_AGE,
        same_site="lax",
        https_only=settings.SESSION_HTTPS_ONLY,
    )
    app.add_middleware(BaseHTTPMiddleware, dispatch=security_headers)

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

from poker.core import settings
from poker.core.settings import IS_PRODUCTION


logger = logging.getLogger("poker.request")


# ───────────────────────── 安全响应头 ─────────────────────────

# 首页点 POKER 时会在 iframe 里预加载 poker 子站，所以两边都要放行：
#   frame-src：首页可以嵌入 poker 子站（settings.FRAME_SOURCES，来自 POKER_URL）；
#   frame-ancestors：poker 页面只允许被本站和主域名嵌入（settings.FRAME_ANCESTORS）。
# 不再发送 X-Frame-Options：它无法表达“允许另一个指定域名”，而现代浏览器以 frame-ancestors 为准。
#
# 页面用到的外部资源：cdnjs（脚本、Font Awesome 样式与字体）、
# Google Fonts（首页）、Cloudinary（头像）。内联脚本和样式目前仍大量使用，
# 因此暂时保留 'unsafe-inline'；主要收益是禁止向外站发请求、禁止被嵌入、
# 禁止加载其它来源的脚本。
CONTENT_SECURITY_POLICY = "; ".join([
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com",
    "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com",
    "font-src 'self' data: https://cdnjs.cloudflare.com https://fonts.gstatic.com",
    "img-src 'self' data: blob: https://res.cloudinary.com",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-src " + " ".join(["'self'"] + settings.FRAME_SOURCES),
    "frame-ancestors " + " ".join(["'self'"] + settings.FRAME_ANCESTORS),
])

SECURITY_HEADERS = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "X-Content-Type-Options": "nosniff",
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

# 被禁用或被移出组的账号，最多在这段时间后失去访问权限
SESSION_CHECK_TTL = 15

_session_cache = {}
_session_cache_lock = threading.Lock()

_SKIP_PREFIXES = ("/static", "/healthz", "/readyz")
_PUBLIC_PATHS = {"/", "/login", "/register", "/group-join"}


def _session_is_valid(user_id, group_id, role):
    from database import SessionLocal
    from poker.models import User, UserGroupRole

    db = SessionLocal()
    try:
        row = db.query(User.is_active).filter(User.id == user_id).first()
        if row is None or row[0] == 0:
            return False

        if role and group_id:
            membership = db.query(UserGroupRole.id).filter(
                UserGroupRole.user_id == user_id,
                UserGroupRole.group_id == group_id,
                UserGroupRole.role == role,
            ).first()
            if membership is None:
                return False

        return True
    finally:
        db.close()


def _cached_session_is_valid(user_id, group_id, role):
    key = (user_id, group_id, role)
    now = time.monotonic()

    with _session_cache_lock:
        cached = _session_cache.get(key)
        if cached and cached[1] > now:
            return cached[0]

    valid = _session_is_valid(user_id, group_id, role)

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


async def session_guard(request, call_next):
    path = request.url.path

    if path.startswith(_SKIP_PREFIXES):
        return await call_next(request)

    user_id = request.session.get("user_id")

    if user_id:
        try:
            valid = await run_in_threadpool(
                _cached_session_is_valid,
                user_id,
                request.session.get("current_group_id"),
                request.session.get("current_role"),
            )
        except Exception:
            # 数据库暂时不可用时不在这里拦截，后续处理自己会报错
            logger.exception("session check failed", extra={"path": path})
            valid = True

        if not valid:
            request.session.clear()

            if path not in _PUBLIC_PATHS:
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

def install_middleware(app, domain_router=None):
    """
    Starlette 中后注册的在外层。请求进入时的执行顺序（外 → 内）：
      security_headers → SessionMiddleware → request_logging → domain_router
      → origin_check → session_guard → 路由
    """
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

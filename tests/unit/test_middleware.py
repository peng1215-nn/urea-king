"""
用一个最小的 Starlette 应用加载真实的中间件与异常处理器，不需要数据库。
"""

import pytest
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from poker.core import middleware
from poker.core.errors import register_exception_handlers


BASE = "http://poker.test"
SAME_ORIGIN = {"origin": BASE}


async def page(request):
    return HTMLResponse("<p>page</p>")


async def api(request):
    return JSONResponse({"success": True})


async def sign_in(request):
    request.session.update({"user_id": 1, "current_role": "organizer", "current_group_id": 2})
    return JSONResponse({"success": True})


async def login_page(request):
    return HTMLResponse("login")


async def boom(request):
    raise ValueError("secret internal detail")


@pytest.fixture
def session_valid(monkeypatch):
    state = {"valid": True}
    monkeypatch.setattr(middleware, "_session_is_valid", lambda *args: state["valid"])
    middleware.clear_session_cache()
    yield state
    middleware.clear_session_cache()


@pytest.fixture
def client(session_valid):
    app = Starlette(routes=[
        Route("/page", page),
        Route("/api", api, methods=["POST"]),
        Route("/sign-in", sign_in, methods=["POST"]),
        Route("/login", login_page),
        Route("/boom", boom),
    ])
    register_exception_handlers(app)
    middleware.install_middleware(app)
    return TestClient(app, base_url=BASE, raise_server_exceptions=False)


def test_security_headers_are_set(client):
    response = client.get("/page")
    assert response.status_code == 200
    assert "connect-src 'self'" in response.headers["content-security-policy"]
    csp = response.headers["content-security-policy"]
    assert "frame-ancestors 'self' https://urea-king.com https://www.urea-king.com" in csp
    assert "frame-src 'self' https://poker.urea-king.com" in csp
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert response.headers["x-request-id"]


def test_cross_origin_post_is_blocked(client):
    response = client.post("/api", headers={"origin": "https://evil.example"})
    assert response.status_code == 403
    assert response.json()["message"] == "forbiddenOrigin"


def test_cross_origin_referer_is_blocked(client):
    response = client.post("/api", headers={"referer": "https://evil.example/form"})
    assert response.status_code == 403


def test_null_origin_is_blocked(client):
    assert client.post("/api", headers={"origin": "null"}).status_code == 403


def test_same_origin_post_is_allowed(client):
    assert client.post("/api", headers=SAME_ORIGIN).status_code == 200


def test_post_without_origin_or_referer_is_allowed(client):
    # 浏览器跨站请求一定带 Origin；没有任何来源头的只可能是非浏览器客户端
    assert client.post("/api").status_code == 200


def test_session_cookie_flags(client):
    response = client.post("/sign-in", headers=SAME_ORIGIN)
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie


def test_invalid_session_redirects_pages_to_login(client, session_valid):
    client.post("/sign-in", headers=SAME_ORIGIN)
    session_valid["valid"] = False

    response = client.get("/page", headers={"accept": "text/html"}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


def test_invalid_session_returns_401_for_api(client, session_valid):
    client.post("/sign-in", headers=SAME_ORIGIN)
    session_valid["valid"] = False

    response = client.post("/api", headers=SAME_ORIGIN)
    assert response.status_code == 401
    assert response.json()["message"] == "sessionExpired"


def test_public_page_still_loads_with_invalid_session(client, session_valid):
    client.post("/sign-in", headers=SAME_ORIGIN)
    session_valid["valid"] = False
    assert client.get("/login", headers={"accept": "text/html"}).status_code == 200


def test_valid_session_passes(client):
    client.post("/sign-in", headers=SAME_ORIGIN)
    assert client.get("/page", headers={"accept": "text/html"}).status_code == 200


def test_unknown_page_renders_custom_404(client):
    response = client.get("/missing", headers={"accept": "text/html"})
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]
    assert "404" in response.text


def test_unknown_api_returns_json_404(client):
    response = client.get("/missing", headers={"accept": "application/json"})
    assert response.status_code == 404
    assert response.json() == {"success": False, "message": "notFound"}


def test_unhandled_error_does_not_leak_details(client):
    response = client.get("/boom", headers={"accept": "application/json"})
    assert response.status_code == 500
    assert response.json() == {"success": False, "message": "operationFailed"}
    assert "secret" not in response.text


def test_unhandled_error_renders_html_page_for_browsers(client):
    response = client.get("/boom", headers={"accept": "text/html"})
    assert response.status_code == 500
    assert "text/html" in response.headers["content-type"]
    assert "secret" not in response.text

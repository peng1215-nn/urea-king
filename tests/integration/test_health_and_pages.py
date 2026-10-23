def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_checks_database(client):
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_healthz_works_with_platform_host_header(client):
    # 平台健康检查用的 Host 不是我们的域名，不能被跳转到首页
    response = client.get("/healthz", headers={"host": "healthcheck.railway.app"})
    assert response.status_code == 200


def test_login_page_has_security_headers(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert "content-security-policy" in response.headers
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_unknown_page_returns_custom_404(client):
    response = client.get("/this-page-does-not-exist", headers={"accept": "text/html"})
    assert response.status_code == 404
    assert "404" in response.text


def test_cross_origin_login_post_is_rejected(client):
    response = client.post(
        "/login",
        data={"username": "someone", "password": "whatever123"},
        headers={"origin": "https://evil.example"},
    )
    assert response.status_code == 403

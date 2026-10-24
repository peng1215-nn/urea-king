from poker.core import settings


def test_production_serves_poker_only_on_poker_subdomain(monkeypatch):
    monkeypatch.setattr(settings, "IS_STAGING", False)
    assert settings.is_poker_host("poker.urea-king.com") is True
    assert settings.is_poker_host("urea-king.com") is False


def test_staging_serves_poker_on_any_host(monkeypatch):
    monkeypatch.setattr(settings, "IS_STAGING", True)
    assert settings.is_poker_host("urea-king-staging.onrender.com") is True


def test_production_links_point_to_real_domains(monkeypatch):
    monkeypatch.setattr(settings, "IS_STAGING", False)
    monkeypatch.delenv("ROOT_URL", raising=False)
    monkeypatch.delenv("POKER_URL", raising=False)
    assert settings.root_url() == "https://urea-king.com"
    assert settings.poker_url() == "https://poker.urea-king.com"


def test_staging_links_stay_on_the_staging_site(monkeypatch):
    monkeypatch.setattr(settings, "IS_STAGING", True)
    monkeypatch.delenv("ROOT_URL", raising=False)
    monkeypatch.delenv("POKER_URL", raising=False)
    assert settings.root_url() == "/"
    assert settings.poker_url() == "/login"


def test_staging_shows_landing_page_at_root(monkeypatch):
    from root.services.index import should_redirect_to_poker

    monkeypatch.setattr(settings, "IS_STAGING", True)
    assert should_redirect_to_poker("urea-king-staging.onrender.com") is False

    monkeypatch.setattr(settings, "IS_STAGING", False)
    assert should_redirect_to_poker("poker.urea-king.com") is True
    assert should_redirect_to_poker("urea-king.com") is False

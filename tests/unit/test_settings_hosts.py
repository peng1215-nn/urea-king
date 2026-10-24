from poker.core import settings


def test_production_serves_poker_only_on_poker_subdomain(monkeypatch):
    monkeypatch.setattr(settings, "IS_STAGING", False)
    assert settings.is_poker_host("poker.urea-king.com") is True
    assert settings.is_poker_host("urea-king.com") is False


def test_staging_serves_poker_on_any_host(monkeypatch):
    monkeypatch.setattr(settings, "IS_STAGING", True)
    assert settings.is_poker_host("urea-king-staging.onrender.com") is True

from poker.core import error_reporting


def test_disabled_without_dsn(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    assert error_reporting.setup_error_reporting() is False


def test_enabled_with_dsn(monkeypatch):
    import sentry_sdk

    calls = {}
    monkeypatch.setenv("SENTRY_DSN", "https://key@example.ingest.sentry.io/1")
    monkeypatch.setattr(sentry_sdk, "init", lambda **kwargs: calls.update(kwargs))

    assert error_reporting.setup_error_reporting() is True
    assert calls["send_default_pii"] is False
    assert calls["traces_sample_rate"] == 0

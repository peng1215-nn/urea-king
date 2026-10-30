from core import error_reporting


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


def test_local_variables_and_sql_parameters_are_not_sent(monkeypatch):
    import sentry_sdk

    calls = {}
    monkeypatch.setenv("SENTRY_DSN", "https://key@example.ingest.sentry.io/1")
    monkeypatch.setattr(sentry_sdk, "init", lambda **kwargs: calls.update(kwargs))
    error_reporting.setup_error_reporting()
    assert calls["include_local_variables"] is False

    event = {
        "exception": {"values": [{"value": "IntegrityError [SQL: INSERT ...] [parameters: ('a@b.com', 'secret-token')]"}]},
        "request": {"data": "password=x"},
    }
    scrubbed = calls["before_send"](event, None)
    assert "secret-token" not in str(scrubbed)
    assert "request" not in scrubbed

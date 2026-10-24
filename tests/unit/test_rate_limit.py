from core.rate_limit import SlidingWindowLimiter
from poker.core.rate_limit import login_keys


def test_blocks_after_max_events_within_window():
    limiter = SlidingWindowLimiter(max_events=3, window_seconds=60)
    for t in (0, 1, 2):
        assert limiter.retry_after("k", now=t) == 0
        limiter.hit("k", now=t)
    assert limiter.retry_after("k", now=3) > 0


def test_other_keys_are_not_affected():
    limiter = SlidingWindowLimiter(max_events=1, window_seconds=60)
    limiter.hit("a", now=0)
    assert limiter.retry_after("a", now=1) > 0
    assert limiter.retry_after("b", now=1) == 0


def test_unblocks_after_window_passes():
    limiter = SlidingWindowLimiter(max_events=2, window_seconds=60)
    limiter.hit("k", now=0)
    limiter.hit("k", now=10)
    assert limiter.retry_after("k", now=30) > 0
    # 第一次失败过期后，又能再试一次
    assert limiter.retry_after("k", now=61) == 0


def test_retry_after_counts_down():
    limiter = SlidingWindowLimiter(max_events=1, window_seconds=60)
    limiter.hit("k", now=0)
    assert limiter.retry_after("k", now=10) > limiter.retry_after("k", now=50) > 0


def test_reset_clears_key():
    limiter = SlidingWindowLimiter(max_events=1, window_seconds=60)
    limiter.hit("k", now=0)
    limiter.reset("k")
    assert limiter.retry_after("k", now=1) == 0


def test_memory_is_bounded():
    limiter = SlidingWindowLimiter(max_events=5, window_seconds=60, max_keys=100)
    for i in range(1000):
        limiter.hit(f"key-{i}", now=i * 0.001)
    assert len(limiter._events) <= 100


def test_login_keys_are_case_insensitive_for_username():
    assert login_keys("1.2.3.4", "Alice ") == login_keys("1.2.3.4", "alice")
    assert login_keys(None, "alice")[1] == "unknown"


def test_trusted_login_expires():
    from poker.core import rate_limit

    rate_limit.clear_trusted_logins()
    rate_limit.remember_trusted_login("1.1.1.1", "Alice", now=0)
    assert rate_limit.is_trusted_login("1.1.1.1", "alice", now=10)
    assert not rate_limit.is_trusted_login("2.2.2.2", "alice", now=10)
    assert not rate_limit.is_trusted_login("1.1.1.1", "alice", now=rate_limit.TRUSTED_LOGIN_TTL + 1)
    rate_limit.clear_trusted_logins()


def test_username_limit_does_not_block_trusted_device():
    from poker.core import rate_limit

    rate_limit.clear_trusted_logins()
    rate_limit.login_failures_by_username._events.clear()
    rate_limit.login_failures_by_account._events.clear()
    rate_limit.login_failures_by_ip._events.clear()

    rate_limit.record_login_success("1.1.1.1", "owner")
    for i in range(20):
        rate_limit.record_login_failure(f"9.9.9.{i}", "owner")  # 攻击者轮换 IP 乱试

    assert rate_limit.login_retry_after("8.8.8.8", "owner") > 0   # 陌生来源被挡
    assert rate_limit.login_retry_after("1.1.1.1", "owner") == 0  # 账号主人的设备不受影响

    rate_limit.clear_trusted_logins()
    for limiter in (rate_limit.login_failures_by_username, rate_limit.login_failures_by_account, rate_limit.login_failures_by_ip):
        limiter._events.clear()

from poker.core.rate_limit import SlidingWindowLimiter, login_keys


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

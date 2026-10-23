"""
进程内滑动窗口限流（不依赖第三方库）。

适用于当前的单实例部署。若将来扩展到多个实例，每个实例各自计数，
限制会相应放宽；届时应改为基于数据库或 Redis 的共享计数。
"""

import threading
import time
from collections import deque


class SlidingWindowLimiter:
    def __init__(self, max_events, window_seconds, max_keys=10000):
        self.max_events = max_events
        self.window = window_seconds
        self.max_keys = max_keys
        self._events = {}
        self._lock = threading.Lock()

    def _prune(self, key, now):
        events = self._events.get(key)
        if not events:
            return None
        cutoff = now - self.window
        while events and events[0] <= cutoff:
            events.popleft()
        if not events:
            del self._events[key]
            return None
        return events

    def retry_after(self, key, now=None):
        """已达上限时返回需要等待的秒数，否则返回 0。"""
        now = time.monotonic() if now is None else now
        with self._lock:
            events = self._prune(key, now)
            if events is None or len(events) < self.max_events:
                return 0
            return max(1, int(events[0] + self.window - now) + 1)

    def hit(self, key, now=None):
        now = time.monotonic() if now is None else now
        with self._lock:
            events = self._prune(key, now)
            if events is None:
                if len(self._events) >= self.max_keys:
                    self._evict(now)
                events = deque()
                self._events[key] = events
            events.append(now)

    def reset(self, key):
        with self._lock:
            self._events.pop(key, None)

    def _evict(self, now):
        # 先清掉过期的键；仍然太多时丢弃最早的一半，防止内存被撑爆
        for key in list(self._events.keys()):
            self._prune(key, now)
        if len(self._events) >= self.max_keys:
            oldest = sorted(self._events.items(), key=lambda kv: kv[1][-1])
            for key, _ in oldest[: len(oldest) // 2]:
                del self._events[key]


WINDOW = 15 * 60

# IP 取自 X-Forwarded-For，客户端可以伪造；所以每类限制都另有一道与 IP 无关的上限。

# 登录（以及需要输入密码的“邀请码加入组”）：15 分钟内
#   同一 IP + 用户名最多失败 5 次；同一 IP 最多失败 30 次；
#   同一用户名（不论来源）最多失败 20 次——但曾在该 IP 成功登录过的不受这一条限制，
#   避免别人靠故意输错密码把账号主人锁在外面。
login_failures_by_account = SlidingWindowLimiter(5, WINDOW)
login_failures_by_ip = SlidingWindowLimiter(30, WINDOW)
login_failures_by_username = SlidingWindowLimiter(20, WINDOW)

# 邀请码：同一 IP 15 分钟内最多 10 次邀请码相关失败；
# “邀请码不存在”（猜码）全站合计最多 300 次
register_failures_by_ip = SlidingWindowLimiter(10, WINDOW)
group_join_failures_by_ip = SlidingWindowLimiter(10, WINDOW)
invite_failures_global = SlidingWindowLimiter(300, WINDOW)

GLOBAL_KEY = "global"


def login_keys(ip, username):
    return (f"{ip}|{(username or '').strip().lower()}", ip or "unknown")


def username_key(username):
    return (username or "").strip().lower()


# ───── 成功登录过的 (IP, 用户名) ─────

TRUSTED_LOGIN_TTL = 30 * 24 * 3600
_TRUSTED_MAX = 20000
_trusted_logins = {}
_trusted_lock = threading.Lock()


def remember_trusted_login(ip, username, now=None):
    now = time.monotonic() if now is None else now
    key = login_keys(ip, username)[0]
    with _trusted_lock:
        if len(_trusted_logins) >= _TRUSTED_MAX:
            for k, expires in list(_trusted_logins.items()):
                if expires <= now:
                    del _trusted_logins[k]
            if len(_trusted_logins) >= _TRUSTED_MAX:
                for k in sorted(_trusted_logins, key=_trusted_logins.get)[: _TRUSTED_MAX // 2]:
                    del _trusted_logins[k]
        _trusted_logins[key] = now + TRUSTED_LOGIN_TTL


def is_trusted_login(ip, username, now=None):
    now = time.monotonic() if now is None else now
    key = login_keys(ip, username)[0]
    with _trusted_lock:
        expires = _trusted_logins.get(key)
        return expires is not None and expires > now


def clear_trusted_logins():
    with _trusted_lock:
        _trusted_logins.clear()


# ───── 登录类请求的统一入口（登录、邀请码加入组共用） ─────

def login_retry_after(ip, username):
    account_key, ip_key = login_keys(ip, username)
    waits = [
        login_failures_by_account.retry_after(account_key),
        login_failures_by_ip.retry_after(ip_key),
    ]
    if not is_trusted_login(ip, username):
        waits.append(login_failures_by_username.retry_after(username_key(username)))
    return max(waits)


def record_login_failure(ip, username):
    account_key, ip_key = login_keys(ip, username)
    login_failures_by_account.hit(account_key)
    login_failures_by_ip.hit(ip_key)
    login_failures_by_username.hit(username_key(username))


def record_login_success(ip, username):
    login_failures_by_account.reset(login_keys(ip, username)[0])
    remember_trusted_login(ip, username)

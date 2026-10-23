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

# 登录：同一 IP + 用户名 15 分钟内最多失败 5 次；同一 IP 最多失败 30 次；
# 同一用户名（不论来源）最多失败 20 次
login_failures_by_account = SlidingWindowLimiter(5, WINDOW)
login_failures_by_ip = SlidingWindowLimiter(30, WINDOW)
login_failures_by_username = SlidingWindowLimiter(20, WINDOW)

# 注册、用邀请码加入组：同一 IP 15 分钟内最多 10 次失败；全站合计最多 100 次（防止暴力猜邀请码）
register_failures_by_ip = SlidingWindowLimiter(10, WINDOW)
group_join_failures_by_ip = SlidingWindowLimiter(10, WINDOW)
invite_failures_global = SlidingWindowLimiter(100, WINDOW)

GLOBAL_KEY = "global"


def login_keys(ip, username):
    return (f"{ip}|{(username or '').strip().lower()}", ip or "unknown")


def username_key(username):
    return (username or "").strip().lower()

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

    def _append(self, key, now):
        events = self._prune(key, now)
        if events is None:
            if len(self._events) >= self.max_keys:
                self._evict(now)
            events = deque()
            self._events[key] = events
        events.append(now)

    def hit(self, key, now=None):
        """计数一次，返回这次的时间戳（可用于 undo）。"""
        now = time.monotonic() if now is None else now
        with self._lock:
            self._append(key, now)
        return now

    def try_hit(self, key, now=None):
        """
        检查与计数一步完成，避免并发请求同时通过检查。
        未达上限：计数一次，返回 (0, 时间戳)；已达上限：不计数，返回 (等待秒数, None)。
        """
        now = time.monotonic() if now is None else now
        with self._lock:
            events = self._prune(key, now)
            if events is not None and len(events) >= self.max_events:
                return max(1, int(events[0] + self.window - now) + 1), None
            self._append(key, now)
            return 0, now

    def undo(self, key, stamp):
        """撤销一次之前的计数（例如密码校验通过后，撤销预先占用的失败名额）。"""
        if stamp is None:
            return
        with self._lock:
            events = self._events.get(key)
            if not events:
                return
            try:
                events.remove(stamp)
            except ValueError:
                return
            if not events:
                del self._events[key]

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

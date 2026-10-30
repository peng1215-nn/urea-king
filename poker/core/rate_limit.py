"""
poker 模块的限流规则：登录、注册、加入组、邀请码。
限流工具本身在 core/rate_limit.py。
"""

import threading
import time

from core.rate_limit import SlidingWindowLimiter


WINDOW = 15 * 60

# IP 取自 X-Forwarded-For，客户端可以伪造；所以每类限制都另有一道与 IP 无关的上限。

# 登录（以及需要输入密码的“邀请码加入组”）：15 分钟内
#   同一 IP + 用户名最多失败 5 次；同一 IP 最多失败 30 次；
#   同一用户名（不论来源）最多失败 20 次——但曾在该 IP 成功登录过的不受这一条限制，
#   避免别人靠故意输错密码把账号主人锁在外面。
login_failures_by_account = SlidingWindowLimiter(5, WINDOW)
login_failures_by_ip = SlidingWindowLimiter(30, WINDOW)
# 这一条是防分布式猜密码的唯一屏障，多留一些键的空间
login_failures_by_username = SlidingWindowLimiter(20, WINDOW, max_keys=100000)

# 所有需要校验密码的请求（登录、邀请码加组、注销、更换验证邮箱），不论成败：同一 IP 15 分钟内最多 60 次。
# 只限制失败的话，用一个真实账号循环"正确密码登录"就能不停消耗 CPU（密码哈希）和数据库连接
password_checks_by_ip = SlidingWindowLimiter(60, WINDOW)

# 注册：同一 IP 15 分钟内最多 10 次注册请求（成功的也计数，防止借注册给任意邮箱发信）
register_failures_by_ip = SlidingWindowLimiter(10, WINDOW)

# 邀请码：同一 IP 15 分钟内最多 10 次邀请码相关失败；
# “邀请码不存在”（猜码）全站合计最多 300 次；局头创建邀请码时撞到已存在的码也计入
group_join_failures_by_ip = SlidingWindowLimiter(10, WINDOW)
invite_failures_global = SlidingWindowLimiter(300, WINDOW)

# 重发验证邮件：同一 IP 15 分钟内最多 10 次请求
resend_verify_failures_by_ip = SlidingWindowLimiter(10, WINDOW)

# 忘记密码：同一 IP 15 分钟内最多 10 次
forgot_password_failures_by_ip = SlidingWindowLimiter(10, WINDOW)

# 重置密码提交：同一 IP 15 分钟内最多 10 次无效链接
reset_password_failures_by_ip = SlidingWindowLimiter(10, WINDOW)

# 修改密码时输错当前密码：同一用户 15 分钟内最多 5 次
current_password_failures_by_user = SlidingWindowLimiter(5, WINDOW)

# 更换验证邮箱（未验证账号）：同一 IP 15 分钟内最多 10 次请求
change_email_by_ip = SlidingWindowLimiter(10, WINDOW)

# 局头创建邀请码：同一用户 15 分钟内最多 20 次（防止借"邀请码已存在"试探其他组的邀请码）
invite_creates_by_user = SlidingWindowLimiter(20, WINDOW)

# 头像上传：同一用户 60 秒内最多 5 次
avatar_uploads_by_user = SlidingWindowLimiter(5, 60)

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


# ───── 先占名额、再校验：避免并发请求一起通过检查 ─────

class Reservation:
    """
    reserve() 的结果。wait > 0 表示已达上限（此时没有占用任何名额）。
    名额占用后：这次请求算作失败时什么也不用做；不算失败时调用 release() 退回名额。
    """

    def __init__(self, held=None, wait=0):
        self._held = held or []
        self.wait = wait

    def release(self):
        for limiter, key, stamp in self._held:
            limiter.undo(key, stamp)
        self._held = []

    def stamp_of(self, limiter):
        """取出某个限流器这次的计数时间戳，用于只退回其中一项。"""
        for held_limiter, _key, stamp in self._held:
            if held_limiter is limiter:
                return stamp
        return None


def reserve(entries):
    """
    entries: [(limiter, key, enforce)]。enforce=False 表示只计数、不因它拦截。
    任何一项已达上限时，退回已占的名额并返回 wait > 0。
    """
    held = []
    for limiter, key, enforce in entries:
        if enforce:
            wait, stamp = limiter.try_hit(key)
            if wait:
                Reservation(held).release()
                return Reservation(wait=wait)
        else:
            stamp = limiter.hit(key)
        held.append((limiter, key, stamp))
    return Reservation(held)


def reserve_login_attempt(ip, username):
    """
    需要校验账号密码的请求（登录、注销、改邮箱、邀请码加组）在校验之前调用。
    先按"失败"占用名额；密码正确时调用 release() 退回。
    """
    # 先按"所有请求"计数：这一项不随 release() 退回，密码正确也算一次
    wait, _ = password_checks_by_ip.try_hit(ip or "unknown")
    if wait:
        return Reservation(wait=wait)

    account_key, ip_key = login_keys(ip, username)
    reservation = reserve([
        (login_failures_by_account, account_key, True),
        (login_failures_by_ip, ip_key, True),
        # 曾在该 IP 成功登录过的不受"同一用户名"这条限制，但仍然计数
        (login_failures_by_username, username_key(username), not is_trusted_login(ip, username)),
    ])
    if reservation.wait:
        reservation.wait = max(reservation.wait, login_retry_after(ip, username))
    return reservation


def record_login_success(ip, username):
    login_failures_by_account.reset(login_keys(ip, username)[0])
    remember_trusted_login(ip, username)

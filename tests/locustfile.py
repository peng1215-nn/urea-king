"""
Ureaking Poker 压力测试脚本
目标：https://urea-king-staging.onrender.com

═══════════════════════════════════════════════════
 测试前准备
═══════════════════════════════════════════════════
1. 在 staging 手动创建两个账号（已验证邮箱、已加入同一个组）：
   - 局头账号（已建组或已是组内 organizer）：填入 ORGANIZER 常量
   - 普通用户账号（已加入该组）：填入 MEMBER 常量
2. 记好上述账号所在组的 group_id（登录后看 select-group 接口返回）

═══════════════════════════════════════════════════
 运行方式
═══════════════════════════════════════════════════
    pip install locust
    locust -f tests/locustfile.py --host=https://urea-king-staging.onrender.com
    打开 http://localhost:8089，设置：
      - 总并发用户数：建议先从 20 开始，逐步加到 100
      - 每秒增加用户数：5
      - 主机：https://urea-king-staging.onrender.com（已默认填入）

═══════════════════════════════════════════════════
 测完后清理 staging 数据库（Neon）
═══════════════════════════════════════════════════
连接 Neon staging DB，执行以下 SQL（按顺序，有外键依赖）：

    -- 1. 验证邮件记录
    DELETE FROM poker_email_verifications
    WHERE user_id IN (SELECT id FROM platform_users WHERE username LIKE 'test_%');

    -- 2. 用户模块绑定
    DELETE FROM platform_user_modules
    WHERE user_id IN (SELECT id FROM platform_users WHERE username LIKE 'test_%');

    -- 3. 组角色
    DELETE FROM poker_user_group_roles
    WHERE user_id IN (SELECT id FROM platform_users WHERE username LIKE 'test_%');

    -- 4. 成员别名
    DELETE FROM poker_group_member_aliases
    WHERE user_id IN (SELECT id FROM platform_users WHERE username LIKE 'test_%');

    -- 5. 筹码请求
    DELETE FROM poker_chip_requests
    WHERE user_id IN (SELECT id FROM platform_users WHERE username LIKE 'test_%');

    -- 6. 最后删用户本身
    DELETE FROM platform_users WHERE username LIKE 'test_%';

    -- 确认（应返回 0）
    SELECT COUNT(*) FROM platform_users WHERE username LIKE 'test_%';
"""

import random
import string
from locust import HttpUser, task, between, tag

# ─── 请在运行前修改为 staging 上实际存在的账号 ───────────────────────────
ORGANIZER = {
    "username": "test_organizer",   # staging 局头账号用户名
    "password": "Test1234!",
}
MEMBER = {
    "username": "test_member",      # staging 普通成员账号用户名
    "password": "Test1234!",
}
# ─────────────────────────────────────────────────────────────────────────


def _rand(n=8):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def _login(client, cred):
    """登录并选第一个可用组，返回 group_id（没有则 None）。"""
    resp = client.post(
        "/login",
        data=cred,
        name="POST /login",
        catch_response=True,
    )
    with resp:
        try:
            data = resp.json()
        except Exception:
            resp.failure("登录响应非 JSON")
            return None
        if not data.get("success"):
            resp.failure(f"登录失败: {data.get('message', '')}")
            return None
        resp.success()

    groups = data.get("groups", [])
    if not groups:
        return None

    gid = groups[0]["group_id"]
    client.post(
        "/select-group",
        data={"group_id": gid},
        name="POST /select-group",
    )
    return gid


# ─── 1. 游客：只访问公开页面 ──────────────────────────────────────────────
class GuestUser(HttpUser):
    """未登录访客，访问登录/注册页面。"""
    wait_time = between(1, 3)
    weight = 1

    @task(4)
    @tag("public")
    def login_page(self):
        self.client.get("/login", name="GET /login")

    @task(2)
    @tag("public")
    def register_page(self):
        self.client.get("/register", name="GET /register")

    @task(1)
    @tag("public")
    def forgot_password_page(self):
        self.client.get("/forgot-password", name="GET /forgot-password")


# ─── 2. 注册用户：测试注册接口吞吐量 ─────────────────────────────────────
class RegisterUser(HttpUser):
    """模拟批量注册（不验证邮箱），用户名统一 test_ 前缀。"""
    wait_time = between(3, 8)
    weight = 1

    @task
    @tag("register")
    def register(self):
        suffix = _rand()
        username = f"test_{suffix}"
        self.client.post(
            "/register",
            data={
                "username": username,
                "nickname": f"压测用户{suffix}",
                "email": f"{username}@locust-test.invalid",
                "password": "Test1234!",
                "confirm_password": "Test1234!",
            },
            name="POST /register",
        )


# ─── 3. 普通成员：登录后浏览用户侧页面 ──────────────────────────────────
class MemberUser(HttpUser):
    """已登录普通成员，读操作为主。"""
    wait_time = between(2, 5)
    weight = 4

    def on_start(self):
        self.group_id = _login(self.client, MEMBER)

    @task(4)
    @tag("member", "read")
    def user_dashboard(self):
        self.client.get("/user-dashboard", name="GET /user-dashboard")

    @task(3)
    @tag("member", "read")
    def user_game(self):
        self.client.get("/user-game", name="GET /user-game")

    @task(3)
    @tag("member", "read")
    def user_game_ongoing(self):
        self.client.get("/user/game/ongoing", name="GET /user/game/ongoing")

    @task(2)
    @tag("member", "read")
    def user_game_logs_page(self):
        self.client.get("/user-game-logs", name="GET /user-game-logs")

    @task(2)
    @tag("member", "read")
    def user_game_log_list(self):
        self.client.get("/user/game-log/list", name="GET /user/game-log/list")

    @task(1)
    @tag("member", "read")
    def user_game_log_stats(self):
        self.client.get("/user/game-log/stats", name="GET /user/game-log/stats")

    @task(1)
    @tag("member", "read")
    def user_announcements(self):
        self.client.get("/user/announcements", name="GET /user/announcements")

    @task(1)
    @tag("member", "auth")
    def group_select_page(self):
        self.client.get("/group-select", name="GET /group-select")


# ─── 4. 局头：登录后浏览 organizer 侧页面 ────────────────────────────────
class OrganizerUser(HttpUser):
    """已登录局头，读写操作混合。"""
    wait_time = between(2, 6)
    weight = 3

    def on_start(self):
        self.group_id = _login(self.client, ORGANIZER)

    @task(4)
    @tag("organizer", "read")
    def organizer_games(self):
        self.client.get("/organizer-games", name="GET /organizer-games")

    @task(3)
    @tag("organizer", "read")
    def organizer_game_ongoing(self):
        self.client.get("/organizer/game/ongoing", name="GET /organizer/game/ongoing")

    @task(3)
    @tag("organizer", "read")
    def organizer_members(self):
        self.client.get("/organizer/members", name="GET /organizer/members")

    @task(2)
    @tag("organizer", "read")
    def organizer_game_logs(self):
        self.client.get("/organizer-game-logs", name="GET /organizer-game-logs")

    @task(2)
    @tag("organizer", "read")
    def organizer_game_log_list(self):
        self.client.get("/organizer/game-log/list", name="GET /organizer/game-log/list")

    @task(2)
    @tag("organizer", "read")
    def organizer_invite_management(self):
        self.client.get("/organizer-invite-management", name="GET /organizer-invite-management")

    @task(1)
    @tag("organizer", "read")
    def organizer_invite_list(self):
        self.client.get("/organizer/invite/list", name="GET /organizer/invite/list")

    @task(1)
    @tag("organizer", "read")
    def organizer_group_info(self):
        self.client.get("/organizer/group-info", name="GET /organizer/group-info")

    @task(1)
    @tag("organizer", "read")
    def organizer_announcements(self):
        self.client.get("/organizer-announcements", name="GET /organizer-announcements")

    @task(1)
    @tag("organizer", "read")
    def organizer_game_log_stats(self):
        self.client.get("/organizer/game-log/stats", name="GET /organizer/game-log/stats")

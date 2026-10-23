# 开发与部署指南

## 本地开发

**需要：** Python 3.12+、PostgreSQL、Node.js（只用于检查 JS 语法）。

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

cp .env.example .env                 # 然后填写 DATABASE_URL 等
alembic upgrade head                 # 建表 / 升级到最新结构
uvicorn main:app --reload
```

浏览器打开 `http://localhost:8000/login`。本地用 `localhost` 访问即可，主机名不是 `poker.` 开头也不会被跳转。

## 数据库迁移

改了 `poker/models.py` 之后：

```bash
alembic revision --autogenerate -m "说明这次改了什么"
# 检查生成的文件，确认无误后
alembic upgrade head
```

`alembic check` 可以确认模型和迁移是否一致。

## 测试

```bash
# 只跑单元测试（不需要数据库）
pytest tests/unit

# 跑全部测试：需要一个专用测试库，库名必须包含 test
createdb poker_test
TEST_DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/poker_test pytest
```

- 集成测试会在每个用例前**清空测试库的所有表**，所以绝不要把 `TEST_DATABASE_URL` 指向开发库或线上库；库名不含 `test` 时测试会直接拒绝运行。
- 没设置 `TEST_DATABASE_URL` 时，集成测试会被跳过。
- 测试会自动对测试库执行 `alembic upgrade head`。

## 代码检查

```bash
ruff check .            # Python
ruff check . --fix      # 自动修复能修的问题
```

## 持续集成（GitHub Actions）

每次推送到 `main` 或提交 PR，会自动运行：

| 任务 | 内容 | 失败是否阻断 |
|---|---|---|
| Lint | Ruff 检查 Python；`node --check` 检查所有 JS 语法 | 是 |
| Tests | 启动 Postgres，执行迁移，运行全部测试 | 是 |
| Tests 中的 `alembic check` | 模型与迁移是否一致 | 否（先只报告） |
| Dependency audit | `pip-audit` 检查依赖已知漏洞，结果写在该次运行的 Summary 页面 | 否（只报告，不会变红） |

Dependabot 每周检查一次 Python 依赖和 GitHub Actions 版本，有更新会自动开 PR。

## 部署（Render）

**必须设置的环境变量：**

| 变量 | 说明 |
|---|---|
| `DATABASE_URL` | PostgreSQL 连接地址。缺失时应用拒绝启动。 |
| `SESSION_SECRET_KEY` | 会话签名密钥，足够长的随机字符串。生产环境缺失时应用拒绝启动。 |
| `CLOUDINARY_*` | 头像上传 |

以上变量在 Render 控制台的服务页面 → **Environment** 中设置。Render 会自动设置 `RENDER=true`，应用据此识别生产环境（也可以用 `APP_ENV` 显式指定）。

**建议在 Render 上开启的设置**（在服务的 **Settings** 中）：

- **Health Check Path** 设为 `/healthz`：新版本没有正常启动时，Render 不会把流量切过去，旧版本继续服务。
- **自动部署时机**：如果设置里有“CI 检查通过后再自动部署”的选项，等 GitHub 上的 CI 第一次跑通后再开启。
- **数据库备份**：确认数据库所在套餐有自动备份，并至少演练过一次恢复。如果数据库是 Render 的免费 PostgreSQL，请留意它的到期时间（免费数据库有使用期限），到期前要升级或迁移。

**健康检查接口：**

- `GET /healthz`：进程存活即返回 200。
- `GET /readyz`：同时检查数据库连接，数据库不可用时返回 503。

## 安全相关的行为（改代码前请了解）

- **登录限流**：15 分钟内，同一 IP + 用户名失败 5 次、同一 IP 失败 30 次、同一用户名（不论来源）失败 20 次后暂时锁定；曾在某个 IP 成功登录过的用户不受“同一用户名 20 次”这条限制，避免别人故意输错密码把账号主人锁在外面。“邀请码加入组”也要输入密码，同样计入。邀请码相关失败按 IP 限制 10 次；“邀请码不存在”全站合计不超过 300 次。客户端 IP 取自 `X-Forwarded-For`，可被伪造，所以都有不依赖 IP 的上限。计数保存在进程内存中，重启后清零；适用于当前的单实例部署，将来扩展到多个实例时需要改为共享存储（数据库或 Redis）。
- **会话核对**：每个请求都会核对账号是否被禁用、是否仍在该组担任该角色（结果缓存 15 秒）。失效时页面跳转登录，接口返回 401 `sessionExpired`。
- **CSRF**：所有修改类请求（POST 等）要求 `Origin` 或 `Referer` 与本站一致。
- **安全响应头**：CSP、`X-Frame-Options`、`nosniff` 等在 `poker/core/middleware.py` 中统一设置。新增外部资源（新的 CDN、图片域名）时，需要同步修改其中的 `CONTENT_SECURITY_POLICY`，否则会被浏览器拦截。
- **前端渲染**：把任何来自服务器的字符串放进 `innerHTML` 之前，都要用 `escapeHtml()`（`poker/static/js/common/escape.js`）转义。
- **错误信息**：服务层在 `except` 中使用 `safe_error(e)`，完整异常写入日志，前端只收到通用错误码。
- **输入校验**：昵称、别名、牌局名、备注、组名、公告的长度和字符规则集中在 `poker/core/validators.py`。

## 日志

日志以 JSON 格式逐行输出到标准输出，Render 会自动收集，可以在服务页面的 **Logs** 中查看和搜索。每个请求都有一条 `request` 日志（方法、路径、状态码、耗时、用户 ID）和一个 `X-Request-ID` 响应头，排查问题时可以用它把日志串起来。用 `LOG_LEVEL` 调整日志级别。

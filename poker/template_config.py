from utils.time import now_columbus_naive

from fastapi.templating import Jinja2Templates

from poker.core import settings


templates = Jinja2Templates(
    directory="poker/templates"
)

templates.env.globals["static_version"] = now_columbus_naive().strftime(
    "%Y%m%d%H%M%S"
)

# 登录页的返回按钮：线上指向主域名首页，测试环境留在本站
templates.env.globals["root_url"] = settings.root_url

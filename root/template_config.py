from fastapi.templating import Jinja2Templates

from core.time import now_columbus_naive


templates = Jinja2Templates(
    directory="root/templates"
)

templates.env.globals["static_version"] = now_columbus_naive().strftime(
    "%Y%m%d%H%M%S"
)

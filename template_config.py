from datetime import datetime
from utils.time import now_columbus_naive

from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(
    directory="templates"
)

templates.env.globals["static_version"] = now_columbus_naive().strftime(
    "%Y%m%d%H%M%S"
)
from datetime import datetime

from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(
    directory="templates"
)

templates.env.globals["static_version"] = datetime.utcnow().strftime(
    "%Y%m%d%H%M%S"
)
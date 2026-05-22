from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import RedirectResponse

from services.common import get_current_user_service


router = APIRouter()


@router.get("/current-user")
def current_user(request: Request):
    return get_current_user_service(request)


@router.get("/logout")
def logout(request: Request):

    request.session.clear()

    response = RedirectResponse(
        url="/login",
        status_code=302
    )

    response.headers["Cache-Control"] = \
        "no-store, no-cache, must-revalidate, max-age=0"

    response.headers["Pragma"] = "no-cache"

    response.headers["Expires"] = "0"

    return response
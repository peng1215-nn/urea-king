from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import RedirectResponse
from services.common.common import add_no_cache_headers
from services.common.common import get_current_user_service


router = APIRouter()


@router.get("/current-user")
def current_user(request: Request):
    return get_current_user_service(request)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()

    response = RedirectResponse(
        url="/login",
        status_code=302,
    )

    return add_no_cache_headers(response)
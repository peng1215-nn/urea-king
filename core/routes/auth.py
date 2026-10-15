"""Platform auth API routes — JSON/REST, no session, no templates."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from core.services.auth import (
    register_service,
    login_service,
    verify_token_service,
    get_user_service,
)

router = APIRouter(prefix="/platform", tags=["platform"])


class RegisterRequest(BaseModel):
    username: str
    nickname: str
    password: str
    confirm_password: str


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/auth/register")
def platform_register(body: RegisterRequest):
    result = register_service(
        username=body.username,
        nickname=body.nickname,
        password=body.password,
        confirm_password=body.confirm_password,
    )
    status = 201 if result.get("success") else 400
    return JSONResponse(content=result, status_code=status)


@router.post("/auth/token")
def platform_login(body: LoginRequest):
    result = login_service(username=body.username, password=body.password)
    status = 200 if result.get("success") else 401
    return JSONResponse(content=result, status_code=status)


@router.get("/auth/verify")
def platform_verify(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse(
            content={"success": False, "error_code": "tokenMissing"},
            status_code=401,
        )
    token = auth_header[7:]
    result = verify_token_service(token)
    status = 200 if result.get("success") else 401
    return JSONResponse(content=result, status_code=status)


@router.get("/users/{user_id}")
def platform_get_user(user_id: int):
    result = get_user_service(user_id)
    status = 200 if result.get("success") else 404
    return JSONResponse(content=result, status_code=status)

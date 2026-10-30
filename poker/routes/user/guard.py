"""普通用户接口的登录/角色检查。"""

from fastapi import Request
from fastapi.responses import JSONResponse


def user_api_denied(request: Request):
    """
    /user/* 的 JSON 接口统一用这个检查，通过时返回 None。
    - 没有登录（会话过期）：返回 401 sessionExpired，前端 current_user.js 会统一跳回登录页；
    - 登录了但当前不是普通成员身份：和以前一样返回 permissionDenied。
    """
    if not request.session.get("user_id"):
        return JSONResponse({"success": False, "message": "sessionExpired"}, status_code=401)
    if request.session.get("current_role") != "user":
        return {"success": False, "message": "permissionDenied"}
    return None

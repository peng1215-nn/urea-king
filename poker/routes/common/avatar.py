from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import JSONResponse

from poker.core.rate_limit import avatar_uploads_by_user
from poker.services.common.avatar import MAX_AVATAR_BYTES, upload_avatar_service


router = APIRouter()


@router.post("/upload-avatar")
async def upload_avatar(
    request: Request,
    avatar: UploadFile = File(...),
):
    user_id = request.session.get("user_id")

    if not user_id:
        return {"success": False, "message": "notLoggedIn"}

    wait = avatar_uploads_by_user.retry_after(str(user_id))
    if wait:
        return JSONResponse(
            {"success": False, "message": "tooManyUploads", "retry_after": wait},
            status_code=429,
        )

    # 多读 1 字节，用来判断是否超过上限，而不必读完整个大文件
    data = await avatar.read(MAX_AVATAR_BYTES + 1)

    result = upload_avatar_service(user_id, data)
    if result.get("success"):
        avatar_uploads_by_user.hit(str(user_id))
    return result

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

    # 先占名额，上传失败时退回
    wait, stamp = avatar_uploads_by_user.try_hit(str(user_id))
    if wait:
        return JSONResponse(
            {"success": False, "message": "tooManyUploads", "retry_after": wait},
            status_code=429,
        )

    # 多读 1 字节，用来判断是否超过上限，而不必读完整个大文件
    data = await avatar.read(MAX_AVATAR_BYTES + 1)

    result = upload_avatar_service(user_id, data)
    # 只有在上传到图床之前就被拒绝的（文件太大、格式不对）才退回名额；
    # 已经发给图床的，无论成功失败都计数，防止借失败的上传无限消耗图床额度
    if result.get("message") in ("avatarTooLarge", "avatarInvalidType", "userNotFound"):
        avatar_uploads_by_user.undo(str(user_id), stamp)
    return result

from fastapi import APIRouter, File, Request, UploadFile

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

    # 多读 1 字节，用来判断是否超过上限，而不必读完整个大文件
    data = await avatar.read(MAX_AVATAR_BYTES + 1)

    return upload_avatar_service(user_id, data)

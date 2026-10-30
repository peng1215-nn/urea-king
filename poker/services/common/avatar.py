"""
头像：校验、上传到 Cloudinary、注销时删除。
"""

import io
import logging
import os

import cloudinary
import cloudinary.uploader

from database import SessionLocal
from poker.models import User
from core import settings
from core.errors import safe_error


# 测试环境用另一个文件夹（环境变量 AVATAR_FOLDER），避免覆盖线上用户的头像。
# 两边的用户编号会重叠，测试环境忘了设置时也不能落到线上的文件夹里，所以默认值按环境区分。
AVATAR_FOLDER = os.getenv("AVATAR_FOLDER", "").strip() or (
    "urea_king_avatars_staging" if settings.IS_STAGING else "urea_king_avatars"
)

# 前端会先把图片压缩到 512px 以内；这里的上限只是兜底
MAX_AVATAR_BYTES = 10 * 1024 * 1024


def detect_image_type(data):
    """按文件头判断真实格式，不信任客户端声明的类型和扩展名。"""
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)


def upload_avatar_service(user_id, data):
    """校验图片、上传到 Cloudinary，并保存头像地址。"""
    if len(data) > MAX_AVATAR_BYTES:
        return {"success": False, "message": "avatarTooLarge"}

    if detect_image_type(data) is None:
        return {"success": False, "message": "avatarInvalidType"}

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return {"success": False, "message": "userNotFound"}

        upload_result = cloudinary.uploader.upload(
            io.BytesIO(data),
            folder=AVATAR_FOLDER,
            public_id=f"user_{user_id}",
            overwrite=True,
            invalidate=True,
        )

        avatar_url = upload_result["secure_url"]
        user.avatar_url = avatar_url
        db.commit()

        return {"success": True, "avatar_url": avatar_url}

    except Exception as e:
        db.rollback()
        return {"success": False, "message": safe_error(e)}

    finally:
        db.close()


def delete_avatar_for_user(user_id):
    """注销时删除 Cloudinary 上的头像。失败只记日志，不影响注销本身。"""
    try:
        cloudinary.uploader.destroy(
            f"{AVATAR_FOLDER}/user_{user_id}",
            invalidate=True,
        )
    except Exception:
        logging.getLogger("poker.avatar").exception(
            "failed to delete avatar", extra={"user_id": user_id}
        )

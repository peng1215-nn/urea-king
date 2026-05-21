import os

import cloudinary
import cloudinary.uploader

from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import File
from fastapi import Request

from database import SessionLocal

from models import User


router = APIRouter()


cloudinary.config(
    cloud_name=os.getenv(
        "CLOUDINARY_CLOUD_NAME"
    ),

    api_key=os.getenv(
        "CLOUDINARY_API_KEY"
    ),

    api_secret=os.getenv(
        "CLOUDINARY_API_SECRET"
    )
)


@router.post("/upload-avatar")
async def upload_avatar(

    request: Request,

    avatar: UploadFile = File(...)
):

    user_id = request.session.get(
        "user_id"
    )

    if not user_id:

        return {
            "success": False,
            "message": "未登录。"
        }

    try:

        upload_result = (
            cloudinary.uploader.upload(
                avatar.file,
                folder="urea_king_avatars"
            )
        )

        avatar_url = upload_result[
            "secure_url"
        ]

        db = SessionLocal()

        user = db.query(User).filter(
            User.id == user_id
        ).first()

        if not user:

            db.close()

            return {
                "success": False,
                "message": "用户不存在。"
            }

        user.avatar_url = avatar_url

        db.commit()

        db.close()

        return {
            "success": True,
            "avatar_url": avatar_url
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }
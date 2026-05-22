function validateAvatarFile(file) {
    const allowedTypes = [
        "image/jpeg",
        "image/png",
        "image/webp"
    ];

    if (!allowedTypes.includes(file.type)) {
        alert("请上传 JPG、PNG 或 WebP 格式头像。苹果手机请不要直接上传 HEIC 图片。");
        return false;
    }

    return true;
}
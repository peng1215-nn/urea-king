const AVATAR_MAX_EDGE = 512;

function loadImageFromFile(file) {
    return new Promise((resolve, reject) => {
        const url = URL.createObjectURL(file);
        const img = new Image();
        img.onload = () => { URL.revokeObjectURL(url); resolve(img); };
        img.onerror = () => { URL.revokeObjectURL(url); reject(new Error("decode failed")); };
        img.src = url;
    });
}

// 手机照片通常有 3–6 MB；上传前缩到 512px 以内并转成 JPEG，失败时原样上传
async function shrinkAvatar(file) {
    try {
        const img = await loadImageFromFile(file);
        const longest = Math.max(img.naturalWidth, img.naturalHeight);
        const scale = Math.min(1, AVATAR_MAX_EDGE / longest);

        if (scale === 1 && file.size <= 1024 * 1024) {
            return file;
        }

        const canvas = document.createElement("canvas");
        canvas.width = Math.max(1, Math.round(img.naturalWidth * scale));
        canvas.height = Math.max(1, Math.round(img.naturalHeight * scale));

        const ctx = canvas.getContext("2d");
        ctx.fillStyle = "#ffffff";  // 透明 PNG 转 JPEG 时避免变成黑底
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

        const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/jpeg", 0.88));
        return blob ? new File([blob], "avatar.jpg", { type: "image/jpeg" }) : file;
    } catch (error) {
        return file;
    }
}


async function uploadAvatar() {
    const fileInput = document.getElementById("avatar-input");
    const file = fileInput.files[0];

    if (!file) {
        return;
    }

    if (!validateAvatarFile(file)) {
        return;
    }

    const upload = await shrinkAvatar(file);

    const formData = new FormData();
    formData.append("avatar", upload);

    try {
        const response = await fetch("/upload-avatar", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (!data.success) {
            alert(typeof t === "function" ? t(data.message || "avatarUploadFailed") : "头像上传失败。");
            return;
        }

        const avatarPreview = document.getElementById("avatar-preview");
        avatarPreview.src = "/static/images/default_avatar.jpg";
        const newSrc = data.avatar_url + "?t=" + Date.now();
        const tempImg = new Image();
        tempImg.onload = () => { avatarPreview.src = newSrc; };
        tempImg.onerror = () => { /* 保持默认头像，CDN 还未传播 */ };
        tempImg.src = newSrc;

    } catch (error) {
        console.error(error);
        alert(typeof t === "function" ? t("avatarUploadFailed") : "头像上传失败。");
    }
}
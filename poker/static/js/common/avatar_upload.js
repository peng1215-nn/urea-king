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


// 页面的翻译文件里没有某个提示时（如局头页面还没加这几条），用这里的中英文兜底，不把键名显示给用户
const AVATAR_FALLBACK_TEXT = {
    zh: {
        avatarUploading: "上传中…",
        avatarUploadSuccess: "头像已更新",
        avatarUploadFailed: "头像上传失败。",
        avatarInvalidType: "只支持 JPG、PNG、WebP 格式的图片。",
        tooManyUploads: "上传过于频繁，请稍后再试。",
        retryAfterSeconds: "请 {s} 秒后再试。",
    },
    en: {
        avatarUploading: "Uploading…",
        avatarUploadSuccess: "Avatar updated",
        avatarUploadFailed: "Avatar upload failed.",
        avatarInvalidType: "Only JPG, PNG and WebP images are supported.",
        tooManyUploads: "Too many uploads. Please try again later.",
        retryAfterSeconds: "Please try again in {s} seconds.",
    },
};

function avatarText(key) {
    const translated = typeof t === "function" ? t(key) : key;
    if (translated && translated !== key) {
        return translated;
    }
    const lang = typeof getCurrentLanguage === "function" ? getCurrentLanguage() : "zh";
    const table = AVATAR_FALLBACK_TEXT[lang] || AVATAR_FALLBACK_TEXT.zh;
    return table[key] || translated;
}

// 上传期间：按钮显示“上传中…”，不能再选文件
function setAvatarUploading(uploading) {
    const fileInput = document.getElementById("avatar-input");
    const button = document.querySelector(".upload-avatar-button");
    if (fileInput) {
        fileInput.disabled = uploading;
    }
    if (button) {
        button.classList.toggle("is-busy", uploading);
        button.setAttribute("aria-busy", uploading ? "true" : "false");
        button.innerText = uploading ? avatarText("avatarUploading") : avatarText("uploadAvatar");
    }
}

function flashAvatarButton(message) {
    const button = document.querySelector(".upload-avatar-button");
    if (!button) return;
    button.innerText = message;
    setTimeout(() => {
        if (!button.classList.contains("is-busy")) {
            button.innerText = avatarText("uploadAvatar");
        }
    }, 2000);
}

function avatarErrorMessage(data) {
    const key = (data && data.message) || "avatarUploadFailed";
    let message = avatarText(key);
    if (key === "tooManyUploads" && data && data.retry_after) {
        message += " " + avatarText("retryAfterSeconds").replace("{s}", Math.ceil(Number(data.retry_after)));
    }
    return message;
}

let avatarUploadInProgress = false;

async function uploadAvatar() {
    const fileInput = document.getElementById("avatar-input");
    const file = fileInput.files[0];

    if (!file || avatarUploadInProgress) {
        return;
    }

    let succeeded = false;

    try {
        if (!validateAvatarFile(file)) {
            return;
        }

        avatarUploadInProgress = true;
        setAvatarUploading(true);

        const upload = await shrinkAvatar(file);

        const formData = new FormData();
        formData.append("avatar", upload);

        const response = await fetch("/upload-avatar", {
            method: "POST",
            body: formData,
        });

        const data = await response.json().catch(() => null);

        if (!data || !data.success) {
            alert(avatarErrorMessage(data));
            return;
        }

        // 新头像加载好之前保留旧头像（不先换成默认头像）
        const avatarPreview = document.getElementById("avatar-preview");
        const newSrc = data.avatar_url + "?t=" + Date.now();
        const tempImg = new Image();
        tempImg.onload = () => {
            if (avatarPreview) {
                avatarPreview.src = newSrc;
                avatarPreview.classList.add("loaded");
            }
        };
        tempImg.onerror = () => { /* 图床还没传播：先保留旧头像，下次打开页面会显示新的 */ };
        tempImg.src = newSrc;

        succeeded = true;

    } catch (error) {
        console.error(error);
        alert(avatarText("avatarUploadFailed"));
    } finally {
        avatarUploadInProgress = false;
        setAvatarUploading(false);
        if (succeeded) {
            flashAvatarButton(avatarText("avatarUploadSuccess"));
        }
        // 清空选择，下次选同一个文件也会触发 change
        fileInput.value = "";
    }
}

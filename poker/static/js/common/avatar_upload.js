async function uploadAvatar() {
    const fileInput = document.getElementById("avatar-input");
    const file = fileInput.files[0];

    if (!file) {
        return;
    }

    if (!validateAvatarFile(file)) {
        return;
    }

    const formData = new FormData();
    formData.append("avatar", file);

    try {
        const response = await fetch("/upload-avatar", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (!data.success) {
            alert(data.message || "头像上传失败。");
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
        alert("头像上传失败。");
    }
}
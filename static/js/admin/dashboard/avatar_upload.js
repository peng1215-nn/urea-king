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
            body: formData
        });

        const data = await response.json();

        if (!data.success) {
            alert(data.message || "头像上传失败。");
            return;
        }

        document.getElementById("avatar-preview").src =
            data.avatar_url;

    } catch (error) {
        console.error(error);
        alert("头像上传失败。");
    }
}
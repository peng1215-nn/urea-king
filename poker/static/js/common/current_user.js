async function loadCurrentUser() {
    try {
        const response =
            await fetch("/current-user");

        const data =
            await response.json();

        if (!data.success) {
            return;
        }

        const avatarPreview =
            document.getElementById(
                "avatar-preview"
            );

        if (avatarPreview) {
            const src = data.avatar_url
                ? data.avatar_url + "?t=" + Date.now()
                : "/static/images/default_avatar.jpg";

            avatarPreview.onerror = () => {
                avatarPreview.onerror = null;
                avatarPreview.src = "/static/images/default_avatar.jpg";
            };

            avatarPreview.src = src;
            avatarPreview.classList.add("loaded");
        }

        const currentGroupText =
            document.getElementById(
                "current-group-text"
            );

        if (currentGroupText) {
            currentGroupText.innerText =
                data.current_group_name ||
                "8th-Ecosystem";
        }

    } catch (error) {
        console.error(
            "加载当前用户失败：",
            error
        );
    }
}


window.addEventListener(
    "DOMContentLoaded",
    loadCurrentUser
);
async function loadCurrentUser() {
    const avatar = document.getElementById("avatar-preview");

    if (!avatar) {
        return;
    }

    const defaultAvatar = "/static/images/default_avatar.jpg";

    try {
        const response = await fetch("/current-user");
        const data = await response.json();

        if (data.success) {
            avatar.src = data.avatar_url || defaultAvatar;
        } else {
            avatar.src = defaultAvatar;
        }

        avatar.classList.add("loaded");

    } catch (error) {
        console.error("加载当前用户失败：", error);

        avatar.src = defaultAvatar;
        avatar.classList.add("loaded");
    }
}
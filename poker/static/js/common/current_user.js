// 会话失效（账号被禁用、被移出组或角色变更）时，后端返回 401 sessionExpired，
// 这里统一跳回登录页，避免页面停在一堆“操作失败”的状态。
(function hookSessionExpiry() {
    if (window.__sessionExpiryHooked || !window.fetch) {
        return;
    }

    window.__sessionExpiryHooked = true;

    const originalFetch = window.fetch.bind(window);

    window.fetch = async function (...args) {
        const response = await originalFetch(...args);

        if (response.status === 401) {
            const data = await response.clone().json().catch(() => null);

            if (data && data.message === "sessionExpired") {
                // 登录页根据 reason=expired 提示“登录已失效，请重新登录”
                window.location.href = "/login?reason=expired";
            }
        }

        return response;
    };
})();


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
                data.current_group_name || "";
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
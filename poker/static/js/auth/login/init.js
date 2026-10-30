window.addEventListener("pageshow", function (event) {
    resetMessage();
    showExpiredNotice();

    // 从后退缓存恢复时，按钮可能还停在“处理中”
    if (event.persisted) {
        loginSubmitting = false;
        authSetBusy(document.getElementById("login-button"), false);
    }
});


// 其他页面因登录过期跳回来时带 ?reason=expired
function showExpiredNotice() {
    const params = new URLSearchParams(window.location.search);

    if (params.get("reason") === "expired") {
        showNotice(t("loginExpiredNotice"));
    }
}


authBindSubmit("login-form", login);

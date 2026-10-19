async function loadCurrentAccount() {
    const data = await fetchCurrentAccount();
    if (data.success && data.user) {
        document.getElementById("current-nickname").value = data.user.nickname || data.user.username || "";
    }
}

window.addEventListener("pageshow", function (e) {
    if (e.persisted) {
        window.location.reload();
        return;
    }
    closeJoinGroupModal();
    applyLanguage();
    loadCurrentUser();
    loadCurrentAccount();
});
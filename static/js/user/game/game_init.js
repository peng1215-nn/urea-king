window.addEventListener("pageshow", function (e) {
    if (e.persisted) {
        window.location.reload();
        return;
    }
    closeJoinGroupModal();
    applyLanguage();
    loadCurrentUser();
    loadUserGames();
});
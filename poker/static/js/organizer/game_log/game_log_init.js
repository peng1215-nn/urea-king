window.addEventListener("pageshow", function () {
    closeJoinGroupModal();
    applyLanguage();
    loadCurrentUser();
    loadGameLogs(1);
});
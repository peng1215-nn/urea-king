window.addEventListener("pageshow", function () {
    closeJoinGroupModal();
    applyLanguage();
    loadCurrentUser();
    loadCurrentAccount();
});
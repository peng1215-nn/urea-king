window.addEventListener("pageshow", function () {
    closeJoinGroupModal();
    applyLanguage();
    loadCurrentUser();
    loadInviteCodes();
});
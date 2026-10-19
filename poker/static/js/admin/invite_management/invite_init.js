document.addEventListener(
    "DOMContentLoaded",
    async () => {

        applyLanguage();

        await loadGroupOptions();

        await loadUnusedInvitationOptions();
    }
);
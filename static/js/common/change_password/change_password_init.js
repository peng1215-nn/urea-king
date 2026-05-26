document.addEventListener(
    "DOMContentLoaded",
    async () => {
        applyLanguage();

        await loadCurrentAccount();
    }
);
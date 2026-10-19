document.addEventListener(
    "DOMContentLoaded",
    async () => {
        applyLanguage();

        await loadAnnouncements();
    }
);
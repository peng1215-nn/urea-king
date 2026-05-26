document.addEventListener(
    "DOMContentLoaded",
    async () => {
        applyLanguage();

        await loadAuditLogs();
    }
);
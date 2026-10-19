let pollingTimer = null;

function startPolling() {
    stopPolling();
    pollingTimer = setInterval(() => {
        if (!document.hidden) {
            loadUserGames(true);
        }
    }, 5000);
}

function stopPolling() {
    if (pollingTimer) {
        clearInterval(pollingTimer);
        pollingTimer = null;
    }
}

document.addEventListener("visibilitychange", function () {
    if (document.hidden) {
        stopPolling();
    } else {
        loadUserGames(true);
        startPolling();
    }
});

window.addEventListener("pageshow", function (e) {
    if (e.persisted) {
        window.location.reload();
        return;
    }
    closeJoinGroupModal();
    applyLanguage();
    loadCurrentUser();
    loadUserGames(false);
    startPolling();
});

window.addEventListener("pagehide", function () {
    stopPolling();
});
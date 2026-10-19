window.addEventListener("pageshow", function () {
    loadSystemMonitor();
    loadCurrentUser();
});

setInterval(loadSystemMonitor, 1000);
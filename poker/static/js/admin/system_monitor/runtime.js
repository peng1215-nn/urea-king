function formatRuntime(seconds) {
    const totalSeconds = Number(seconds || 0);

    const days = Math.floor(totalSeconds / 86400);
    const hours = Math.floor((totalSeconds % 86400) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;

    return `${days}${t("days")} ${hours}${t("hours")} ${minutes}${t("minutes")} ${secs}${t("seconds")}`;
}
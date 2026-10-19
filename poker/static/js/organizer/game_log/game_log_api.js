async function fetchGameLogs(page, q = "") {
    const params = new URLSearchParams({ page });
    if (q) params.set("q", q);
    const res = await fetch(`/organizer/game-log/list?${params}`);
    return await res.json();
}

async function fetchStats() {
    const res = await fetch("/organizer/game-log/stats");
    return await res.json();
}
async function fetchGameLogs(page) {
    const res = await fetch(`/user/game-log/list?page=${page}`);
    return await res.json();
}

async function fetchStats() {
    const res = await fetch("/user/game-log/stats");
    return await res.json();
}
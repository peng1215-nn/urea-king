async function fetchAdminGroupOptions() {
    const res = await fetch("/admin/groups/options");
    return await res.json();
}

async function fetchGameLogs(page, q = "") {
    const groupId = window.adminGameLogState.groupId;
    const params = new URLSearchParams({ group_id: groupId, page });
    if (q) params.set("q", q);
    const res = await fetch(`/admin/game-log/list?${params}`);
    return await res.json();
}

async function fetchStats() {
    const groupId = window.adminGameLogState.groupId;
    const res = await fetch(`/admin/game-log/stats?group_id=${groupId}`);
    return await res.json();
}

async function fetchMemberStats() {
    const groupId = window.adminGameLogState.groupId;
    const res = await fetch(`/admin/game-log/member-stats?group_id=${groupId}`);
    return await res.json();
}

async function fetchMemberTrend(userId) {
    const groupId = window.adminGameLogState.groupId;
    const res = await fetch(`/admin/game-log/member-trend?group_id=${groupId}&user_id=${userId}`);
    return await res.json();
}

async function deleteGameLog(gameId) {
    const groupId = window.adminGameLogState.groupId;
    const fd = new FormData();
    fd.append("game_id", gameId);
    fd.append("group_id", groupId);
    const res = await fetch("/admin/game-log/delete", { method: "POST", body: fd });
    return await res.json();
}

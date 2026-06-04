async function fetchOngoingGames() {
    const res = await fetch("/organizer/game/ongoing");
    return await res.json();
}

async function fetchGameHistory() {
    const res = await fetch("/organizer/game/history");
    return await res.json();
}

async function fetchGroupMembers() {
    const res = await fetch("/organizer/game/members");
    return await res.json();
}

async function apiRemovePlayer(gameId, userId) {
    const fd = new FormData();
    fd.append("game_id", gameId);
    fd.append("user_id", userId);
    const res = await fetch("/organizer/game/remove-player", { method: "POST", body: fd });
    return await res.json();
}

async function apiAddPlayer(gameId, userId) {
    const fd = new FormData();
    fd.append("game_id", gameId);
    fd.append("user_id", userId);
    const res = await fetch("/organizer/game/add-player", { method: "POST", body: fd });
    return await res.json();
}

async function apiApproveRequest(requestId, gameId) {
    const fd = new FormData();
    fd.append("request_id", requestId);
    fd.append("game_id", gameId);
    const res = await fetch("/organizer/game/approve-request", { method: "POST", body: fd });
    return await res.json();
}

async function apiRejectRequest(requestId, gameId) {
    const fd = new FormData();
    fd.append("request_id", requestId);
    fd.append("game_id", gameId);
    const res = await fetch("/organizer/game/reject-request", { method: "POST", body: fd });
    return await res.json();
}

async function apiStartGame(preselectedIds, name) {
    const res = await fetch("/organizer/game/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            name: name || "",
            preselected_user_ids: preselectedIds,
        }),
    });
    return await res.json();
}
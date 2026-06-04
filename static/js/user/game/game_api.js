async function fetchUserOngoingGames() {
    const res = await fetch("/user/game/ongoing");
    return await res.json();
}

async function apiSubmitBuyinRequest(gameId, amount) {
    const fd = new FormData();
    fd.append("game_id", gameId);
    fd.append("amount", amount);
    const res = await fetch("/user/game/buyin-request", { method: "POST", body: fd });
    return await res.json();
}
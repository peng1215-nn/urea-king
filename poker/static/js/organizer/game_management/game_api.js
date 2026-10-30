/*
 * 所有请求都经过 gameRequest：
 * - 网络断开、超时等异常不再抛出，返回 { success:false, message:"networkErrorCheck", networkError:true }，
 *   调用方据此提示“请刷新确认操作是否已记录”并恢复按钮；
 * - 返回的不是 JSON（如网关错误页）时同样当作结果不明处理；
 * - 401 会话失效由 current_user.js 统一跳转登录页，这里只保证不报错。
 */
async function gameRequest(url, options) {
    let res;
    try {
        res = await fetch(url, options);
    } catch (error) {
        return { success: false, message: "networkErrorCheck", networkError: true };
    }

    try {
        return await res.json();
    } catch (error) {
        if (res.status === 401) {
            return { success: false, message: "sessionExpired" };
        }
        return { success: false, message: "networkErrorCheck", networkError: true };
    }
}

function _postForm(url, fields) {
    const fd = new FormData();
    Object.entries(fields).forEach(([key, value]) => fd.append(key, value));
    return gameRequest(url, { method: "POST", body: fd });
}

function _postJson(url, body) {
    return gameRequest(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
}

async function fetchOngoingGames() {
    return gameRequest("/organizer/game/ongoing");
}

async function fetchGroupMembers() {
    return gameRequest("/organizer/game/members");
}

async function apiRemovePlayer(gameId, userId) {
    return _postForm("/organizer/game/remove-player", { game_id: gameId, user_id: userId });
}

async function apiExitPlayer(gameId, userId, cashOut) {
    return _postForm("/organizer/game/exit-player", { game_id: gameId, user_id: userId, cash_out: cashOut });
}

async function apiAddPlayer(gameId, userId) {
    return _postForm("/organizer/game/add-player", { game_id: gameId, user_id: userId });
}

async function apiApproveRequest(requestId, gameId) {
    return _postForm("/organizer/game/approve-request", { request_id: requestId, game_id: gameId });
}

async function apiRejectRequest(requestId, gameId) {
    return _postForm("/organizer/game/reject-request", { request_id: requestId, game_id: gameId });
}

async function apiOrganizerBuyin(gameId, amount, buyType) {
    return _postForm("/organizer/game/organizer-buyin", { game_id: gameId, amount: amount, buy_type: buyType });
}

async function apiProxyBuyin(gameId, targetUserId, amount) {
    return _postForm("/organizer/game/proxy-buyin", { game_id: gameId, target_user_id: targetUserId, amount: amount });
}

async function apiStartGame(preselectedIds, name) {
    return _postJson("/organizer/game/start", {
        name: name || "",
        preselected_user_ids: preselectedIds,
    });
}

async function apiFinishGame(body) {
    return _postJson("/organizer/game/finish", body);
}

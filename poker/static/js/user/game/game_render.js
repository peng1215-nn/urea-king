let currentBuyinGameId = null;

// 轮询之间的状态：用来发现“牌局结束了”“申请被处理了”
let lastGameNames = null;           // 上一次成功加载时的 { 牌局 id: 显示名 }；null 表示还没成功加载过
let lastRequestStatus = null;       // 上一次的 { 申请 id: 状态 }
const endedGames = [];              // 本页打开期间结束的牌局 [{ id, name }]
let lastSuccessAt = null;           // 上次成功更新的时间
let loadingGames = false;           // 避免上一次请求还没回来又发一次
let reloadQueued = false;           // 请求进行中又要求刷新时，等这次回来后再刷新一次

function formatClock(date) {
    const pad = n => String(n).padStart(2, "0");
    return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

function formatSigned(n) {
    const value = Number(n) || 0;
    return value > 0 ? "+" + value : String(value);
}

function setConnectionStatus(ok) {
    const line = document.getElementById("game-conn-status");
    if (!line) return;
    if (ok) {
        line.hidden = true;
        line.innerText = "";
        return;
    }
    const when = lastSuccessAt ? ` · ${t("lastUpdated")} ${formatClock(lastSuccessAt)}` : "";
    line.innerText = `${t("connectionLost")}${when}`;
    line.hidden = false;
}

async function loadUserGames(silent = false) {
    const list = document.getElementById("game-list");
    if (loadingGames) {
        reloadQueued = true;
        return;
    }
    loadingGames = true;

    if (!silent && lastGameNames === null) {
        list.innerHTML = `<div class="game-loading">${t("loading")}</div>`;
    }

    let data;
    try {
        data = await fetchUserOngoingGames();
    } catch (error) {
        data = null;
    } finally {
        loadingGames = false;
    }

    if (reloadQueued) {
        reloadQueued = false;
        setTimeout(() => loadUserGames(true), 0);
    }

    if (!data || !data.success) {
        if (lastGameNames === null) {
            // 第一次就没加载成功：不要一直停在“加载中...”
            const message = data && data.message ? t(data.message) : t("connectionLostFirst");
            list.innerHTML = `<div class="game-loading">${escapeHtml(message)}
                <button type="button" class="btn-retry" data-on-click="retryLoadUserGames">${t("retry")}</button></div>`;
        } else {
            setConnectionStatus(false);
        }
        return;
    }

    lastSuccessAt = new Date();
    setConnectionStatus(true);

    const games = data.games || [];
    detectEndedGames(games);
    notifyResolvedRequests(games);

    list.innerHTML = "";
    endedGames.forEach(g => renderEndedNotice(g, list));

    if (games.length === 0) {
        if (endedGames.length === 0) {
            renderEmptyState(list, data.group_ongoing_count || 0);
        }
        return;
    }

    games.forEach(game => renderGameCard(game, list));
}

function retryLoadUserGames() {
    loadUserGames(false);
}

function gameDisplayName(game) {
    return game.name || game.started_at || ("#" + game.id);
}

// 上一次还在、这一次不见了的牌局：已经结束（玩家记录不会被删除，只有结束的牌局会从这里消失）
function detectEndedGames(games) {
    const current = {};
    games.forEach(g => { current[g.id] = gameDisplayName(g); });

    if (lastGameNames !== null) {
        Object.keys(lastGameNames).forEach(id => {
            if (!(id in current) && !endedGames.some(g => String(g.id) === id)) {
                endedGames.unshift({ id: Number(id), name: lastGameNames[id] });
            }
        });
    }
    lastGameNames = current;
}

function notifyResolvedRequests(games) {
    const current = {};
    const changed = [];
    games.forEach(game => {
        (game.players || []).forEach(p => {
            if (!p.is_me) return;
            (p.requests || []).forEach(r => {
                current[r.id] = r.status;
                // 自己撤回的申请不再提示（撤回时已经有提示了，在另一台设备上撤回的也不必再提醒）
                if (lastRequestStatus && lastRequestStatus[r.id] === "pending"
                        && r.status !== "pending" && r.status !== "withdrawn") {
                    changed.push(r);
                }
            });
        });
    });
    lastRequestStatus = current;

    if (changed.length === 0) return;
    const messages = changed.map(r => {
        const key = r.status === "approved" ? "toastRequestApproved"
            : r.rejected_by === "auto" ? "toastRequestAutoRejected" : "toastRequestRejected";
        return t(key).replace("{amount}", r.amount);
    });
    const success = changed.every(r => r.status === "approved");
    showGameToast(messages.join("\n"), success);
}

let toastTimer = null;

function showGameToast(message, success) {
    const toast = document.getElementById("game-toast");
    if (!toast) return;
    toast.innerText = message;
    toast.classList.toggle("toast-success", !!success);
    toast.classList.toggle("toast-warning", !success);
    toast.hidden = false;
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toast.hidden = true; }, 6000);
}

function renderEmptyState(container, groupOngoingCount) {
    const groupLine = groupOngoingCount > 0
        ? t("groupHasOngoingGames").replace("{n}", groupOngoingCount)
        : t("groupNoOngoingGames");
    const box = document.createElement("div");
    box.className = "game-empty-state";
    box.innerHTML = `
        <div class="game-empty-icon"><i class="fa-solid fa-chess-board"></i></div>
        <div class="game-empty-title">${t("notInGameHint")}</div>
        <div class="game-empty-sub">${escapeHtml(groupLine)}</div>
    `;
    container.appendChild(box);
}

function renderEndedNotice(game, container) {
    const box = document.createElement("div");
    box.className = "game-ended-notice";
    box.innerHTML = `
        <div class="game-ended-text">
            <i class="fa-solid fa-flag-checkered"></i>
            <span>${t("gameEndedTitle")}</span>
            <span class="game-ended-name">${escapeHtml(game.name)}</span>
        </div>
        <div class="game-ended-links">
            <a class="game-ended-link primary" href="/game-report?game_id=${encodeURIComponent(game.id)}">${t("viewResult")} →</a>
            <a class="game-ended-link" href="/user-game-logs">${t("gameLogs")}</a>
        </div>
    `;
    container.appendChild(box);
}

function renderMyStatusBanner(game) {
    if (game.my_status === "exited") {
        const net = Number(game.my_net) || 0;
        const netClass = net > 0 ? "net-positive" : net < 0 ? "net-negative" : "";
        return `<div class="my-status-banner status-exited">
            <i class="fa-solid fa-right-from-bracket"></i>
            <span>${t("myStatusExited")} · ${t("cashOut")} ${escapeHtml(game.my_cash_out)} · ${t("net")} <b class="${netClass}">${formatSigned(net)}</b></span>
        </div>`;
    }
    if (game.my_status === "away") {
        return `<div class="my-status-banner status-away">
            <i class="fa-solid fa-mug-hot"></i>
            <span>${t("myStatusAway")}</span>
        </div>`;
    }
    return "";
}

function renderGameCard(game, container) {
    const card = document.createElement("div");
    card.className = "user-game-card" + (game.my_status && game.my_status !== "active" ? " is-left" : "");

    const canBuyIn = !game.my_status || game.my_status === "active";
    const playersHtml = game.players.map(p => renderPlayerRow(p, game.id, canBuyIn)).join("");

    card.innerHTML = `
        <div class="user-game-header">
            <div class="user-game-info">
                ${game.name ? `<span class="user-game-name">${escapeHtml(game.name)}</span>` : ""}
                <span class="user-game-time"><i class="fa-regular fa-clock"></i> ${escapeHtml(game.started_at)}</span>
            </div>
        </div>
        ${renderMyStatusBanner(game)}
        <div class="user-players-list">
            ${playersHtml}
        </div>
    `;

    container.appendChild(card);
}

function requestStatusLabel(r) {
    if (r.status === "approved") {
        return {
            cls: "req-approved",
            text: r.source === "proxy" ? t("requestProxyBuyin") : t("requestApproved"),
        };
    }
    if (r.status === "rejected") {
        return {
            cls: "req-rejected",
            text: r.rejected_by === "auto" ? t("requestAutoRejected") : t("requestRejected"),
        };
    }
    if (r.status === "withdrawn") {
        return { cls: "req-withdrawn", text: t("requestWithdrawn") };
    }
    return { cls: "req-pending", text: t("requestPending") };
}

function renderPlayerRow(p, gameId, canBuyIn) {
    const roleTag = p.is_organizer
        ? `<span class="player-role-tag organizer-tag">${t("organizer")}</span>`
        : "";
    const meTag = p.is_me
        ? `<span class="player-role-tag me-tag">${t("me")}</span>`
        : "";

    const avatarHtml = p.avatar_url
        ? `<img src="${escapeHtml(p.avatar_url)}" class="player-avatar" alt="">`
        : `<div class="player-avatar-placeholder"><i class="fa-solid fa-user"></i></div>`;

    // 申请买入按钮只对自己、且仍在桌上时显示；已有待审批的申请时显示为不可点的状态
    const pendingRequest = p.is_me ? (p.requests || []).find(r => r.status === "pending") : null;
    let buyinBtn = "";
    if (p.is_me && canBuyIn) {
        buyinBtn = pendingRequest
            ? `<div class="buyin-pending-wrap">
                   <span class="buyin-pending-state"><i class="fa-regular fa-hourglass-half"></i> ${t("buyinPendingState")}</span>
                   <button type="button" class="btn-withdraw-buyin" data-on-click="openWithdrawModal"
                       data-args="${escapeHtml(JSON.stringify([Number(pendingRequest.id), Number(pendingRequest.amount)]))}">
                       <i class="fa-solid fa-rotate-left"></i> ${t("withdrawRequest")}
                   </button>
               </div>`
            : `<button type="button" class="btn-submit-buyin" data-on-click="openBuyinModal" data-args="[${gameId}]">
                   <i class="fa-solid fa-plus"></i> ${t("submitBuyinRequest")}
               </button>`;
    }

    // 申请记录只对自己显示
    let requestsHtml = "";
    if (p.is_me && p.requests && p.requests.length > 0) {
        requestsHtml = `
            <div class="my-requests-title">${t("myBuyinRequests")}</div>
            <div class="my-requests-list">
                ${p.requests.map(r => {
                    const status = requestStatusLabel(r);
                    return `<div class="request-row">
                        <span class="req-amount">${escapeHtml(r.amount)}</span>
                        <span class="req-time">${escapeHtml(r.requested_at)}</span>
                        <span class="req-status ${status.cls}">${status.text}</span>
                    </div>`;
                }).join("")}
            </div>
        `;
    }

    return `
        <div class="user-player-row ${p.is_me ? "is-me" : ""} ${p.is_organizer ? "is-organizer" : ""}">
            <div class="player-row-top">
                <div class="player-left">
                    ${avatarHtml}
                    <div class="player-info">
                        <div class="player-name">${escapeHtml(p.nickname)} ${roleTag} ${meTag}</div>
                        <div class="player-buyin">${withColon(t("buyIn"))}${escapeHtml(p.total_buy_in)}</div>
                    </div>
                </div>
                <div class="player-right">
                    ${buyinBtn}
                </div>
            </div>
            ${requestsHtml}
        </div>
    `;
}

function setBuyinSubmitting(submitting) {
    const btn = document.getElementById("buyin-confirm-button");
    if (!btn) return;
    btn.disabled = submitting;
    btn.innerText = submitting ? t("submitting") : t("confirm");
}

function openBuyinModal(gameId) {
    currentBuyinGameId = gameId;
    setBuyinSubmitting(false);
    document.getElementById("buyin-amount").value = "";
    document.getElementById("buyin-message").innerText = "";
    document.getElementById("buyin-modal").style.display = "flex";
}

function closeBuyinModal() {
    document.getElementById("buyin-modal").style.display = "none";
    currentBuyinGameId = null;
    setBuyinSubmitting(false);
}

async function confirmBuyin() {
    const btn = document.getElementById("buyin-confirm-button");
    if (btn && btn.disabled) return;

    const messageBox = document.getElementById("buyin-message");
    messageBox.style.color = "#ff8a8a";
    messageBox.innerText = "";

    const amount = parseInt(document.getElementById("buyin-amount").value);
    if (!amount || amount <= 0) {
        messageBox.innerText = t("invalidAmount");
        return;
    }

    setBuyinSubmitting(true);
    let data;
    try {
        data = await apiSubmitBuyinRequest(currentBuyinGameId, amount);
    } catch (error) {
        data = { success: false, message: "connectionLostFirst" };
    }

    if (!data.success) {
        setBuyinSubmitting(false);
        messageBox.innerText = t(data.message || "operationFailed");
        return;
    }

    messageBox.style.color = "#5CFFB2";
    messageBox.innerText = t("buyinRequestSuccess");

    // 提交成功后按钮保持禁用，直到弹窗关闭，避免重复提交
    setTimeout(() => {
        closeBuyinModal();
        loadUserGames(true);
    }, 1200);
}

// ── 撤回待审批的申请 ──
// 用弹窗确认而不是在卡片里确认：卡片每 5 秒会随轮询重新渲染，弹窗不受影响

let withdrawRequestId = null;
let withdrawSubmitting = false;

function setWithdrawSubmitting(submitting) {
    withdrawSubmitting = submitting;
    const confirmBtn = document.getElementById("withdraw-confirm-button");
    const cancelBtn = document.getElementById("withdraw-cancel-button");
    if (confirmBtn) {
        confirmBtn.disabled = submitting;
        confirmBtn.innerText = submitting ? t("withdrawing") : t("confirmWithdraw");
    }
    if (cancelBtn) cancelBtn.disabled = submitting;
}

function openWithdrawModal(requestId, amount) {
    withdrawRequestId = requestId;
    setWithdrawSubmitting(false);
    document.getElementById("withdraw-desc").innerText = t("withdrawRequestDesc").replace("{amount}", amount);
    document.getElementById("withdraw-message").innerText = "";
    document.getElementById("withdraw-modal").style.display = "flex";
}

function closeWithdrawModal() {
    if (withdrawSubmitting) return;
    document.getElementById("withdraw-modal").style.display = "none";
    withdrawRequestId = null;
}

async function confirmWithdrawRequest() {
    if (withdrawSubmitting || withdrawRequestId === null) return;
    const messageBox = document.getElementById("withdraw-message");
    messageBox.innerText = "";

    setWithdrawSubmitting(true);
    let data;
    try {
        data = await apiWithdrawBuyinRequest(withdrawRequestId);
    } catch (error) {
        data = { success: false, message: "connectionLostFirst" };
    }

    if (!data.success && data.message === "connectionLostFirst") {
        // 网络问题：留在弹窗里，可以再试一次
        setWithdrawSubmitting(false);
        messageBox.innerText = t(data.message);
        return;
    }

    setWithdrawSubmitting(false);
    closeWithdrawModal();
    if (data.success) {
        showGameToast(t("withdrawRequestSuccess"), true);
    } else {
        // 例如局头刚好同时批准/拒绝了：以服务器的状态为准，刷新后就能看到结果
        showGameToast(t(data.message || "operationFailed"), false);
    }
    loadUserGames(true);
}

// 切换语言后，用最新的数据重新渲染（不用等下一次轮询）
document.addEventListener("languageChanged", function () {
    if (lastGameNames !== null) {
        loadUserGames(true);
    }
});

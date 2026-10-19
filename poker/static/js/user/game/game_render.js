let currentBuyinGameId = null;

async function loadUserGames(silent = false) {
    const list = document.getElementById("game-list");
    if (!silent) {
        list.innerHTML = `<div class="game-loading">${t("loading")}</div>`;
    }

    const data = await fetchUserOngoingGames();

    if (!data.success) {
        if (!silent) list.innerHTML = `<div class="game-loading">${t("operationFailed")}</div>`;
        return;
    }

    if (!data.games || data.games.length === 0) {
        list.innerHTML = `<div class="game-loading">${t("notInGame")}</div>`;
        return;
    }

    list.innerHTML = "";
    data.games.forEach(game => renderGameCard(game, list));
}

function renderGameCard(game, container) {
    const card = document.createElement("div");
    card.className = "user-game-card";

    const playersHtml = game.players.map(p => renderPlayerRow(p, game.id)).join("");

    card.innerHTML = `
        <div class="user-game-header">
            <div class="user-game-info">
                ${game.name ? `<span class="user-game-name">${game.name}</span>` : ""}
                <span class="user-game-time"><i class="fa-regular fa-clock"></i> ${game.started_at}</span>
            </div>
        </div>
        <div class="user-players-list">
            ${playersHtml}
        </div>
    `;

    container.appendChild(card);
}

function renderPlayerRow(p, gameId) {
    const roleTag = p.is_organizer
        ? `<span class="player-role-tag organizer-tag">${t("organizer")}</span>`
        : "";
    const meTag = p.is_me
        ? `<span class="player-role-tag me-tag">${t("me")}</span>`
        : "";

    const avatarHtml = p.avatar_url
        ? `<img src="${p.avatar_url}" class="player-avatar">`
        : `<div class="player-avatar-placeholder"><i class="fa-solid fa-user"></i></div>`;

    // 申请买入按钮只对自己显示
    const buyinBtn = p.is_me
        ? `<button class="btn-submit-buyin" onclick="openBuyinModal(${gameId})">
               <i class="fa-solid fa-plus"></i> ${t("submitBuyinRequest")}
           </button>`
        : "";

    // 申请记录只对自己显示
    let requestsHtml = "";
    if (p.is_me && p.requests && p.requests.length > 0) {
        requestsHtml = `
            <div class="my-requests-title">${t("myBuyinRequests")}</div>
            <div class="my-requests-list">
                ${p.requests.map(r => {
                    const statusClass = r.status === "approved" ? "req-approved"
                        : r.status === "rejected" ? "req-rejected" : "req-pending";
                    const statusText = r.status === "approved" ? t("requestApproved")
                        : r.status === "rejected" ? t("requestRejected") : t("requestPending");
                    return `<div class="request-row">
                        <span class="req-amount">${r.amount}</span>
                        <span class="req-time">${r.requested_at}</span>
                        <span class="req-status ${statusClass}">${statusText}</span>
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
                        <div class="player-name">${p.nickname} ${roleTag} ${meTag}</div>
                        <div class="player-buyin">${t("buyIn")}：${p.total_buy_in}</div>
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

function openBuyinModal(gameId) {
    currentBuyinGameId = gameId;
    document.getElementById("buyin-amount").value = "";
    document.getElementById("buyin-message").innerText = "";
    document.getElementById("buyin-modal").style.display = "flex";
}

function closeBuyinModal() {
    document.getElementById("buyin-modal").style.display = "none";
    currentBuyinGameId = null;
}

async function confirmBuyin() {
    const messageBox = document.getElementById("buyin-message");
    messageBox.style.color = "#ff8a8a";
    messageBox.innerText = "";

    const amount = parseInt(document.getElementById("buyin-amount").value);
    if (!amount || amount <= 0) {
        messageBox.innerText = t("invalidAmount");
        return;
    }

    const data = await apiSubmitBuyinRequest(currentBuyinGameId, amount);

    if (!data.success) {
        messageBox.innerText = t(data.message || "operationFailed");
        return;
    }

    messageBox.style.color = "#5CFFB2";
    messageBox.innerText = t("buyinRequestSuccess");

    setTimeout(() => {
        closeBuyinModal();
        loadUserGames();
    }, 1200);
}
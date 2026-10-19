async function loadGamePage() {
    const data = await fetchOngoingGames();
    if (!data.success) return;

    currentGames = data.games || [];

    if (currentGames.length === 0) {
        showNoGameSection();
        return;
    }

    // 保持当前 tab 索引有效
    if (currentGameIndex >= currentGames.length) {
        currentGameIndex = 0;
    }

    showOngoingGameSection();
    renderGameTabs();
    selectGameTab(currentGameIndex);
}

function showNoGameSection() {
    document.getElementById("no-game-section").style.display = "block";
    document.getElementById("ongoing-game-section").style.display = "none";
}

function showOngoingGameSection() {
    document.getElementById("no-game-section").style.display = "none";
    document.getElementById("ongoing-game-section").style.display = "block";
}

function renderGameTabs() {
    const tabContainer = document.getElementById("game-tabs");
    tabContainer.innerHTML = "";

    currentGames.forEach((game, index) => {
        const tab = document.createElement("button");
        tab.className = "game-tab" + (index === currentGameIndex ? " active" : "");
        tab.innerText = game.name || `#${index + 1}`;
        tab.onclick = () => selectGameTab(index);
        tabContainer.appendChild(tab);
    });
}

function selectGameTab(index) {
    currentGameIndex = index;
    const game = currentGames[index];

    currentGame = game;
    currentPlayers = game.players || [];
    currentRequests = game.requests || [];

    // 更新 tab 高亮
    document.querySelectorAll(".game-tab").forEach((tab, i) => {
        tab.classList.toggle("active", i === index);
    });

    renderGameStatus();
    renderPlayerList();
    renderRequestList();
}

function renderGameStatus() {
    document.getElementById("game-started-at").innerText = currentGame.started_at || "--";
    const activeCount = currentPlayers.filter(p => p.is_active === 1).length;
    document.getElementById("game-player-count").innerText = activeCount;
}

function renderPlayerList() {
    const container = document.getElementById("player-list");
    container.innerHTML = "";

    if (currentPlayers.length === 0) {
        container.innerHTML = `<div class="request-empty">${t("noPlayersYet")}</div>`;
        return;
    }

    const organizerId = currentGame.organizer_id;

    currentPlayers.forEach(player => {
        const isActive = player.is_active === 1;
        const isOrganizer = player.user_id === organizerId;
        const avatarUrl = player.avatar_url || "/static/images/default_avatar.jpg";
        const name = player.nickname || player.username;

        const card = document.createElement("div");
        card.className = "player-card" + (isActive ? "" : " inactive");

        let statsHtml = "";
        if (isOrganizer) {
            const normal = player.buy_in_normal || 0;
            const insurance = player.buy_in_insurance || 0;
            const anti = player.buy_in_anti || 0;
            statsHtml = `
                <div class="player-stat-row">
                    <span class="player-stat-item organizer-stat-col">${t("buyInNormal")}：${normal}</span>
                    <span class="player-stat-item organizer-stat-col">${t("buyInInsurance")}：${insurance}</span>
                </div>
                <div class="player-stat-row">
                    <span class="player-stat-item organizer-stat-col">${t("buyInAnti")}：${anti}</span>
                    <span class="player-stat-item organizer-stat-col">${t("buyInTotal")}：${player.total_buy_in}</span>
                </div>
            `;
        } else {
            statsHtml = `<div class="player-stat-row"><span class="player-stat-item">${t("buyIn")}：${player.total_buy_in}</span></div>`;
        }

        let actionsHtml = "";
        if (isActive) {
            if (isOrganizer) {
                actionsHtml = `
                    <div class="player-action-row">
                        <button class="btn-small btn-buyin" onclick="openOrganizerBuyinModal(${player.user_id})">${t("buyInChips")}</button>
                    </div>
                    <div class="player-action-row">
                        <button class="btn-small btn-remove" onclick="removePlayer(${player.user_id})">${t("removeFromGame")}</button>
                    </div>
                `;
            } else {
                actionsHtml = `
                    <div class="player-action-row">
                        <button class="btn-small btn-remove" onclick="removePlayer(${player.user_id})">${t("removeFromGame")}</button>
                    </div>
                `;
            }
        } else {
            actionsHtml = `
                <div class="player-action-row">
                    <button class="btn-small btn-rejoin" onclick="rejoinPlayer(${player.user_id})">${t("rejoin")}</button>
                </div>
            `;
        }

        card.innerHTML = `
            <img class="player-avatar" src="${avatarUrl}" alt="头像">
            <div class="player-info">
                <div class="player-name">${name}${isOrganizer ? ` <span class="organizer-tag">${t("organizer")}</span>` : ""}</div>
                <div class="player-stats">${statsHtml}</div>
            </div>
            <div class="player-right">
                <span class="player-status-badge ${isActive ? "active" : "inactive"}">
                    ${isActive ? t("inGame") : t("leftGame")}
                </span>
                <div class="player-actions">${actionsHtml}</div>
            </div>
        `;

        container.appendChild(card);
    });
}

function renderRequestList() {
    const container = document.getElementById("request-list");
    container.innerHTML = "";

    const pending = currentRequests.filter(r => r.status === "pending");

    if (pending.length === 0) {
        container.innerHTML = `<div class="request-empty">${t("noPendingRequests")}</div>`;
        return;
    }

    pending.forEach(req => {
        const card = document.createElement("div");
        card.className = "request-card";
        card.innerHTML = `
            <div class="request-card-header">
                <span class="request-user">${req.nickname || req.username}</span>
                <span class="request-time">${req.requested_at}</span>
            </div>
            <div class="request-amount">${req.amount} ${t("chips")}</div>
            <div class="request-actions">
                <button class="btn-approve" onclick="approveRequest(${req.id})">${t("approve")}</button>
                <button class="btn-reject" onclick="rejectRequest(${req.id})">${t("reject")}</button>
            </div>
        `;
        container.appendChild(card);
    });
}
// ── 声音提示 ──────────────────────────────────────────────
let _knownRequestIds = new Set();
let _audioCtx = null;

function _getAudioCtx() {
    if (!_audioCtx || _audioCtx.state === "closed") {
        _audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    return _audioCtx;
}

function playChipRequestSound() {
    try {
        const ctx = _getAudioCtx();
        const osc  = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.type = "sine";
        osc.frequency.value = 660;
        gain.gain.setValueAtTime(0, ctx.currentTime);
        gain.gain.linearRampToValueAtTime(0.2, ctx.currentTime + 0.01);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
        osc.start(ctx.currentTime);
        osc.stop(ctx.currentTime + 0.5);
    } catch (e) {
        // 浏览器未授权音频，静默忽略
    }
}

function _checkNewRequests(games) {
    let hasNew = false;
    games.forEach(game => {
        (game.requests || []).forEach(req => {
            if (req.status === "pending" && !_knownRequestIds.has(req.id)) {
                hasNew = true;
            }
            _knownRequestIds.add(req.id);
        });
    });
    if (hasNew) playChipRequestSound();
}
// ─────────────────────────────────────────────────────────

async function loadGamePage() {
    const data = await fetchOngoingGames();
    if (!data.success) return;

    currentGames = data.games || [];
    _checkNewRequests(currentGames);

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
        const hasPending = (game.requests || []).some(r => r.status === "pending");
        const tab = document.createElement("button");
        tab.className = "game-tab" + (index === currentGameIndex ? " active" : "");
        tab.innerHTML = `${game.name ? escapeHtml(game.name) : `#${index + 1}`}${hasPending ? ' <span class="tab-pending-dot">●</span>' : ""}`;
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
                        <button class="btn-small btn-buyin" data-on-click="openOrganizerBuyinModal" data-args="[${player.user_id}]">${t("buyInChips")}</button>
                    </div>
                    <div class="player-action-row">
                        <button class="btn-small btn-remove" data-on-click="removePlayer" data-args="[${player.user_id}]">${t("removeFromGame")}</button>
                    </div>
                `;
            } else {
                const proxyBtn = player.allow_organizer_chip_op
                    ? `<button class="btn-small btn-proxy-buyin" data-on-click="openProxyBuyinModal" data-args="[${player.user_id}]">${t("proxyBuyin")}</button>`
                    : "";
                actionsHtml = `
                    ${proxyBtn ? `<div class="player-action-row">${proxyBtn}</div>` : ""}
                    <div class="player-action-row">
                        <button class="btn-small btn-remove" data-on-click="removePlayer" data-args="[${player.user_id}]">${t("removeFromGame")}</button>
                    </div>
                `;
            }
        } else {
            actionsHtml = `
                <div class="player-action-row">
                    <button class="btn-small btn-rejoin" data-on-click="rejoinPlayer" data-args="[${player.user_id}]">${t("rejoin")}</button>
                </div>
            `;
        }

        card.innerHTML = `
            <img class="player-avatar" src="${escapeHtml(avatarUrl)}" alt="头像">
            <div class="player-info">
                <div class="player-name">${escapeHtml(name)}${isOrganizer ? ` <span class="organizer-tag">${t("organizer")}</span>` : ""}</div>
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
                <span class="request-user">${escapeHtml(req.nickname || req.username)}</span>
                <span class="request-time">${escapeHtml(req.requested_at)}</span>
            </div>
            <div class="request-amount">${escapeHtml(req.amount)} ${t("chips")}</div>
            <div class="request-actions">
                <button class="btn-approve" data-on-click="approveRequest" data-args="[${req.id}]">${t("approve")}</button>
                <button class="btn-reject" data-on-click="rejectRequest" data-args="[${req.id}]">${t("reject")}</button>
            </div>
        `;
        container.appendChild(card);
    });
}
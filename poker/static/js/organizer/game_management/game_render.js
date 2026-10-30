// ── 声音提示 ──────────────────────────────────────────────
// 浏览器要求音频必须在用户点过页面之后才能播放：第一次点击/触摸页面时创建（或恢复）AudioContext，
// 之后有新的买入申请才能响。页面刚打开时已有的申请只记下，不响。
let _knownRequestIds = new Set();
let _requestsInitialized = false;
let _audioCtx = null;

function _unlockAudio() {
    try {
        if (!_audioCtx || _audioCtx.state === "closed") {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (!AudioCtx) return;
            _audioCtx = new AudioCtx();
        }
        if (_audioCtx.state === "suspended") {
            _audioCtx.resume().catch(() => {});
        }
    } catch (e) {
        // 浏览器不支持或不允许音频，静默忽略
    }
}

["pointerdown", "touchstart", "keydown", "click"].forEach(type => {
    document.addEventListener(type, _unlockAudio, { capture: true, passive: true });
});

function playChipRequestSound() {
    try {
        const ctx = _audioCtx;
        if (!ctx || ctx.state === "closed") return;
        if (ctx.state === "suspended") ctx.resume().catch(() => {});
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
    if (!_requestsInitialized) {
        _requestsInitialized = true;
        return;
    }
    if (hasNew) playChipRequestSound();
}

// 标签页标题显示待审批数，如 "(3) UREAKING-POKER 牌局管理"
function _updatePendingTitle(games) {
    const count = games.reduce(
        (sum, game) => sum + (game.requests || []).filter(r => r.status === "pending" && !isRequestHandled(r.id)).length,
        0
    );
    const base = t("titleGameManagement");
    document.title = count > 0 ? `(${count}) ${base}` : base;
}
// ─────────────────────────────────────────────────────────

async function loadGamePage() {
    const data = await fetchOngoingGames();
    if (!data.success) return;

    currentGames = data.games || [];
    _checkNewRequests(currentGames);
    _updatePendingTitle(currentGames);

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
        const hasPending = (game.requests || []).some(r => r.status === "pending" && !isRequestHandled(r.id));
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
        const name = displayPlayerName(player);

        const card = document.createElement("div");
        card.className = "player-card" + (isActive ? "" : " inactive");

        // 不在桌上的玩家区分"暂离"（筹码还在手上，可回来）和"已结算离场"
        let statusClass = "active";
        let statusText = t("inGame");
        if (!isActive) {
            const exited = player.leave_type === "exit";
            statusClass = exited ? "inactive exited" : "inactive away";
            statusText = exited ? t("statusExited") : t("statusAway");
        }

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
        if (player.left_cash_out > 0) {
            statsHtml += `<div class="player-stat-row"><span class="player-stat-item">${t("leftCashOut")}：${player.left_cash_out}</span></div>`;
        }

        let actionsHtml = "";
        if (isActive) {
            if (isOrganizer) {
                actionsHtml = `
                    <div class="player-action-row">
                        <button class="btn-small btn-buyin" data-on-click="openOrganizerBuyinModal" data-args="[${player.user_id}]">${t("buyInChips")}</button>
                    </div>
                    <div class="player-action-row player-action-remove">
                        <button class="btn-small btn-remove" data-on-click="removePlayer" data-args="[${player.user_id}]">${t("removeFromGame")}</button>
                    </div>
                `;
            } else {
                const proxyBtn = player.allow_organizer_chip_op
                    ? `<button class="btn-small btn-proxy-buyin" data-on-click="openProxyBuyinModal" data-args="[${player.user_id}]">${t("proxyBuyin")}</button>`
                    : "";
                actionsHtml = `
                    ${proxyBtn ? `<div class="player-action-row">${proxyBtn}</div>` : ""}
                    <div class="player-action-row player-action-remove">
                        <button class="btn-small btn-remove" data-on-click="removePlayer" data-args="[${player.user_id}]">${t("removeFromGame")}</button>
                    </div>
                `;
            }
        } else {
            actionsHtml = `
                <div class="player-action-row">
                    <button class="btn-small btn-rejoin" data-on-click="rejoinPlayer" data-args="[${player.user_id}, &quot;$this&quot;]"${isActionBusy(`rejoin-${player.user_id}`) ? " disabled" : ""}>${t("rejoin")}</button>
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
                <span class="player-status-badge ${statusClass}">${statusText}</span>
                <div class="player-actions">${actionsHtml}</div>
            </div>
        `;

        container.appendChild(card);
    });
}

function renderRequestList() {
    const container = document.getElementById("request-list");
    container.innerHTML = "";

    const pending = currentRequests.filter(r => r.status === "pending" && !isRequestHandled(r.id));

    // 手机上把有待审批申请的面板排到玩家列表前面，并在标题旁显示数量
    const panel = document.getElementById("request-panel");
    if (panel) panel.classList.toggle("has-pending", pending.length > 0);
    const countBadge = document.getElementById("request-count");
    if (countBadge) {
        countBadge.innerText = pending.length > 0 ? String(pending.length) : "";
        countBadge.style.display = pending.length > 0 ? "inline-flex" : "none";
    }

    if (pending.length === 0) {
        container.innerHTML = `<div class="request-empty">${t("noPendingRequests")}</div>`;
        return;
    }

    pending.forEach(req => {
        const busy = isActionBusy(`request-${req.id}`) ? " disabled" : "";
        const card = document.createElement("div");
        card.className = "request-card";
        card.innerHTML = `
            <div class="request-card-header">
                <span class="request-user">${escapeHtml(displayPlayerName(req))}</span>
                <span class="request-time">${escapeHtml(req.requested_at)}</span>
            </div>
            <div class="request-amount">${escapeHtml(req.amount)} ${t("chips")}</div>
            <div class="request-actions">
                <button class="btn-approve" data-on-click="approveRequest" data-args="[${req.id}, &quot;$this&quot;]"${busy}>${t("approve")}</button>
                <button class="btn-reject" data-on-click="rejectRequest" data-args="[${req.id}, &quot;$this&quot;]"${busy}>${t("reject")}</button>
            </div>
        `;
        container.appendChild(card);
    });
}

// 切换语言后，脚本生成的玩家/申请列表跟着更新
document.addEventListener("languageChanged", function () {
    if (currentGames.length > 0) _updatePendingTitle(currentGames);
    if (currentGame) {
        renderPlayerList();
        renderRequestList();
    }
});

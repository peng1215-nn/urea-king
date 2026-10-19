let pendingDeleteGameId = null;
let currentPage = 1;
let currentView = "logs";

function openDeleteGameModal(gameId) {
    pendingDeleteGameId = gameId;
    document.getElementById("delete-game-modal").style.display = "flex";
}

function closeDeleteGameModal() {
    document.getElementById("delete-game-modal").style.display = "none";
    pendingDeleteGameId = null;
}

async function confirmDeleteGame() {
    if (!pendingDeleteGameId) return;
    const fd = new FormData();
    fd.append("game_id", pendingDeleteGameId);
    const res = await fetch("/organizer/game-log/delete", { method: "POST", body: fd });
    const data = await res.json();
    closeDeleteGameModal();
    if (data.success) loadGameLogs(currentPage);
}

function switchView(view) {
    currentView = view;
    document.getElementById("view-logs").style.display = view === "logs" ? "block" : "none";
    document.getElementById("view-stats").style.display = view === "stats" ? "block" : "none";
    document.getElementById("btn-logs").classList.toggle("active", view === "logs");
    document.getElementById("btn-stats").classList.toggle("active", view === "stats");
    if (view === "logs") loadGameLogs(currentPage);
    else loadStats();
}

async function loadGameLogs(page) {
    currentPage = page;
    const list = document.getElementById("game-log-list");
    list.innerHTML = `<div class="log-loading">${t("loading")}</div>`;
    const data = await fetchGameLogs(page);
    if (!data.success) { list.innerHTML = `<div class="log-loading">${t("operationFailed")}</div>`; return; }
    if (!data.games || data.games.length === 0) { list.innerHTML = `<div class="log-loading">${t("noGameLogs")}</div>`; renderPagination(1,1); return; }
    list.innerHTML = "";
    data.games.forEach(game => renderGameCard(game, list));
    renderPagination(data.page, data.total_pages);
}

function renderGameCard(game, container) {
    const card = document.createElement("div");
    card.className = "log-card";
    const balanced = game.is_balanced ? `<span class="badge-balanced">${t("balanced")}</span>` : `<span class="badge-unbalanced">${t("unbalanced")}</span>`;
    const title = game.name ? `<span class="log-game-name">${game.name}</span>` : "";
    card.innerHTML = `
        <div class="log-card-header" onclick="toggleDetail(this)">
            <div class="log-card-left">
                ${title}
                <span class="log-time">${game.started_at} → ${game.ended_at}</span>
                <span class="log-duration"><i class="fa-regular fa-clock"></i> ${game.duration}</span>
            </div>
            <div class="log-card-right">
                <span class="log-chips">${t("totalBuyIn")}：${game.total_buy_in}</span>
                ${balanced}
                <button class="btn-delete-log" onclick="event.stopPropagation(); openDeleteGameModal(${game.id})">${t("delete")}</button>
                <i class="fa-solid fa-chevron-down log-chevron"></i>
            </div>
        </div>
        <div class="log-card-detail" style="display:none;">${renderPlayers(game)}</div>
    `;
    container.appendChild(card);
}

function renderPlayers(game) {
    if (!game.players || game.players.length === 0) return "";
    let html = `<div class="log-players">`;
    game.players.forEach(p => {
        const isWinner = p.user_id === game.top_winner_id;
        const netClass = p.net > 0 ? "net-positive" : p.net < 0 ? "net-negative" : "net-zero";
        const winnerBadge = isWinner ? `<span class="winner-badge">🏆 ${t("topWinner")}</span>` : "";
        const organizerBadge = p.is_organizer ? `<span class="organizer-tag">${t("organizer")}</span>` : "";
        let buyinDetail = "";
        if (p.is_organizer) {
            buyinDetail = `<div class="log-player-buyin-detail">
                <span>${t("buyInNormal")}：${p.buy_in_normal||0}</span>
                <span>${t("buyInInsurance")}：${p.buy_in_insurance||0}</span>
                <span>${t("buyInAnti")}：${p.buy_in_anti||0}</span>
            </div>`;
        }
        let detailsHtml = "";
        if (p.buyin_details && p.buyin_details.length > 0) {
            detailsHtml = '<div class="buyin-details-list">' +
                p.buyin_details.map(function(d, i) {
                    const typeLabel = d.type === "insurance" ? t("buyInInsurance") : d.type === "anti" ? t("buyInAnti") : t("buyInNormal");
                    return '<div class="buyin-detail-row">' +
                        '<span class="detail-index">#' + (i+1) + '</span>' +
                        '<span class="detail-amount">' + d.amount + '</span>' +
                        '<span class="detail-type">' + typeLabel + '</span>' +
                        '<span class="detail-time">' + d.time + '</span>' +
                        '</div>';
                }).join("") +
            '</div>';
        }
        html += `<div class="log-player-row ${isWinner?"winner":""}">
            <div class="log-player-name">${p.nickname} ${organizerBadge} ${winnerBadge}</div>
            <div class="log-player-stats">
                <span>${t("buyIn")}：${p.total_buy_in}</span>
                <span>${t("cashOut")}：${p.cash_out}</span>
                <span class="${netClass}">${t("net")}：${p.net>0?"+":""}${p.net}</span>
            </div>
            ${buyinDetail}
            ${detailsHtml}
        </div>`;
    });
    html += `</div>`;
    return html;
}

function toggleDetail(header) {
    const detail = header.nextElementSibling;
    const chevron = header.querySelector(".log-chevron");
    const isOpen = detail.style.display !== "none";
    detail.style.display = isOpen ? "none" : "block";
    chevron.style.transform = isOpen ? "" : "rotate(180deg)";
}

function renderPagination(page, totalPages) {
    const container = document.getElementById("pagination");
    container.innerHTML = "";
    if (totalPages <= 1) return;
    const prev = document.createElement("button");
    prev.className = "page-btn" + (page <= 1 ? " disabled" : "");
    prev.innerText = "←";
    prev.onclick = () => { if (page > 1) loadGameLogs(page - 1); };
    container.appendChild(prev);
    for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement("button");
        btn.className = "page-btn" + (i === page ? " active" : "");
        btn.innerText = i;
        btn.onclick = () => loadGameLogs(i);
        container.appendChild(btn);
    }
    const next = document.createElement("button");
    next.className = "page-btn" + (page >= totalPages ? " disabled" : "");
    next.innerText = "→";
    next.onclick = () => { if (page < totalPages) loadGameLogs(page + 1); };
    container.appendChild(next);
}

async function loadStats() {
    const panel = document.getElementById("stats-panel");
    panel.innerHTML = `<div class="log-loading">${t("loading")}</div>`;
    const data = await fetchStats();
    if (!data.success || !data.stats) { panel.innerHTML = `<div class="log-loading">${t("noGameLogs")}</div>`; return; }
    const s = data.stats;
    const rows = [
        { color: "green",  icon: "fa-arrow-trend-up",   label: t("statMostWins"),   value: s.most_wins.names.length ? s.most_wins.names.join("、") : "-",   sub: s.most_wins.names.length ? s.most_wins.count + " " + t("times") : "" },
        { color: "red",    icon: "fa-arrow-trend-down",  label: t("statMostLoses"),  value: s.most_loses.names.length ? s.most_loses.names.join("、") : "-",  sub: s.most_loses.names.length ? s.most_loses.count + " " + t("times") : "" },
        { color: "yellow", icon: "fa-trophy",            label: t("statMostProfit"), value: s.most_profit.names.length ? s.most_profit.names.join("、") : "-", sub: s.most_profit.names.length ? "+" + s.most_profit.amount : "" },
        { color: "purple", icon: "fa-face-sad-tear",     label: t("statMostLoss"),   value: s.most_loss.names.length ? s.most_loss.names.join("、") : "-",   sub: s.most_loss.names.length ? (s.most_loss.amount < 0 ? "" : "-") + Math.abs(s.most_loss.amount) : "" },
        { color: "blue",   icon: "fa-users",             label: t("statMostGames"),  value: s.most_games.names.join("、"),  sub: s.most_games.count + " " + t("times") },
        { color: "cyan",   icon: "fa-clock",             label: t("statLongestGame"),value: s.longest_game.duration,        sub: s.longest_game.name },
        { color: "orange", icon: "fa-coins",             label: t("statMaxChips"),   value: s.max_chips.amount,             sub: s.max_chips.name },
        { color: "green",  icon: "fa-star",               label: t("statBestSingle"),  value: s.best_single.nickname || "-",   sub: s.best_single.nickname ? "+" + s.best_single.amount + (s.best_single.game ? " · " + s.best_single.game : "") : "" },
        { color: "red",    icon: "fa-skull",               label: t("statWorstSingle"), value: s.worst_single.nickname || "-",  sub: s.worst_single.nickname ? s.worst_single.amount + (s.worst_single.game ? " · " + s.worst_single.game : "") : "" },
    ];
    let playerRatesHtml = "";
    if (s.player_rates && s.player_rates.length > 0) {
        playerRatesHtml = `<div class="player-rates-section">
            <div class="player-rates-title">${t("statPlayerRates")}</div>
            <div class="player-rates-list">` +
            s.player_rates.map(p => `
                <div class="player-rate-row">
                    <div class="player-rate-name">${p.nickname}</div>
                    <div class="player-rate-stats">
                        <span class="rate-games">${t("participated")} ${p.game_count} ${t("games")}</span>
                        <span class="rate-win">${t("winRate")} ${p.win_rate}%（${p.win_count}次）</span>
                        <span class="rate-lose">${t("loseRate")} ${p.lose_rate}%（${p.lose_count}次）</span>

                    </div>
                </div>
            `).join("") +
            `</div></div>`;
    }

    panel.innerHTML = `<div class="stats-list">` +
        rows.map(r => `
            <div class="stats-row">
                <div class="stats-row-icon ${r.color}"><i class="fa-solid ${r.icon}"></i></div>
                <div class="stats-row-label">${r.label}</div>
                <div class="stats-row-value">${r.value}</div>
                <div class="stats-row-sub">${r.sub}</div>
            </div>
        `).join("") +
    `</div>` + playerRatesHtml;
}
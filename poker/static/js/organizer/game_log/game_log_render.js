let pendingDeleteGameId = null;
let currentPage = 1;
let currentView = "logs";
let currentSearch = "";

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
    document.getElementById("view-member-stats").style.display = view === "member-stats" ? "block" : "none";
    document.getElementById("btn-logs").classList.toggle("active", view === "logs");
    document.getElementById("btn-stats").classList.toggle("active", view === "stats");
    document.getElementById("btn-member-stats").classList.toggle("active", view === "member-stats");
    if (view === "logs") loadGameLogs(currentPage);
    else if (view === "stats") loadStats();
    else loadMemberStats();
}

function onSearch() {
    currentSearch = document.getElementById("log-search-input")?.value?.trim() || "";
    loadGameLogs(1);
}

async function loadGameLogs(page) {
    currentPage = page;
    const list = document.getElementById("game-log-list");
    list.innerHTML = `<div class="log-loading">${t("loading")}</div>`;
    const data = await fetchGameLogs(page, currentSearch);
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
    const noteHtml = game.note ? `<span class="log-game-note"><i class="fa-solid fa-note-sticky"></i> ${game.note}</span>` : "";
    card.innerHTML = `
        <div class="log-card-header" onclick="toggleDetail(this)">
            <div class="log-card-left">
                ${title}
                ${noteHtml}
                <span class="log-time">${game.started_at} → ${game.ended_at}</span>
                <span class="log-duration"><i class="fa-regular fa-clock"></i> ${game.duration}</span>
            </div>
            <div class="log-card-right">
                <span class="log-chips">${t("totalBuyIn")}：${game.total_buy_in}</span>
                ${balanced}
                <button class="btn-export-log" onclick="event.stopPropagation(); exportGameCard(${game.id})">${t("export")}</button>
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
    panel.innerHTML = `<div class="stats-list">` +
        rows.map(r => `
            <div class="stats-row">
                <div class="stats-row-icon ${r.color}"><i class="fa-solid ${r.icon}"></i></div>
                <div class="stats-row-label">${r.label}</div>
                <div class="stats-row-value">${r.value}</div>
                <div class="stats-row-sub">${r.sub}</div>
            </div>
        `).join("") +
    `</div>`;
}
let memberSortKey = "total_net";
let memberSortAsc = false;
let memberStatsData = [];

async function loadMemberStats() {
    const panel = document.getElementById("member-stats-panel");
    panel.innerHTML = `<div class="log-loading">${t("loading")}</div>`;
    let data;
    try {
        const resp = await fetch("/organizer/game-log/member-stats");
        data = await resp.json();
    } catch(e) {
        panel.innerHTML = `<div class="log-loading">${t("operationFailed")}</div>`;
        return;
    }
    if (!data.success) {
        panel.innerHTML = `<div class="log-loading">${t("operationFailed")}</div>`;
        return;
    }
    if (!data.members || data.members.length === 0) {
        panel.innerHTML = `<div class="log-loading">${t("noGameLogs")}</div>`;
        return;
    }
    memberStatsData = data.members;
    memberSortKey = "total_net";
    memberSortAsc = false;
    renderMemberStatsTable(memberStatsData, panel);
}

function sortMemberStats(key) {
    if (memberSortKey === key) {
        memberSortAsc = !memberSortAsc;
    } else {
        memberSortKey = key;
        memberSortAsc = false;
    }
    const panel = document.getElementById("member-stats-panel");
    renderMemberStatsTable(memberStatsData, panel);
}

function renderMemberStatsTable(members, container) {
    const sorted = [...members].sort((a, b) => {
        const v = memberSortAsc ? 1 : -1;
        return a[memberSortKey] > b[memberSortKey] ? v : a[memberSortKey] < b[memberSortKey] ? -v : 0;
    });

    const arrow = (key) => {
        if (memberSortKey !== key) return `<span class="sort-arrow">↕</span>`;
        return `<span class="sort-arrow active">${memberSortAsc ? "↑" : "↓"}</span>`;
    };

    let html = `
        <div class="member-stats-table-wrap">
            <table class="member-stats-table">
                <thead>
                    <tr>
                        <th>${t("memberRank")}</th>
                        <th>${t("memberNickname")}</th>
                        <th class="sortable" onclick="sortMemberStats('game_count')">${t("memberGames")} ${arrow("game_count")}</th>
                        <th class="sortable" onclick="sortMemberStats('win_rate')" style="color:#4caf7d">${t("memberWinRate")} ${arrow("win_rate")}</th>
                        <th class="sortable" onclick="sortMemberStats('lose_rate')" style="color:#e05c5c">${t("memberLoseRate")} ${arrow("lose_rate")}</th>
                        <th class="sortable" onclick="sortMemberStats('total_net')">${t("memberTotalNet")} ${arrow("total_net")}</th>
                    </tr>
                </thead>
                <tbody>
    `;
    sorted.forEach((m, i) => {
        const netClass = m.total_net > 0 ? "net-positive" : m.total_net < 0 ? "net-negative" : "net-zero";
        const netStr = m.total_net > 0 ? "+" + m.total_net : String(m.total_net);
        html += `
            <tr class="member-row" onclick="openMemberTrendModal(${m.user_id}, '${m.nickname.replace(/'/g, "\\'")}')">
                <td class="rank-cell">${i + 1}</td>
                <td class="name-cell">${m.nickname}</td>
                <td>${m.game_count}</td>
                <td style="color:#4caf7d">${m.win_rate}%（${m.win_count}${t("times")}）</td>
                <td style="color:#e05c5c">${m.lose_rate !== undefined ? m.lose_rate + "%（" + m.lose_count + t("times") + "）" : "-"}</td>
                <td class="${netClass} net-cell">${netStr}</td>
            </tr>
        `;
    });
    html += `</tbody></table></div>`;
    container.innerHTML = html;
}

let trendChart = null;

async function openMemberTrendModal(userId, nickname) {
    document.getElementById("trend-modal-title").innerText = nickname;
    document.getElementById("trend-summary").innerHTML = "";
    document.getElementById("member-trend-modal").style.display = "flex";

    if (trendChart) { trendChart.destroy(); trendChart = null; }
    const canvas = document.getElementById("trend-chart");
    canvas.style.display = "none";

    let data;
    try {
        const resp = await fetch(`/organizer/game-log/member-trend?user_id=${userId}`);
        data = await resp.json();
    } catch(e) {
        document.getElementById("trend-summary").innerText = t("operationFailed");
        return;
    }
    if (!data.success || !data.points || data.points.length === 0) {
        document.getElementById("trend-summary").innerText = t("noGameLogs");
        return;
    }
    renderTrendChart(data.points, canvas);
}

function closeMemberTrendModal() {
    document.getElementById("member-trend-modal").style.display = "none";
    if (trendChart) { trendChart.destroy(); trendChart = null; }
}

document.addEventListener("click", (e) => {
    if (e.target === document.getElementById("member-trend-modal")) closeMemberTrendModal();
});

function renderTrendChart(points, canvas) {
    canvas.style.display = "block";
    const labels = points.map(p => p.game_name || p.date);
    const netData = points.map(p => p.net);
    const cumulData = points.map(p => p.cumulative);

    trendChart = new Chart(canvas, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: t("memberTotalNet"),
                    data: cumulData,
                    borderColor: "#6c9ef8",
                    backgroundColor: "rgba(108,158,248,0.12)",
                    fill: true,
                    tension: 0.3,
                    pointRadius: 5,
                    pointHoverRadius: 8,
                    pointBackgroundColor: cumulData.map(v => v >= 0 ? "#4caf7d" : "#f44336"),
                    pointBorderColor: "#fff",
                    pointBorderWidth: 2,
                    yAxisID: "y",
                },
                {
                    label: t("netPerGame"),
                    data: netData,
                    borderColor: "rgba(255,215,64,0.8)",
                    backgroundColor: "transparent",
                    borderDash: [5, 4],
                    tension: 0.3,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: netData.map(v => v >= 0 ? "#4caf7d" : "#f44336"),
                    pointBorderColor: "#fff",
                    pointBorderWidth: 1,
                    yAxisID: "y",
                },
            ],
        },
        options: {
            responsive: true,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { labels: { color: "rgba(255,255,255,0.7)", font: { size: 12 } } },
                tooltip: {
                    backgroundColor: "rgba(20,20,35,0.95)",
                    titleColor: "#fff",
                    bodyColor: "rgba(255,255,255,0.8)",
                    callbacks: {
                        afterBody: (items) => {
                            const i = items[0].dataIndex;
                            const p = points[i];
                            return [`${t("buyIn")}：${p.buy_in}  ${t("cashOut")}：${p.cash_out}`, p.date];
                        }
                    }
                },
            },
            scales: {
                x: { ticks: { color: "rgba(255,255,255,0.55)", maxRotation: 40 }, grid: { color: "rgba(255,255,255,0.05)" } },
                y: {
                    ticks: { color: "rgba(255,255,255,0.55)" },
                    grid: { color: "rgba(255,255,255,0.07)" },
                    zero: true,
                },
            },
        },
    });

    const last = points[points.length - 1];
    const winCount = points.filter(p => p.net > 0).length;
    const winRate = Math.round(winCount / points.length * 100);
    const summaryEl = document.getElementById("trend-summary");
    const netClass = last.cumulative >= 0 ? "net-positive" : "net-negative";
    const netStr = last.cumulative > 0 ? "+" + last.cumulative : String(last.cumulative);
    summaryEl.innerHTML = `
        <span>${t("memberGames")}：${points.length}</span>
        <span>${t("memberWinRate")}：${winRate}%</span>
        <span class="${netClass}">${t("memberTotalNet")}：${netStr}</span>
    `;
}

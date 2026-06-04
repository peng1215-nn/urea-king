function openFinishGameModal() {
    if (!currentGame) return;

    const container = document.getElementById("finish-cashout-list");
    container.innerHTML = "";

    const organizerId = currentGame.organizer_id;

    currentPlayers.forEach(player => {
        const name = player.nickname || player.username;
        const isOrganizer = player.user_id === organizerId;

        const row = document.createElement("div");
        row.className = "finish-player-row";

        row.innerHTML = `
            <div class="finish-player-name">
                ${name}${isOrganizer ? ` <span class="organizer-tag">${t("organizer")}</span>` : ""}
            </div>
            <div class="finish-player-buyin">${t("buyIn")}：${player.total_buy_in}</div>
            <input
                type="number"
                class="finish-cashout-input"
                data-user-id="${player.user_id}"
                min="0"
                data-i18n-placeholder="cashOutPlaceholder"
                placeholder="${t("cashOutPlaceholder")}"
                value="${player.cash_out !== null && player.cash_out !== undefined ? player.cash_out : ''}"
            >
        `;

        container.appendChild(row);
    });

    document.getElementById("finish-message").innerText = "";
    document.getElementById("finish-confirm-btn").dataset.force = "false";
    document.getElementById("finish-confirm-btn").innerText = t("finishAndCheck");
    document.getElementById("finish-confirm-btn").className = "modal-confirm-button";

    document.getElementById("finish-game-modal").style.display = "flex";
}

function closeFinishGameModal() {
    document.getElementById("finish-game-modal").style.display = "none";
}

function closeSettlementModal() {
    document.getElementById("settlement-modal").style.display = "none";
}

function openSettlementModal(data) {
    const game = data.game;
    const players = data.players || [];

    document.getElementById("settle-total-buyin").innerText = game.total_buy_in ?? "--";
    document.getElementById("settle-total-cashout").innerText = game.total_cash_out ?? "--";

    const organizerId = game.organizer_id;
    const list = document.getElementById("settlement-player-list");
    list.innerHTML = "";

    players.forEach(player => {
        const name = player.nickname || player.username;
        const isOrganizer = player.user_id === organizerId;
        const buyIn = player.total_buy_in ?? 0;
        const cashOut = player.cash_out ?? 0;
        const net = player.net ?? (cashOut - buyIn);
        const netClass = net > 0 ? "net-positive" : net < 0 ? "net-negative" : "net-zero";

        const row = document.createElement("div");
        row.className = "settlement-row";

        row.innerHTML = `
            <div class="settlement-name">
                ${name}${isOrganizer ? ` <span class="organizer-tag">${t("organizer")}</span>` : ""}
            </div>
            <div class="settlement-cols">
                <span>${t("buyIn")}：${buyIn}</span>
                <span>${t("cashOut")}：${cashOut}</span>
                <span class="${netClass}">${t("net")}：${net > 0 ? "+" : ""}${net}</span>
            </div>
        `;

        list.appendChild(row);
    });

    document.getElementById("settlement-modal").style.display = "flex";
}

async function confirmFinishGame() {
    const messageBox = document.getElementById("finish-message");
    messageBox.style.color = "#ff8a8a";
    messageBox.innerText = "";

    const btn = document.getElementById("finish-confirm-btn");
    const force = btn.dataset.force === "true";

    const inputs = document.querySelectorAll(".finish-cashout-input");
    const playerCashOuts = [];

    for (const input of inputs) {
        const userId = parseInt(input.dataset.userId);
        const cashOut = parseInt(input.value);

        if (isNaN(cashOut) || cashOut < 0) {
            messageBox.innerText = t("invalidCashOut");
            return;
        }

        playerCashOuts.push({ user_id: userId, cash_out: cashOut });
    }

    const res = await fetch("/organizer/game/finish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            game_id: currentGame.id,
            player_cash_outs: playerCashOuts,
            organizer_insurance_final: 0,
            organizer_anti_final: 0,
            force: force,
        }),
    });

    const data = await res.json();

    if (!data.success) {
        if (data.message === "balanceCheckFailed") {
            const diff = data.diff || 0;
            messageBox.innerText = `${t("balanceCheckFailed")} ${diff}`;
            btn.dataset.force = "true";
            btn.innerText = t("forceFinish");
            btn.className = "modal-confirm-button warning";
        } else {
            messageBox.innerText = t(data.message || "operationFailed");
        }
        return;
    }

    closeFinishGameModal();
    openSettlementModal(data);
    await loadGamePage();
}
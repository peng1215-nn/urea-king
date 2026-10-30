// 结束牌局弹窗：局头只填每人手上剩余的筹码，下方实时汇总，尽量不用自己算账。
// 每人总卖出 = 中途结算离场已卖出 + 现在剩余；差额 = 总卖出 − 总买入（正数表示筹码多了）。

function _finishPlayerById(userId) {
    return currentPlayers.find(p => p.user_id === userId) || null;
}

function _readChips(input) {
    const raw = input.value.trim();
    return /^\d+$/.test(raw) ? parseInt(raw, 10) : NaN;
}

function openFinishGameModal() {
    if (!currentGame) return;

    const container = document.getElementById("finish-cashout-list");
    container.innerHTML = "";

    const organizerId = currentGame.organizer_id;

    currentPlayers.forEach(player => {
        const name = displayPlayerName(player);
        const isOrganizer = player.user_id === organizerId;
        const isActive = player.is_active === 1;
        const buyIn = player.total_buy_in || 0;
        const leftCashOut = player.left_cash_out || 0;
        const exited = !isActive && (player.leave_type === "exit" || (!player.leave_type && leftCashOut > 0));
        const away = !isActive && !exited;

        // 已经结算离场、没再回来的玩家，手上已经没有筹码；一直没买入的人也没有筹码：默认填 0
        const prefill = exited || buyIn === 0 ? "0" : "";

        let hints = "";
        if (leftCashOut > 0) {
            hints += `<div class="finish-player-left">${escapeHtml(t("leftCashOutAuto").replace("{amount}", leftCashOut))}</div>`;
        }
        if (away) {
            hints += `<div class="finish-player-away">${escapeHtml(t("awayChipsHint"))}</div>`;
        }

        const row = document.createElement("div");
        row.className = "finish-player-row";

        row.innerHTML = `
            <div class="finish-player-name">
                ${escapeHtml(name)}${isOrganizer ? ` <span class="organizer-tag">${t("organizer")}</span>` : ""}
                ${hints}
            </div>
            <div class="finish-player-buyin">${t("buyIn")}：${escapeHtml(buyIn)}</div>
            <div class="finish-player-input">
                <input
                    type="number"
                    class="finish-cashout-input"
                    data-user-id="${player.user_id}"
                    data-on-input="onFinishChipsInput"
                    min="0"
                    inputmode="numeric"
                    pattern="[0-9]*"
                    data-i18n-placeholder="cashOutPlaceholder"
                    placeholder="${escapeHtml(t("cashOutPlaceholder"))}"
                    value="${prefill}"
                >
                <div class="finish-player-net" data-net-for="${player.user_id}"></div>
            </div>
        `;

        container.appendChild(row);
    });

    document.getElementById("finish-game-note").value = "";
    document.getElementById("finish-message").innerText = "";
    resetFinishForce();
    updateFinishSummary();

    document.getElementById("finish-game-modal").style.display = "flex";
}

// 上次校验没通过时按钮会变成“强制结束”；只要改了任何数额，就恢复成重新校验
function resetFinishForce() {
    const btn = document.getElementById("finish-confirm-btn");
    btn.dataset.force = "false";
    btn.innerText = t("finishAndCheck");
    btn.className = "modal-confirm-button";
}

function onFinishChipsInput() {
    const btn = document.getElementById("finish-confirm-btn");
    if (btn.dataset.force === "true") {
        resetFinishForce();
        document.getElementById("finish-message").innerText = "";
    }
    updateFinishSummary();
}

function updateFinishSummary() {
    let totalBuyIn = 0;
    let totalLeft = 0;
    let totalChips = 0;
    let unfilled = 0;

    document.querySelectorAll(".finish-cashout-input").forEach(input => {
        const userId = parseInt(input.dataset.userId, 10);
        const player = _finishPlayerById(userId);
        const buyIn = player ? (player.total_buy_in || 0) : 0;
        const left = player ? (player.left_cash_out || 0) : 0;
        totalBuyIn += buyIn;
        totalLeft += left;

        const chips = _readChips(input);
        const netBox = document.querySelector(`.finish-player-net[data-net-for="${userId}"]`);
        if (isNaN(chips)) {
            unfilled += 1;
            if (netBox) {
                netBox.innerText = "";
                netBox.className = "finish-player-net";
            }
            return;
        }

        totalChips += chips;
        const net = left + chips - buyIn;
        if (netBox) {
            netBox.innerText = `${t("net")} ${formatSigned(net)}`;
            netBox.className = "finish-player-net " + (net > 0 ? "net-positive" : net < 0 ? "net-negative" : "net-zero");
        }
    });

    const diff = totalLeft + totalChips - totalBuyIn;
    let diffHtml;
    if (unfilled > 0) {
        diffHtml = `<span class="finish-summary-pending">${escapeHtml(t("summaryUnfilled").replace("{n}", unfilled))}</span>`;
    } else if (diff === 0) {
        diffHtml = `<span class="net-positive">${escapeHtml(t("balanced"))}</span>`;
    } else {
        diffHtml = `<span class="net-negative">${escapeHtml(describeChipDiff(diff))}</span>`;
    }

    const parts = [
        `${escapeHtml(t("totalBuyIn"))} <strong>${totalBuyIn}</strong>`,
        `${escapeHtml(t("summaryLeftCashOut"))} <strong>${totalLeft}</strong>`,
        `${escapeHtml(t("summaryFilledChips"))} <strong>${totalChips}</strong>`,
        `${escapeHtml(t("diff"))} ${diffHtml}`,
    ];
    document.getElementById("finish-summary").innerHTML = parts
        .map(part => `<span class="finish-summary-item">${part}</span>`)
        .join(`<span class="finish-summary-sep">·</span>`);
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

    const totalBuyIn = game.total_buy_in ?? 0;
    const totalCashOut = game.total_cash_out ?? 0;
    document.getElementById("settle-total-buyin").innerText = game.total_buy_in ?? "--";
    document.getElementById("settle-total-cashout").innerText = game.total_cash_out ?? "--";

    // 强制结束（账目没平）时不能再显示“校验成功”
    const balanced = Boolean(data.is_balanced ?? game.is_balanced);
    const icon = document.getElementById("settlement-icon");
    const title = document.getElementById("settlement-title");
    const summary = document.querySelector("#settlement-modal .settlement-summary");
    if (balanced) {
        icon.className = "fa-solid fa-circle-check settlement-success-icon";
        title.innerText = t("settlementSuccess");
        summary.classList.remove("unbalanced");
    } else {
        icon.className = "fa-solid fa-triangle-exclamation settlement-warning-icon";
        title.innerText = t("settlementUnbalanced").replace("{diff}", describeChipDiff(totalCashOut - totalBuyIn));
        summary.classList.add("unbalanced");
    }

    document.getElementById("settlement-report-btn").setAttribute("data-args", JSON.stringify([game.id]));

    const organizerId = game.organizer_id;
    const list = document.getElementById("settlement-player-list");
    list.innerHTML = "";

    players.forEach(player => {
        const name = displayPlayerName(player);
        const isOrganizer = player.user_id === organizerId;
        const buyIn = player.total_buy_in ?? 0;
        const cashOut = player.cash_out ?? 0;
        const net = player.net ?? (cashOut - buyIn);
        const netClass = net > 0 ? "net-positive" : net < 0 ? "net-negative" : "net-zero";

        const row = document.createElement("div");
        row.className = "settlement-row";

        row.innerHTML = `
            <div class="settlement-name">
                ${escapeHtml(name)}${isOrganizer ? ` <span class="organizer-tag">${t("organizer")}</span>` : ""}
            </div>
            <div class="settlement-cols">
                <span>${t("buyIn")}：${escapeHtml(buyIn)}</span>
                <span>${t("cashOut")}：${escapeHtml(cashOut)}</span>
                <span class="${netClass}">${t("net")}：${escapeHtml(formatSigned(net))}</span>
            </div>
        `;

        list.appendChild(row);
    });

    document.getElementById("settlement-modal").style.display = "flex";
}

async function confirmFinishGame() {
    const btn = document.getElementById("finish-confirm-btn");
    await runBusy("finish-game", btn, submitFinishGame);
}

async function submitFinishGame() {
    const messageBox = document.getElementById("finish-message");
    messageBox.style.color = "#ff8a8a";
    messageBox.innerText = "";

    if (!currentGame) return;

    const btn = document.getElementById("finish-confirm-btn");
    const force = btn.dataset.force === "true";

    const inputs = document.querySelectorAll(".finish-cashout-input");
    const playerCashOuts = [];

    for (const input of inputs) {
        const userId = parseInt(input.dataset.userId, 10);
        const cashOut = _readChips(input);

        if (isNaN(cashOut) || cashOut < 0) {
            messageBox.innerText = t("invalidCashOut");
            input.focus();
            return;
        }

        playerCashOuts.push({ user_id: userId, cash_out: cashOut });
    }

    const note = document.getElementById("finish-game-note").value.trim();

    const data = await apiFinishGame({
        game_id: currentGame.id,
        player_cash_outs: playerCashOuts,
        organizer_insurance_final: 0,
        organizer_anti_final: 0,
        force: force,
        note: note,
    });

    if (!data.success) {
        if (data.message === "balanceCheckFailed") {
            const diff = data.diff || 0;
            messageBox.innerText = t("balanceCheckFailed").replace("{diff}", describeChipDiff(diff));
            btn.dataset.force = "true";
            btn.innerText = t("forceFinish");
            btn.className = "modal-confirm-button warning";
        } else {
            reportGameFailure(data, messageBox);
        }
        return;
    }

    closeFinishGameModal();
    openSettlementModal(data);
    await loadGamePage();
}

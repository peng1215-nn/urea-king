// 买入明细弹窗：列出某位玩家的每一笔买入，局头可以撤销记错的那一笔。
// 撤销要在行内再确认一次（提醒先把筹码收回），确认后从总买入里减掉，不能恢复。

let buyinHistoryUserId = null;
let buyinHistoryRows = [];
let buyinConfirmId = null;

function _buyinTypeLabel(type) {
    if (type === "insurance") return t("buyInInsurance");
    if (type === "anti") return t("buyInAnti");
    return t("buyInNormal");
}

async function openBuyinHistoryModal(userId) {
    if (!currentGame) return;
    buyinHistoryUserId = userId;
    buyinConfirmId = null;
    buyinHistoryRows = [];

    const player = currentPlayers.find(p => p.user_id === userId);
    document.getElementById("buyin-history-player").innerText = player ? displayPlayerName(player) : "";
    document.getElementById("buyin-history-list").innerHTML = `<div class="buyin-history-empty">${escapeHtml(t("loading"))}</div>`;
    document.getElementById("buyin-history-modal").style.display = "flex";

    await loadBuyinHistory();
}

async function loadBuyinHistory() {
    if (!currentGame || buyinHistoryUserId === null) return;
    const data = await gameRequest(
        `/organizer/game/player-buyins?game_id=${encodeURIComponent(currentGame.id)}&user_id=${encodeURIComponent(buyinHistoryUserId)}`
    );
    const list = document.getElementById("buyin-history-list");
    if (!data || !data.success) {
        list.innerHTML = `<div class="buyin-history-empty">${escapeHtml(formatGameError(data))}</div>`;
        return;
    }
    buyinHistoryRows = data.buyins || [];
    renderBuyinHistory();
}

function renderBuyinHistory() {
    const list = document.getElementById("buyin-history-list");
    if (buyinHistoryRows.length === 0) {
        list.innerHTML = `<div class="buyin-history-empty">${escapeHtml(t("noBuyins"))}</div>`;
        return;
    }

    const active = buyinHistoryRows.filter(r => r.status === "approved").reduce((sum, r) => sum + r.amount, 0);

    list.innerHTML = buyinHistoryRows.map(row => {
        const reversed = row.status === "reversed";
        let action;
        if (reversed) {
            action = `<span class="buyin-history-reversed">${escapeHtml(t("buyinReversed"))}</span>`;
        } else if (buyinConfirmId === row.id) {
            const busy = isActionBusy(`reverse-${row.id}`) ? " disabled" : "";
            action = `
                <div class="buyin-history-confirm">
                    <span>${escapeHtml(t("reverseBuyinConfirm").replace("{amount}", row.amount))}</span>
                    <div class="buyin-history-confirm-actions">
                        <button class="btn-small btn-remove" data-on-click="confirmReverseBuyin" data-args="[${row.id}, &quot;$this&quot;]"${busy}>${escapeHtml(t("confirmReverse"))}</button>
                        <button class="btn-small" data-on-click="cancelReverseBuyin"${busy}>${escapeHtml(t("cancel"))}</button>
                    </div>
                </div>`;
        } else {
            action = `<button class="btn-small btn-remove" data-on-click="askReverseBuyin" data-args="[${row.id}]">${escapeHtml(t("reverseBuyin"))}</button>`;
        }
        return `
            <div class="buyin-history-row${reversed ? " reversed" : ""}">
                <div class="buyin-history-info">
                    <span class="buyin-history-amount">${escapeHtml(row.amount)}</span>
                    <span class="buyin-history-meta">${escapeHtml(_buyinTypeLabel(row.type))} · ${escapeHtml(row.time)}</span>
                </div>
                <div class="buyin-history-action">${action}</div>
            </div>`;
    }).join("") + `<div class="buyin-history-total">${escapeHtml(t("buyInTotal"))}${getCurrentLanguage() === "en" ? ": " : "："}<strong>${active}</strong></div>`;
}

function askReverseBuyin(requestId) {
    buyinConfirmId = requestId;
    renderBuyinHistory();
}

function cancelReverseBuyin() {
    buyinConfirmId = null;
    renderBuyinHistory();
}

async function confirmReverseBuyin(requestId, button) {
    if (!currentGame) return;
    const gameId = currentGame.id;
    const row = buyinHistoryRows.find(r => r.id === requestId);

    const data = await runBusy(`reverse-${requestId}`, button,
        () => _postForm("/organizer/game/reverse-buyin", { request_id: requestId, game_id: gameId }));
    if (!data) return;

    buyinConfirmId = null;
    if (data.success) {
        showGameMessage(t("reverseBuyinSuccess").replace("{amount}", row ? row.amount : ""), "success");
    } else {
        reportGameFailure(data, null);
    }
    await loadBuyinHistory();
    await loadGamePage();
}

function closeBuyinHistoryModal() {
    document.getElementById("buyin-history-modal").style.display = "none";
    buyinHistoryUserId = null;
    buyinConfirmId = null;
}

// 切换语言后弹窗里的文字跟着更新
document.addEventListener("languageChanged", function () {
    const modal = document.getElementById("buyin-history-modal");
    if (modal && modal.style.display !== "none" && buyinHistoryRows.length) renderBuyinHistory();
});

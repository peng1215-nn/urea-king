let pendingRemoveUserId = null;

function _findCurrentPlayer(userId) {
    return currentPlayers.find(p => p.user_id === userId) || null;
}

function openRemovePlayerModal(userId) {
    pendingRemoveUserId = userId;

    // 每次打开都从头选：不沿用上一次选的“暂离 / 退出”
    document.querySelectorAll(".remove-type-btn").forEach(btn => btn.classList.remove("active"));
    document.getElementById("remove-player-cashout").value = "";
    document.getElementById("remove-player-message").innerText = "";
    document.getElementById("remove-player-exit-section").style.display = "none";
    document.getElementById("remove-player-confirm-btn").disabled = true;

    const player = _findCurrentPlayer(userId);
    document.getElementById("remove-player-name").innerText = player ? displayPlayerName(player) : "";
    renderExitPlayerSummary();

    document.getElementById("remove-player-modal").style.display = "flex";
}

function closeRemovePlayerModal() {
    document.getElementById("remove-player-modal").style.display = "none";
    pendingRemoveUserId = null;
}

function selectRemoveType(type) {
    const exitSection = document.getElementById("remove-player-exit-section");
    if (type === "exit") {
        exitSection.style.display = "block";
        renderExitPlayerSummary();
    } else {
        exitSection.style.display = "none";
    }
    document.querySelectorAll(".remove-type-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.type === type);
    });
    document.getElementById("remove-player-confirm-btn").disabled = false;
    document.getElementById("remove-player-message").innerText = "";
}

// 结算离场：显示该玩家总买入，并随输入实时预览“本次卖出 Y，净 ±Z”
function renderExitPlayerSummary() {
    const player = _findCurrentPlayer(pendingRemoveUserId);
    const info = document.getElementById("remove-player-buyin-info");
    const preview = document.getElementById("remove-player-exit-preview");
    if (!info || !preview) return;

    if (!player) {
        info.innerText = "";
        preview.innerText = "";
        return;
    }

    const buyIn = player.total_buy_in || 0;
    const left = player.left_cash_out || 0;
    info.innerText = t("exitBuyInInfo").replace("{buyin}", buyIn)
        + (left > 0 ? t("exitLeftInfo").replace("{left}", left) : "");

    const raw = document.getElementById("remove-player-cashout").value.trim();
    const cashOut = /^\d+$/.test(raw) ? parseInt(raw, 10) : NaN;
    if (isNaN(cashOut)) {
        preview.innerText = "";
        preview.className = "exit-preview";
        return;
    }
    const net = left + cashOut - buyIn;
    preview.innerText = t("exitPreview")
        .replace("{amount}", cashOut)
        .replace("{net}", formatSigned(net));
    preview.className = "exit-preview " + (net > 0 ? "net-positive" : net < 0 ? "net-negative" : "net-zero");
}

function onExitCashoutInput() {
    renderExitPlayerSummary();
}

async function confirmRemovePlayer() {
    const button = document.getElementById("remove-player-confirm-btn");
    // 请求处理中不再接受点击，避免连点把同一次离场记两次
    await runBusy("remove-player", button, submitRemovePlayer);
}

async function submitRemovePlayer() {
    const messageBox = document.getElementById("remove-player-message");
    messageBox.style.color = "#ff8a8a";
    messageBox.innerText = "";

    if (!pendingRemoveUserId || !currentGame) return;

    const activeBtn = document.querySelector(".remove-type-btn.active");
    if (!activeBtn) {
        messageBox.innerText = t("pleaseSelectRemoveType");
        return;
    }

    const type = activeBtn.dataset.type;

    if (type === "away") {
        const data = await apiRemovePlayer(currentGame.id, pendingRemoveUserId);
        if (!data.success) {
            reportGameFailure(data, messageBox);
            return;
        }
        closeRemovePlayerModal();
        showGameMessage(t("playerAway"), "success");
        await loadGamePage();
    } else {
        const raw = document.getElementById("remove-player-cashout").value.trim();
        const cashOut = /^\d+$/.test(raw) ? parseInt(raw, 10) : NaN;
        if (isNaN(cashOut) || cashOut < 0) {
            messageBox.innerText = t("invalidAmount");
            return;
        }
        const data = await apiExitPlayer(currentGame.id, pendingRemoveUserId, cashOut);
        if (!data.success) {
            reportGameFailure(data, messageBox);
            return;
        }
        closeRemovePlayerModal();
        showGameMessage(t("playerExited"), "success");
        await loadGamePage();
    }
}

async function removePlayer(userId) {
    openRemovePlayerModal(userId);
}

async function rejoinPlayer(userId, button) {
    if (!currentGame) return;

    const gameId = currentGame.id;
    const data = await runBusy(`rejoin-${userId}`, button, () => apiAddPlayer(gameId, userId));
    if (!data) return; // 上一次点击还在处理中

    if (data.success) {
        showGameMessage(t("playerRejoined"), "success");
    } else {
        reportGameFailure(data, null);
    }
    await loadGamePage();
}

// ── 加入玩家 ──

// 成员是否已在“另一场”进行中的牌局里（局头可以同时开多局，不受限制）
function isMemberInOtherGame(member, gameId) {
    if (member.role === "organizer") return false;
    return (member.ongoing_game_ids || []).some(id => id !== gameId);
}

function renderAddPlayerList(members) {
    const inGameIds = new Set(currentPlayers.filter(p => p.is_active === 1).map(p => p.user_id));
    const gameId = currentGame ? currentGame.id : null;

    const list = document.getElementById("add-player-select-list");
    list.innerHTML = "";

    members.forEach(member => {
        const isInGame = inGameIds.has(member.user_id);
        const inOtherGame = !isInGame && isMemberInOtherGame(member, gameId);
        const disabled = isInGame || inOtherGame;
        const selected = !disabled && selectedAddPlayer.includes(member.user_id);

        const item = document.createElement("div");
        item.className = "member-select-item" + (disabled ? " disabled" : "") + (selected ? " selected" : "");
        item.dataset.userId = member.user_id;

        const avatarUrl = member.avatar_url || "/static/images/default_avatar.jpg";
        const label = isInGame ? t("inGame") : inOtherGame ? t("inOtherGame") : "";

        item.innerHTML = `
            <img class="member-select-avatar" src="${escapeHtml(avatarUrl)}" alt="头像">
            <span class="member-select-name">${escapeHtml(displayPlayerName(member))}</span>
            <span class="member-select-role">${label}</span>
            <div class="member-check"><i class="fa-solid fa-check" style="display:${selected ? "block" : "none"};"></i></div>
        `;

        if (!disabled) {
            item.addEventListener("click", () => toggleAddPlayer(item, member.user_id));
        }

        list.appendChild(item);
    });

    // 已选中但现在不可选的人（刚被加进别的局）从选择里去掉
    const selectable = new Set(
        members
            .filter(m => !inGameIds.has(m.user_id) && !isMemberInOtherGame(m, gameId))
            .map(m => m.user_id)
    );
    selectedAddPlayer = selectedAddPlayer.filter(id => selectable.has(id));
}

async function openAddPlayerModal() {
    selectedAddPlayer = [];

    const messageBox = document.getElementById("add-player-message");
    messageBox.innerText = "";

    const data = await fetchGroupMembers();
    if (!data.success) {
        reportGameFailure(data, null);
        return;
    }

    allGroupMembers = data.members;
    renderAddPlayerList(allGroupMembers);

    document.getElementById("add-player-modal").style.display = "flex";
}

function toggleAddPlayer(item, userId) {
    const idx = selectedAddPlayer.indexOf(userId);
    if (idx > -1) {
        selectedAddPlayer.splice(idx, 1);
        item.classList.remove("selected");
        item.querySelector(".fa-check").style.display = "none";
    } else {
        selectedAddPlayer.push(userId);
        item.classList.add("selected");
        item.querySelector(".fa-check").style.display = "block";
    }
}

function closeAddPlayerModal() {
    document.getElementById("add-player-modal").style.display = "none";
    selectedAddPlayer = [];
}

async function confirmAddPlayer() {
    const button = document.querySelector("#add-player-modal .modal-confirm-button");
    await runBusy("add-player", button, submitAddPlayer);
}

async function submitAddPlayer() {
    const messageBox = document.getElementById("add-player-message");
    messageBox.style.color = "#ff8a8a";
    messageBox.innerText = "";

    if (!selectedAddPlayer || selectedAddPlayer.length === 0) {
        messageBox.innerText = t("pleaseSelectMember");
        return;
    }

    if (!currentGame) return;

    const nameOf = userId => {
        const member = allGroupMembers.find(m => m.user_id === userId);
        return member ? displayPlayerName(member) : String(userId);
    };

    // 逐个加入，记下每个人的结果；有人失败时按人名列出来
    const added = [];
    const failed = [];
    let networkError = false;
    for (const userId of [...selectedAddPlayer]) {
        const data = await apiAddPlayer(currentGame.id, userId);
        if (data.success) {
            added.push(nameOf(userId));
        } else {
            if (data.networkError) networkError = true;
            // “已在其他牌局中”的提示本身带人名，其他提示在前面加上人名
            failed.push(data.message === "playerAlreadyInAnotherGame"
                ? formatGameError({ ...data, player_names: [nameOf(userId)] })
                : `${nameOf(userId)}：${formatGameError(data)}`);
        }
    }

    await loadGamePage();

    if (failed.length === 0) {
        closeAddPlayerModal();
        showGameMessage(`${t("addPlayerResultAdded").replace("{names}", added.join(t("nameListSep")))}`, "success");
        return;
    }

    const lines = [];
    if (added.length > 0) {
        lines.push(t("addPlayerResultAdded").replace("{names}", added.join(t("nameListSep"))));
    }
    lines.push(...failed);
    messageBox.innerText = lines.join("\n");
    if (networkError) showGameMessage(t("networkErrorCheck"), "error");

    // 刷新弹窗里的名单：刚加入的、已在别的局里的都置灰
    selectedAddPlayer = [];
    const members = await fetchGroupMembers();
    if (members.success) {
        allGroupMembers = members.members;
    }
    renderAddPlayerList(allGroupMembers);
}

// ── 审批买入申请 ──

function _requestCardButtons(button) {
    const card = button && button.closest ? button.closest(".request-card") : null;
    return card ? Array.from(card.querySelectorAll("button")) : [button];
}

async function approveRequest(requestId, button) {
    if (!currentGame) return;
    const gameId = currentGame.id;

    // 批准、拒绝两个按钮一起锁住，同一申请处理完之前不能再点
    const data = await runBusy(`request-${requestId}`, _requestCardButtons(button),
        () => apiApproveRequest(requestId, gameId));
    if (!data) return; // 这条申请正在处理中

    if (data.success) {
        showGameMessage(t("requestApproved"), "success");
    } else {
        reportGameFailure(data, null);
    }
    await loadGamePage();
}

async function rejectRequest(requestId, button) {
    if (!currentGame) return;
    const gameId = currentGame.id;

    const data = await runBusy(`request-${requestId}`, _requestCardButtons(button),
        () => apiRejectRequest(requestId, gameId));
    if (!data) return; // 这条申请正在处理中

    if (data.success) {
        showGameMessage(t("requestRejected"), "success");
    } else {
        reportGameFailure(data, null);
    }
    await loadGamePage();
}

// ── 局头买入 ──

let organizerBuyinUserId = null;

function openOrganizerBuyinModal(userId) {
    organizerBuyinUserId = userId;
    document.getElementById("organizer-buyin-type").value = "normal";
    document.getElementById("organizer-buyin-amount").value = "";
    document.getElementById("organizer-buyin-message").innerText = "";
    document.getElementById("organizer-buyin-modal").style.display = "flex";
}

function closeOrganizerBuyinModal() {
    document.getElementById("organizer-buyin-modal").style.display = "none";
    organizerBuyinUserId = null;
}

// ── 代买 modal ──
let proxyBuyinUserId = null;

function openProxyBuyinModal(userId) {
    proxyBuyinUserId = userId;
    const player = _findCurrentPlayer(userId);
    document.getElementById("proxy-buyin-player").innerText = player ? displayPlayerName(player) : "";
    document.getElementById("proxy-buyin-amount").value = "";
    document.getElementById("proxy-buyin-message").innerText = "";
    document.getElementById("proxy-buyin-modal").style.display = "flex";
}

function closeProxyBuyinModal() {
    document.getElementById("proxy-buyin-modal").style.display = "none";
    proxyBuyinUserId = null;
}

function _readPositiveAmount(inputId) {
    const raw = document.getElementById(inputId).value.trim();
    return /^\d+$/.test(raw) ? parseInt(raw, 10) : NaN;
}

async function confirmProxyBuyin() {
    const button = document.querySelector("#proxy-buyin-modal .modal-confirm-button");
    // 处理中锁住按钮，避免连点重复买入
    await runBusy("proxy-buyin", button, async () => {
        const messageBox = document.getElementById("proxy-buyin-message");
        messageBox.style.color = "#ff8a8a";
        messageBox.innerText = "";

        const amount = _readPositiveAmount("proxy-buyin-amount");
        if (!amount || amount <= 0) {
            messageBox.innerText = t("invalidAmount");
            return;
        }

        if (!currentGame || !proxyBuyinUserId) return;

        const data = await apiProxyBuyin(currentGame.id, proxyBuyinUserId, amount);

        if (!data.success) {
            reportGameFailure(data, messageBox);
            return;
        }

        closeProxyBuyinModal();
        showGameMessage(t("proxyBuyinSuccess"), "success");
        await loadGamePage();
    });
}

async function confirmOrganizerBuyin() {
    const button = document.querySelector("#organizer-buyin-modal .modal-confirm-button");
    // 处理中锁住按钮，避免连点重复买入
    await runBusy("organizer-buyin", button, async () => {
        const messageBox = document.getElementById("organizer-buyin-message");
        messageBox.style.color = "#ff8a8a";
        messageBox.innerText = "";

        const amount = _readPositiveAmount("organizer-buyin-amount");
        const buyType = document.getElementById("organizer-buyin-type").value;

        if (!amount || amount <= 0) {
            messageBox.innerText = t("invalidAmount");
            return;
        }

        if (!currentGame || !organizerBuyinUserId) return;

        const data = await apiOrganizerBuyin(currentGame.id, amount, buyType);

        if (!data.success) {
            reportGameFailure(data, messageBox);
            return;
        }

        closeOrganizerBuyinModal();
        showGameMessage(t("buyinSuccess"), "success");
        await loadGamePage();
    });
}

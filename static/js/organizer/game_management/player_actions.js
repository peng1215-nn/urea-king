async function removePlayer(userId) {
    if (!currentGame) return;

    const data = await apiRemovePlayer(currentGame.id, userId);

    const messageBox = document.getElementById("game-message");
    messageBox.style.color = "#ff8a8a";

    if (!data.success) {
        messageBox.innerText = t(data.message || "operationFailed");
        return;
    }

    messageBox.style.color = "#5CFFB2";
    messageBox.innerText = t("playerRemoved");
    await loadGamePage();
}

async function rejoinPlayer(userId) {
    if (!currentGame) return;

    const data = await apiAddPlayer(currentGame.id, userId);

    const messageBox = document.getElementById("game-message");
    messageBox.style.color = "#ff8a8a";

    if (!data.success) {
        messageBox.innerText = t(data.message || "operationFailed");
        return;
    }

    messageBox.style.color = "#5CFFB2";
    messageBox.innerText = t("playerRejoined");
    await loadGamePage();
}

async function openAddPlayerModal() {
    selectedAddPlayer = [];

    document.getElementById("add-player-message").innerText = "";

    const data = await fetchGroupMembers();
    if (!data.success) return;

    allGroupMembers = data.members;

    const inGameIds = new Set(currentPlayers.filter(p => p.is_active === 1).map(p => p.user_id));

    const list = document.getElementById("add-player-select-list");
    list.innerHTML = "";

    data.members.forEach(member => {
        const isInGame = inGameIds.has(member.user_id);

        const item = document.createElement("div");
        item.className = "member-select-item" + (isInGame ? " disabled" : "");
        item.dataset.userId = member.user_id;

        const avatarUrl = member.avatar_url || "/static/images/default_avatar.jpg";
        const name = member.nickname || member.username;

        item.innerHTML = `
            <img class="member-select-avatar" src="${avatarUrl}" alt="头像">
            <span class="member-select-name">${name}</span>
            <span class="member-select-role">${isInGame ? t("inGame") : ""}</span>
            <div class="member-check"><i class="fa-solid fa-check" style="display:none;"></i></div>
        `;

        if (!isInGame) {
            item.addEventListener("click", () => toggleAddPlayer(item, member.user_id));
        }

        list.appendChild(item);
    });

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
    const messageBox = document.getElementById("add-player-message");
    messageBox.style.color = "#ff8a8a";
    messageBox.innerText = "";

    if (!selectedAddPlayer || selectedAddPlayer.length === 0) {
        messageBox.innerText = t("pleaseSelectMember");
        return;
    }

    if (!currentGame) return;

    let lastError = null;
    for (const userId of selectedAddPlayer) {
        const data = await apiAddPlayer(currentGame.id, userId);
        if (!data.success) {
            lastError = data.message;
        }
    }

    if (lastError) {
        messageBox.innerText = t(lastError || "operationFailed");
        await loadGamePage();
        return;
    }

    closeAddPlayerModal();
    await loadGamePage();
}

async function approveRequest(requestId) {
    if (!currentGame) return;

    const data = await apiApproveRequest(requestId, currentGame.id);

    const messageBox = document.getElementById("game-message");
    messageBox.style.color = "#ff8a8a";

    if (!data.success) {
        messageBox.innerText = t(data.message || "operationFailed");
        return;
    }

    messageBox.style.color = "#5CFFB2";
    messageBox.innerText = t("requestApproved");
    await loadGamePage();
}

async function rejectRequest(requestId) {
    if (!currentGame) return;

    const data = await apiRejectRequest(requestId, currentGame.id);

    const messageBox = document.getElementById("game-message");
    messageBox.style.color = "#ff8a8a";

    if (!data.success) {
        messageBox.innerText = t(data.message || "operationFailed");
        return;
    }

    messageBox.style.color = "#5CFFB2";
    messageBox.innerText = t("requestRejected");
    await loadGamePage();
}


let organizerBuyinUserId = null;

function openOrganizerBuyinModal(userId) {
    organizerBuyinUserId = userId;
    document.getElementById("organizer-buyin-amount").value = "";
    document.getElementById("organizer-buyin-message").innerText = "";
    document.getElementById("organizer-buyin-modal").style.display = "flex";
}

function closeOrganizerBuyinModal() {
    document.getElementById("organizer-buyin-modal").style.display = "none";
    organizerBuyinUserId = null;
}

async function confirmOrganizerBuyin() {
    const messageBox = document.getElementById("organizer-buyin-message");
    messageBox.style.color = "#ff8a8a";
    messageBox.innerText = "";

    const amount = parseInt(document.getElementById("organizer-buyin-amount").value);
    const buyType = document.getElementById("organizer-buyin-type").value;

    if (!amount || amount <= 0) {
        messageBox.innerText = t("invalidAmount");
        return;
    }

    if (!currentGame || !organizerBuyinUserId) return;

    const fd = new FormData();
    fd.append("game_id", currentGame.id);
    fd.append("user_id", organizerBuyinUserId);
    fd.append("amount", amount);
    fd.append("buy_type", buyType);

    const res = await fetch("/organizer/game/organizer-buyin", { method: "POST", body: fd });
    const data = await res.json();

    if (!data.success) {
        messageBox.innerText = t(data.message || "operationFailed");
        return;
    }

    closeOrganizerBuyinModal();

    const gameMsg = document.getElementById("game-message");
    gameMsg.style.color = "#5CFFB2";
    gameMsg.innerText = t("buyinSuccess");

    await loadGamePage();
}
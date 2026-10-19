function openInsuranceModal(userId, insuranceType) {
    currentInsuranceType = insuranceType;
    currentInsuranceUserId = userId;

    document.getElementById("insurance-amount").value = "";
    document.getElementById("insurance-message").innerText = "";

    const title = document.getElementById("insurance-modal-title");
    const desc = document.getElementById("insurance-modal-desc");

    if (insuranceType === "payout") {
        title.innerText = t("insPayout");
        desc.innerText = t("insPayoutDesc");
    } else {
        title.innerText = t("insCollect");
        desc.innerText = t("insCollectDesc");
    }

    const select = document.getElementById("insurance-player-select");
    select.innerHTML = "";

    const organizerId = currentGame.organizer_id;

    const activePlayers = currentPlayers.filter(
        p => p.is_active === 1 && p.user_id !== organizerId
    );

    activePlayers.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p.user_id;
        opt.textContent = p.nickname || p.username;
        if (p.user_id === userId) opt.selected = true;
        select.appendChild(opt);
    });

    document.getElementById("insurance-modal").style.display = "flex";
}

function closeInsuranceModal() {
    document.getElementById("insurance-modal").style.display = "none";
    currentInsuranceType = null;
    currentInsuranceUserId = null;
}

async function confirmInsurance() {
    const messageBox = document.getElementById("insurance-message");
    messageBox.style.color = "#ff8a8a";
    messageBox.innerText = "";

    const userId = parseInt(document.getElementById("insurance-player-select").value);
    const amount = parseInt(document.getElementById("insurance-amount").value);

    if (!amount || amount <= 0) {
        messageBox.innerText = t("invalidAmount");
        return;
    }

    if (!currentGame) return;

    const data = await apiInsurance(currentGame.id, userId, amount, currentInsuranceType);

    if (!data.success) {
        messageBox.innerText = t(data.message || "operationFailed");
        return;
    }

    closeInsuranceModal();

    const gameMsg = document.getElementById("game-message");
    gameMsg.style.color = "#5CFFB2";
    gameMsg.innerText = t("insuranceRecorded");

    await loadGamePage();
}

function openAntiModal(userId) {
    currentAntiUserId = userId;

    document.getElementById("anti-amount").value = "";
    document.getElementById("anti-message").innerText = "";

    const select = document.getElementById("anti-player-select");
    select.innerHTML = "";

    const organizerId = currentGame.organizer_id;

    const activePlayers = currentPlayers.filter(
        p => p.is_active === 1 && p.user_id !== organizerId
    );

    activePlayers.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p.user_id;
        opt.textContent = p.nickname || p.username;
        if (p.user_id === userId) opt.selected = true;
        select.appendChild(opt);
    });

    document.getElementById("anti-modal").style.display = "flex";
}

function closeAntiModal() {
    document.getElementById("anti-modal").style.display = "none";
    currentAntiUserId = null;
}

async function confirmAnti() {
    const messageBox = document.getElementById("anti-message");
    messageBox.style.color = "#ff8a8a";
    messageBox.innerText = "";

    const userId = parseInt(document.getElementById("anti-player-select").value);
    const amount = parseInt(document.getElementById("anti-amount").value);

    if (!amount || amount <= 0) {
        messageBox.innerText = t("invalidAmount");
        return;
    }

    if (!currentGame) return;

    const data = await apiAnti(currentGame.id, userId, amount);

    if (!data.success) {
        messageBox.innerText = t(data.message || "operationFailed");
        return;
    }

    closeAntiModal();

    const gameMsg = document.getElementById("game-message");
    gameMsg.style.color = "#5CFFB2";
    gameMsg.innerText = t("antiRecorded");

    await loadGamePage();
}
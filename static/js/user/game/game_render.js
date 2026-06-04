let currentBuyinGameId = null;

async function loadUserGames() {
    const list = document.getElementById("game-list");
    list.innerHTML = `<div class="game-loading">${t("loading")}</div>`;

    const data = await fetchUserOngoingGames();

    if (!data.success) {
        list.innerHTML = `<div class="game-loading">${t("operationFailed")}</div>`;
        return;
    }

    if (!data.games || data.games.length === 0) {
        list.innerHTML = `<div class="game-loading">${t("notInGame")}</div>`;
        return;
    }

    list.innerHTML = "";

    data.games.forEach(game => {
        const card = document.createElement("div");
        card.className = "user-game-card";

        const pendingCount = game.requests.filter(r => r.status === "pending").length;

        let requestsHtml = "";
        if (game.requests.length > 0) {
            requestsHtml = `
                <div class="my-requests-title">${t("myBuyinRequests")}</div>
                <div class="my-requests-list">
                    ${game.requests.map(r => {
                        const statusClass = r.status === "approved" ? "req-approved"
                            : r.status === "rejected" ? "req-rejected" : "req-pending";
                        const statusText = r.status === "approved" ? t("requestApproved")
                            : r.status === "rejected" ? t("requestRejected") : t("requestPending");
                        return `<div class="request-row">
                            <span class="req-amount">${r.amount}</span>
                            <span class="req-time">${r.requested_at}</span>
                            <span class="req-status ${statusClass}">${statusText}</span>
                        </div>`;
                    }).join("")}
                </div>
            `;
        }

        card.innerHTML = `
            <div class="user-game-header">
                <div class="user-game-info">
                    ${game.name ? `<span class="user-game-name">${game.name}</span>` : ""}
                    <span class="user-game-time"><i class="fa-regular fa-clock"></i> ${game.started_at}</span>
                </div>
                <div class="user-game-meta">
                    <span class="user-game-buyin">${t("myBuyIn")}：${game.my_buy_in}</span>
                    ${pendingCount > 0 ? `<span class="pending-badge">${pendingCount} ${t("requestPending")}</span>` : ""}
                </div>
            </div>
            <div class="user-game-actions">
                <button class="btn-submit-buyin" onclick="openBuyinModal(${game.id})">
                    <i class="fa-solid fa-plus"></i>
                    ${t("submitBuyinRequest")}
                </button>
            </div>
            ${requestsHtml}
        `;

        list.appendChild(card);
    });
}

function openBuyinModal(gameId) {
    currentBuyinGameId = gameId;
    document.getElementById("buyin-amount").value = "";
    document.getElementById("buyin-message").innerText = "";
    document.getElementById("buyin-modal").style.display = "flex";
}

function closeBuyinModal() {
    document.getElementById("buyin-modal").style.display = "none";
    currentBuyinGameId = null;
}

async function confirmBuyin() {
    const messageBox = document.getElementById("buyin-message");
    messageBox.style.color = "#ff8a8a";
    messageBox.innerText = "";

    const amount = parseInt(document.getElementById("buyin-amount").value);
    if (!amount || amount <= 0) {
        messageBox.innerText = t("invalidAmount");
        return;
    }

    const data = await apiSubmitBuyinRequest(currentBuyinGameId, amount);

    if (!data.success) {
        messageBox.innerText = t(data.message || "operationFailed");
        return;
    }

    messageBox.style.color = "#5CFFB2";
    messageBox.innerText = t("buyinRequestSuccess");

    setTimeout(() => {
        closeBuyinModal();
        loadUserGames();
    }, 1200);
}
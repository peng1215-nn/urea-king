async function openStartGameModal() {
    selectedPreselect = [];

    document.getElementById("start-game-message").innerText = "";
    document.getElementById("selected-count").innerText = "0";
    document.getElementById("start-game-name").value = "";

    const data = await fetchGroupMembers();

    if (!data.success) {
        return;
    }

    allGroupMembers = data.members;

    const list = document.getElementById("member-select-list");
    list.innerHTML = "";

    // 找到局头并强制预选
    const organizer = data.members.find(m => m.role === "organizer");
    if (organizer) {
        selectedPreselect.push(organizer.user_id);
    }

    data.members.forEach(member => {
        const isOrganizer = member.role === "organizer";
        const item = document.createElement("div");
        item.className = "member-select-item" + (isOrganizer ? " selected forced" : "");
        item.dataset.userId = member.user_id;

        const avatarUrl = member.avatar_url || "/static/images/default_avatar.jpg";
        const name = member.nickname || member.username;
        const roleLabel = isOrganizer ? t("organizer") : t("roleUser");

        item.innerHTML = `
            <img class="member-select-avatar" src="${avatarUrl}" alt="头像">
            <span class="member-select-name">${name}</span>
            <span class="member-select-role">${roleLabel}</span>
            <div class="member-check"><i class="fa-solid fa-check" style="display:${isOrganizer ? 'block' : 'none'};"></i></div>
        `;

        if (!isOrganizer) {
            item.addEventListener("click", () => togglePreselect(item, member.user_id));
        }

        list.appendChild(item);
    });

    document.getElementById("selected-count").innerText = selectedPreselect.length;
    document.getElementById("start-game-modal").style.display = "flex";
}

function togglePreselect(item, userId) {
    const idx = selectedPreselect.indexOf(userId);

    if (idx > -1) {
        selectedPreselect.splice(idx, 1);
        item.classList.remove("selected");
        item.querySelector(".fa-check").style.display = "none";
    } else {
        if (selectedPreselect.length >= 10) {
            document.getElementById("start-game-message").innerText = t("tooManyPlayers");
            return;
        }
        selectedPreselect.push(userId);
        item.classList.add("selected");
        item.querySelector(".fa-check").style.display = "block";
    }

    document.getElementById("selected-count").innerText = selectedPreselect.length;
    document.getElementById("start-game-message").innerText = "";
}

function closeStartGameModal() {
    document.getElementById("start-game-modal").style.display = "none";
    selectedPreselect = [];
}

async function confirmStartGame() {
    const messageBox = document.getElementById("start-game-message");
    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    const name = document.getElementById("start-game-name").value.trim();

    if (!name) {
        messageBox.innerText = t("gameNameRequired");
        return;
    }

    const data = await apiStartGame(selectedPreselect, name);

    if (!data.success) {
        const msg = data.message || "operationFailed";
        if (msg.startsWith("playerAlreadyInGame:")) {
            const playerName = msg.split(":")[1];
            messageBox.innerText = `${playerName} ${t("playerAlreadyInAnotherGame")}`;
        } else {
            messageBox.innerText = t(msg);
        }
        return;
    }

    closeStartGameModal();
    await loadGamePage();
}
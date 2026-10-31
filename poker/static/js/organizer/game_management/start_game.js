let selectedPreselect = [];
let startSelfDefaulted = false;   // 打开弹窗时默认勾上自己（只做一次，之后由局头自己决定）

// 没勾选自己 = 本局只管理、不上桌：给出提示
function updateStartManagerHint() {
    const hint = document.getElementById("start-manager-hint");
    if (!hint) return;
    hint.hidden = currentMeId === null || selectedPreselect.includes(currentMeId);
}

function renderStartMemberList(members) {
    const list = document.getElementById("member-select-list");
    list.innerHTML = "";

    // 开局的人默认上桌，也可以取消勾选，只管理不上桌；组里另一位局头和普通成员一样可选可不选
    const meId = currentMeId;

    members.forEach(member => {
        const isOrganizer = member.role === "organizer";
        const isMe = member.user_id === meId;
        // 已在其他进行中的牌局里的人（开局人自己除外）不能再选
        const inOtherGame = !isMe && (member.ongoing_game_ids || []).length > 0;
        const selected = !inOtherGame && selectedPreselect.includes(member.user_id);

        const item = document.createElement("div");
        item.className = "member-select-item"
            + (selected ? " selected" : "")
            + (inOtherGame ? " disabled" : "");
        item.dataset.userId = member.user_id;

        const avatarUrl = member.avatar_url || "/static/images/default_avatar.jpg";
        const roleLabel = inOtherGame ? t("inOtherGame")
            : isMe ? t("organizerMe") : isOrganizer ? t("organizer") : t("roleUser");

        item.innerHTML = `
            <img class="member-select-avatar" src="${escapeHtml(avatarUrl)}" alt="头像">
            <span class="member-select-name">${escapeHtml(displayPlayerName(member))}</span>
            <span class="member-select-role">${roleLabel}</span>
            <div class="member-check"><i class="fa-solid fa-check" style="display:${selected ? "block" : "none"};"></i></div>
        `;

        if (!inOtherGame) {
            item.addEventListener("click", () => togglePreselect(item, member.user_id));
        }

        list.appendChild(item);
    });

    // 选中名单只保留仍可选的人（开局人自己始终在内）
    const selectable = new Set(
        members
            .filter(m => m.user_id === meId || (m.ongoing_game_ids || []).length === 0)
            .map(m => m.user_id)
    );
    selectedPreselect = selectedPreselect.filter(id => selectable.has(id));

    document.getElementById("selected-count").innerText = selectedPreselect.length;
    updateStartManagerHint();
}

async function openStartGameModal() {
    selectedPreselect = [];
    startSelfDefaulted = false;

    document.getElementById("start-game-message").innerText = "";
    document.getElementById("selected-count").innerText = "0";
    document.getElementById("start-game-name").value = "";

    const data = await fetchGroupMembers();

    if (!data.success) {
        reportGameFailure(data, null);
        return;
    }

    allGroupMembers = data.members;
    if (data.me !== undefined && data.me !== null) currentMeId = data.me;
    // 默认自己上桌；取消勾选就是只管理
    if (!startSelfDefaulted && currentMeId !== null) {
        selectedPreselect = [currentMeId];
        startSelfDefaulted = true;
    }
    renderStartMemberList(allGroupMembers);

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
    updateStartManagerHint();
}

function closeStartGameModal() {
    document.getElementById("start-game-modal").style.display = "none";
    selectedPreselect = [];
}

async function confirmStartGame() {
    const button = document.querySelector("#start-game-modal .modal-confirm-button");
    await runBusy("start-game", button, submitStartGame);
}

async function submitStartGame() {
    const messageBox = document.getElementById("start-game-message");
    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    // 牌局名称可以不填（后端允许，列表里按序号显示）
    const name = document.getElementById("start-game-name").value.trim();

    const data = await apiStartGame(selectedPreselect, name);

    if (!data.success) {
        reportGameFailure(data, messageBox);
        if (data.message === "playerAlreadyInAnotherGame") {
            // 刷新名单，把已在其他牌局里的人置灰并取消勾选
            const members = await fetchGroupMembers();
            if (members.success) {
                allGroupMembers = members.members;
                renderStartMemberList(allGroupMembers);
            }
        }
        return;
    }

    closeStartGameModal();
    showGameMessage(t("gameStarted"), "success");
    await loadGamePage();
}

async function loadInviteCodes() {
    const list = document.getElementById("invite-list");
    list.innerHTML = `<div class="invite-loading">${t("loading")}</div>`;

    const data = await fetchInviteCodes();

    if (!data.success) {
        list.innerHTML = `<div class="invite-loading">${t("operationFailed")}</div>`;
        return;
    }

    // 更新用量提示
    const quota = document.getElementById("invite-quota");
    if (quota && data.invite_code_limit !== undefined) {
        const count = data.invite_code_count ?? (data.codes ? data.codes.length : 0);
        const limit = data.invite_code_limit;
        const atLimit = count >= limit;
        quota.style.color = atLimit ? "#ff8a8a" : "rgba(200,210,255,0.5)";
        quota.textContent = `${count} / ${limit}`;
    }

    if (!data.codes || data.codes.length === 0) {
        list.innerHTML = `<div class="invite-loading">${t("noInviteCodes")}</div>`;
        return;
    }

    list.innerHTML = "";

    data.codes.forEach(code => {
        const card = document.createElement("div");
        card.className = "invite-card" + (code.is_used ? " used" : "");

        const statusClass = code.is_used ? "used" : "unused";
        const statusText = code.is_used ? t("inviteUsed") : t("inviteUnused");
        const usedBy = code.is_used
            ? `<span>${t("usedBy")}：${escapeHtml(code.used_by_username || "--")}</span><span>${t("usedAt")}：${escapeHtml(code.used_at || "--")}</span>`
            : `<span>${t("createdAt")}：${escapeHtml(code.created_at)}</span>`;

        const deleteBtn = !code.is_used
            ? `<button class="btn-delete-invite" data-on-click="deleteInviteCode" data-args="[${code.id}]">${t("delete")}</button>`
            : "";

        // 未使用的邀请码可以一键复制，发给要邀请的人
        const copyBtn = !code.is_used
            ? `<button class="btn-copy-invite" data-on-click="copyInviteCode" data-args="[&quot;$this&quot;]">${t("copy")}</button>`
            : "";

        card.innerHTML = `
            <div class="invite-code">${escapeHtml(code.code)}</div>
            <div class="invite-meta">${usedBy}</div>
            <span class="invite-status-badge ${statusClass}">${statusText}</span>
            ${copyBtn}
            ${deleteBtn}
        `;

        list.appendChild(card);
    });
}

async function createInviteCode() {
    const messageBox = document.getElementById("invite-message");
    messageBox.style.color = "#ff8a8a";
    messageBox.innerText = "";

    // 邀请码由系统随机生成，不需要填写
    const data = await apiCreateInviteCode();

    if (!data.success) {
        messageBox.innerText = t(data.message || "operationFailed");
        return;
    }

    messageBox.style.color = "#5CFFB2";
    messageBox.innerText = t("inviteCreateSuccess");

    await loadInviteCodes();
}

async function deleteInviteCode(inviteId) {
    const messageBox = document.getElementById("invite-message");
    messageBox.style.color = "#ff8a8a";
    messageBox.innerText = "";

    const data = await apiDeleteInviteCode(inviteId);

    if (!data.success) {
        messageBox.innerText = t(data.message || "operationFailed");
        return;
    }

    messageBox.style.color = "#5CFFB2";
    messageBox.innerText = t("inviteDeleteSuccess");

    await loadInviteCodes();
}

// 选中邀请码文字，方便无法自动复制时手动复制
function _selectInviteCodeText(element) {
    try {
        const range = document.createRange();
        range.selectNodeContents(element);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
    } catch (error) {
        // 选不中也没关系，用户可以长按复制
    }
}

function copyInviteCode(button) {
    const card = button.closest(".invite-card");
    const codeElement = card ? card.querySelector(".invite-code") : null;
    if (!codeElement) return;

    const code = codeElement.textContent.trim();
    const messageBox = document.getElementById("invite-message");

    const onCopied = () => {
        button.innerText = t("copied");
        button.classList.add("copied");
        setTimeout(() => {
            button.innerText = t("copy");
            button.classList.remove("copied");
        }, 1500);
        messageBox.style.color = "#5CFFB2";
        messageBox.innerText = t("copied");
    };

    const onFailed = () => {
        _selectInviteCodeText(codeElement);
        messageBox.style.color = "#ff8a8a";
        messageBox.innerText = t("copyFailed");
    };

    // 必须在点击事件里直接调用剪贴板接口（部分浏览器要求）
    try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(code).then(onCopied, onFailed);
        } else {
            onFailed();
        }
    } catch (error) {
        onFailed();
    }
}

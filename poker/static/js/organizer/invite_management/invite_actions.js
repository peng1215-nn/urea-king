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
            ? `<button class="btn-delete-invite" onclick="deleteInviteCode(${code.id})">${t("delete")}</button>`
            : "";

        card.innerHTML = `
            <div class="invite-code">${escapeHtml(code.code)}</div>
            <div class="invite-meta">${usedBy}</div>
            <span class="invite-status-badge ${statusClass}">${statusText}</span>
            ${deleteBtn}
        `;

        list.appendChild(card);
    });
}

async function createInviteCode() {
    const messageBox = document.getElementById("invite-message");
    messageBox.style.color = "#ff8a8a";
    messageBox.innerText = "";

    const input = document.getElementById("invite-code-input");
    const code = input.value.trim();

    if (!code) {
        messageBox.innerText = t("inviteCodeRequired");
        return;
    }

    const data = await apiCreateInviteCode(code);

    if (!data.success) {
        messageBox.innerText = t(data.message || "operationFailed");
        return;
    }

    messageBox.style.color = "#5CFFB2";
    messageBox.innerText = t("inviteCreateSuccess");
    input.value = "";

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
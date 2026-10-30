// 渲染时把成员对象存在这里，行上只放下标，避免把 JSON 拼进 onclick 属性导致注入
let renderedMembers = [];

// 身份显示为当前语言的文字（organizer → 局头 / Organizer，user → 用户 / User）
function memberRoleLabel(role) {
    if (role === "organizer") return t("organizer");
    if (role === "user") return t("roleUser");
    return role || "--";
}

function renderMembers(members) {
    const tableBody = document.getElementById("user-table-body");

    tableBody.innerHTML = "";

    renderedMembers = members;

    members.forEach((member, index) => {
        const avatarUrl =
            member.avatar_url || "/static/images/default_avatar.jpg";

        const username = member.username || "--";
        const nickname = member.nickname || "--";
        const role     = memberRoleLabel(member.role);

        const roleClass =
            member.role === "organizer" ? "organizer" : "";

        const isActive = parseInt(member.is_active) === 1;

        const statusHtml = isActive
            ? `<span class="status-active">${t("accountEnabled")}</span>`
            : `<span class="status-disabled">${t("accountDisabled")}</span>`;

        const createdAt = member.created_at || "--";

        const row = `
            <tr data-member-index="${index}" data-on-click="selectMemberRow" data-args="[&quot;$this&quot;]">

                <td title="${escapeHtml(username)}">
                    <img
                        class="user-avatar"
                        src="${escapeHtml(avatarUrl)}"
                        alt="头像"
                    >
                </td>

                <td
                    class="${getMemberMatchedClass(member, "nickname")}"
                    title="${escapeHtml(nickname)}"
                >
                    <span class="truncate-text nickname-truncate">
                        ${escapeHtml(nickname)}
                    </span>
                </td>

                <td title="${escapeHtml(role)}">
                    <span class="role-badge ${roleClass} ${getMemberMatchedClass(member, "role")}">
                        <span class="truncate-text role-truncate">
                            ${escapeHtml(role)}
                        </span>
                    </span>
                </td>

                <td>
                    ${statusHtml}
                </td>

                <td title="${escapeHtml(createdAt)}">
                    <span class="truncate-text time-truncate">
                        ${escapeHtml(createdAt)}
                    </span>
                </td>

            </tr>
        `;

        tableBody.innerHTML += row;
    });
}


function getMemberMatchedClass(member, fieldName) {
    if (
        member.matched_fields
        && member.matched_fields.includes(fieldName)
    ) {
        return "search-highlight";
    }

    return "";
}


// 点击成员表格的一行（由 actions.js 调用）
function selectMemberRow(row) {
    selectMember(renderedMembers[Number(row.dataset.memberIndex)], row);

    // 手机上详情和操作区在表格下方，选中后自动滚过去
    if (window.matchMedia && window.matchMedia("(max-width: 768px)").matches) {
        const detail = document.querySelector(".detail-panel");
        if (detail) detail.scrollIntoView({ behavior: "smooth", block: "start" });
    }
}


// 切换语言后重新渲染表格（身份等文字），并保留当前选中行
document.addEventListener("languageChanged", function () {
    if (!Array.isArray(renderedMembers) || renderedMembers.length === 0) return;
    renderMembers(renderedMembers);
    if (typeof selectedMember !== "undefined" && selectedMember) {
        const index = renderedMembers.findIndex(m => m.id === selectedMember.id);
        const row = document.querySelector(`#user-table-body tr[data-member-index="${index}"]`);
        if (row) row.classList.add("active");
        refreshSelectedMemberLanguage();
    }
});

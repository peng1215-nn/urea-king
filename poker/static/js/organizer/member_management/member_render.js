// 渲染时把成员对象存在这里，行上只放下标，避免把 JSON 拼进 onclick 属性导致注入
let renderedMembers = [];

function renderMembers(members) {
    const tableBody = document.getElementById("user-table-body");

    tableBody.innerHTML = "";

    renderedMembers = members;

    members.forEach((member, index) => {
        const avatarUrl =
            member.avatar_url || "/static/images/default_avatar.jpg";

        const username = member.username || "--";
        const nickname = member.nickname || "--";
        const role     = member.role     || "--";

        const roleClass =
            member.role === "organizer" ? "organizer" : "";

        const isActive = parseInt(member.is_active) === 1;

        const statusHtml = isActive
            ? `<span class="status-active">${t("accountEnabled")}</span>`
            : `<span class="status-disabled">${t("accountDisabled")}</span>`;

        const createdAt = member.created_at || "--";

        const row = `
            <tr data-member-index="${index}" onclick="selectMember(renderedMembers[Number(this.dataset.memberIndex)], this)">

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
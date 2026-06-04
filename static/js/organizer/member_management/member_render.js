function renderMembers(members) {
    const tableBody = document.getElementById("user-table-body");

    tableBody.innerHTML = "";

    members.forEach((member) => {
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
            <tr onclick='selectMember(${JSON.stringify(member)}, this)'>

                <td title="${username}">
                    <img
                        class="user-avatar"
                        src="${avatarUrl}"
                        alt="头像"
                    >
                </td>

                <td
                    class="${getMemberMatchedClass(member, "nickname")}"
                    title="${nickname}"
                >
                    <span class="truncate-text nickname-truncate">
                        ${nickname}
                    </span>
                </td>

                <td title="${role}">
                    <span class="role-badge ${roleClass} ${getMemberMatchedClass(member, "role")}">
                        <span class="truncate-text role-truncate">
                            ${role}
                        </span>
                    </span>
                </td>

                <td>
                    ${statusHtml}
                </td>

                <td title="${createdAt}">
                    <span class="truncate-text time-truncate">
                        ${createdAt}
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
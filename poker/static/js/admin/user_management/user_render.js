function renderUsers(users) {
    const tableBody = document.getElementById("user-table-body");

    tableBody.innerHTML = "";

    users.forEach((user) => {
        const avatarUrl =
            user.avatar_url || "/static/images/default_avatar.jpg";

        const username =
            user.username || "--";

        const nickname =
            user.nickname || "--";

        const role =
            user.role || "--";

        const groupName =
            user.group_name || user.group_id || "--";

        const createdAt =
            user.created_at || "--";

        const roleClass =
            user.role === "admin"
                ? "admin"
                : user.role === "organizer"
                    ? "organizer"
                    : "";

        const row = `
            <tr onclick='selectUser(${JSON.stringify(user)}, this)'>

                <td title="${username}">
                    <img
                        class="user-avatar"
                        src="${avatarUrl}"
                        alt="头像"
                    >
                </td>

                <td
                    class="${getMatchedClass(user, "nickname")}"
                    title="${nickname}"
                >
                    <span class="truncate-text nickname-truncate" >
                        ${nickname}
                    </span>
                </td>

                <td title="${role}">
                    <span
                        class="role-badge ${roleClass} ${getMatchedClass(user, "role")}"
                    >
                        <span class="truncate-text role-truncate">
                            ${role}
                        </span>
                    </span>
                </td>

                <td
                    class="${getGroupMatchedClass(user)}"
                    title="${groupName}"
                >
                    <span class="truncate-text group-truncate">
                        ${groupName}
                    </span>
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


function getMatchedClass(user, fieldName) {
    if (
        user.matched_fields
        &&
        user.matched_fields.includes(fieldName)
    ) {
        return "search-highlight";
    }

    return "";
}


function getGroupMatchedClass(user) {
    if (
        user.matched_fields
        &&
        user.matched_fields.includes("group_name")
    ) {
        return "search-highlight";
    }

    return "";
}
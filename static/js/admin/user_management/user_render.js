function renderUsers(users) {
    const tableBody = document.getElementById("user-table-body");

    tableBody.innerHTML = "";

    users.forEach(user => {
        const avatarUrl =
            user.avatar_url || "/static/images/default_avatar.jpg";

        const groupId =
            user.group_id || "--";

        const roleClass =
            user.role === "admin"
                ? "admin"
                : user.role === "organizer"
                    ? "organizer"
                    : "";

        const row = `
            <tr onclick='selectUser(${JSON.stringify(user)}, this)'>

                <td>
                    <img
                        class="user-avatar"
                        src="${avatarUrl}"
                        alt="头像"
                    >
                </td>

                <td>
                    ${user.nickname || "--"}
                </td>

                <td>
                    <span class="role-badge ${roleClass}">
                        ${user.role}
                    </span>
                </td>

                <td>
                    ${groupId}
                </td>

                <td>
                    ${user.created_at}
                </td>

            </tr>
        `;

        tableBody.innerHTML += row;
    });
}
// 渲染时把用户对象存在这里，行上只放下标，避免把 JSON 拼进 onclick 属性导致注入
let renderedUsers = [];

function renderUsers(users) {
    const tableBody = document.getElementById("user-table-body");

    tableBody.innerHTML = "";

    renderedUsers = users;

    users.forEach((user, index) => {
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
            <tr data-user-index="${index}" data-on-click="selectUserRow" data-args="[&quot;$this&quot;]">

                <td title="${escapeHtml(username)}">
                    <img
                        class="user-avatar"
                        src="${escapeHtml(avatarUrl)}"
                        alt="头像"
                    >
                </td>

                <td
                    class="${getMatchedClass(user, "nickname")}"
                    title="${escapeHtml(nickname)}"
                >
                    <span class="truncate-text nickname-truncate" >
                        ${escapeHtml(nickname)}
                    </span>
                </td>

                <td title="${escapeHtml(role)}">
                    <span
                        class="role-badge ${roleClass} ${getMatchedClass(user, "role")}"
                    >
                        <span class="truncate-text role-truncate">
                            ${escapeHtml(role)}
                        </span>
                    </span>
                </td>

                <td
                    class="${getGroupMatchedClass(user)}"
                    title="${escapeHtml(groupName)}"
                >
                    <span class="truncate-text group-truncate">
                        ${escapeHtml(groupName)}
                    </span>
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


// 点击用户表格的一行（由 actions.js 调用）
function selectUserRow(row) {
    selectUser(renderedUsers[Number(row.dataset.userIndex)], row);
}

function searchUsers() {
    const keyword = document
        .getElementById("user-search")
        .value
        .trim()
        .toLowerCase();

    const messageBox = document.getElementById("search-message");

    messageBox.style.color = "#ff8a8a";
    messageBox.innerText = "";

    if (keyword.length === 0) {
        messageBox.innerText =
            "请输入用户名、昵称、身份或组名。";

        renderUsers(allUsers);

        return;
    }

    const matchedUsers = allUsers
        .map(user => {
            const matchedFields = getMatchedFields(user, keyword);

            return {
                ...user,
                matched_fields: matchedFields,
            };
        })
        .filter(user => user.matched_fields.length > 0);

    if (matchedUsers.length === 0) {
        messageBox.innerText = "未找到匹配的用户。";
        renderUsers([]);

        return;
    }

    messageBox.style.color = "#5CFFB2";
    messageBox.innerText =
        `找到 ${matchedUsers.length} 个匹配用户。`;

    renderUsers(matchedUsers);
}


function getMatchedFields(user, keyword) {
    const matchedFields = [];

    const username =
        String(user.username || "").toLowerCase();

    const nickname =
        String(user.nickname || "").toLowerCase();

    const role =
        String(user.role || "").toLowerCase();

    const groupName =
        String(user.group_name || "").toLowerCase();

    if (username === keyword) {
        matchedFields.push("username");
    }

    if (nickname === keyword) {
        matchedFields.push("nickname");
    }

    if (role === keyword) {
        matchedFields.push("role");
    }

    if (groupName === keyword) {
        matchedFields.push("group_name");
    }

    return matchedFields;
}


function clearSearch() {
    document.getElementById("user-search").value = "";

    const messageBox = document.getElementById("search-message");

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    renderUsers(allUsers);
}
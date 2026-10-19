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
            t("searchEmpty");

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
        messageBox.innerText = t("searchNoResult");
        renderUsers([]);

        return;
    }

    messageBox.style.color = "#5CFFB2";
    messageBox.innerText =
        `${t("searchResultPrefix")} ${matchedUsers.length} ${t("searchResultSuffix")}`;

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

    const messageBox =
        document.getElementById("search-message");

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    renderUsers(allUsers);

    resetSelectedUserState();

    document.getElementById("update-user-message").innerText = "";
    document.getElementById("reset-password-message").innerText = "";
    document.getElementById("user-status-message").innerText = "";
}
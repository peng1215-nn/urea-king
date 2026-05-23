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
        messageBox.innerText = "请输入要搜索的用户名或昵称。";
        return;
    }

    const filteredUsers = allUsers.filter((user) => {
        const username =
            String(user.username || "").toLowerCase();

        const nickname =
            String(user.nickname || "").toLowerCase();

        return username === keyword || nickname === keyword;
    });

    if (filteredUsers.length === 0) {
        messageBox.innerText = "未找到匹配的用户。";
        return;
    }

    messageBox.style.color = "#5CFFB2";

    messageBox.innerText =
        `找到 ${filteredUsers.length} 个匹配用户。`;

    renderUsers(filteredUsers);
}


function clearSearch() {
    document.getElementById("user-search").value = "";

    const messageBox =
        document.getElementById("search-message");

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    renderUsers(allUsers);
}
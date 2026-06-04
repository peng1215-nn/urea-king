function searchMembers() {
    const keyword = document
        .getElementById("user-search")
        .value
        .trim()
        .toLowerCase();

    const messageBox = document.getElementById("search-message");

    messageBox.style.color = "#ff8a8a";
    messageBox.innerText = "";

    if (keyword.length === 0) {
        messageBox.innerText = t("searchEmpty");
        renderMembers(allMembers);
        return;
    }

    const matched = allMembers
        .map(member => {
            const matchedFields = getMemberMatchedFields(member, keyword);
            return { ...member, matched_fields: matchedFields };
        })
        .filter(member => member.matched_fields.length > 0);

    if (matched.length === 0) {
        messageBox.innerText = t("searchNoResult");
        renderMembers([]);
        return;
    }

    messageBox.style.color = "#5CFFB2";
    messageBox.innerText =
        `${t("searchResultPrefix")} ${matched.length} ${t("searchResultSuffix")}`;

    renderMembers(matched);
}


function getMemberMatchedFields(member, keyword) {
    const matchedFields = [];

    const username = String(member.username || "").toLowerCase();
    const nickname = String(member.nickname || "").toLowerCase();
    const role     = String(member.role     || "").toLowerCase();

    if (username === keyword) matchedFields.push("username");
    if (nickname === keyword) matchedFields.push("nickname");
    if (role     === keyword) matchedFields.push("role");

    return matchedFields;
}


function clearSearch() {
    document.getElementById("user-search").value = "";

    const messageBox = document.getElementById("search-message");
    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    renderMembers(allMembers);
    resetSelectedMemberState();
}
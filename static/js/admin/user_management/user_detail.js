function selectUser(user, rowElement) {
    selectedUser = user;

    document
        .querySelectorAll("#user-table-body tr")
        .forEach(row => {
            row.classList.remove("active");
        });

    rowElement.classList.add("active");

    setDetailText(
        "detail-username",
        user.username || "--"
    );

    setDetailText(
        "detail-nickname",
        user.nickname || "--"
    );

    setDetailText(
        "detail-role",
        user.role || "--"
    );

    setDetailText(
        "detail-group",
        user.group_name || user.group_id || "--"
    );

    setDetailText(
        "detail-created-at",
        user.created_at || "--"
    );

    setDetailText(
        "detail-status",
        "正常"
    );

    document.getElementById("edit-role").value =
        user.role || "";

    document.getElementById("selected-user-status").innerText =
        "正常";
}


function setDetailText(elementId, value) {
    const element = document.getElementById(elementId);

    if (!element) {
        return;
    }

    element.innerHTML = `
        <span
            class="truncate-text detail-truncate"
            title="${value}"
        >
            ${value}
        </span>
    `;
}


function logout() {
    window.location.href = "/logout";
}
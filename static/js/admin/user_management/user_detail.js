function selectUser(user, rowElement) {
    selectedUser = user;

    document
        .querySelectorAll("#user-table-body tr")
        .forEach(row => {
            row.classList.remove("active");
        });

    rowElement.classList.add("active");

    document.getElementById("detail-username").innerText =
        user.username;

    document.getElementById("detail-nickname").innerText =
        user.nickname || "--";

    document.getElementById("detail-role").innerText =
        user.role;

    document.getElementById("detail-group").innerText =
        user.group_id || "--";

    document.getElementById("detail-created-at").innerText =
        user.created_at;

    document.getElementById("detail-status").innerText =
        "正常";

    document.getElementById("edit-nickname").value =
        user.nickname || "";

    document.getElementById("edit-role").value =
        user.role;

    document.getElementById("edit-group-id").value =
        user.group_id || "";

    document.getElementById("selected-user-status").innerText =
        "正常";
}


function logout() {
    window.location.href = "/logout";
}
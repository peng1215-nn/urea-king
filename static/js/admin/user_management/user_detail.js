function selectUser(user, rowElement) {
    selectedUser = user;

    document
        .querySelectorAll("#user-table-body tr")
        .forEach(row => {
            row.classList.remove("active");
        });

    rowElement.classList.add("active");

    setDetailText("detail-username", user.username || "--");
    setDetailText("detail-nickname", user.nickname || "--");
    setDetailText("detail-role", user.role || "--");
    setDetailText("detail-group", user.group_name || "--");
    setDetailText("detail-created-at", user.created_at || "--");
    setDetailText("detail-status", isUserActive(user)
        ? t("accountEnabled") : t("accountDisabled")
);

    loadUserGroupsToSelect(user);
    loadRoleToSelect(user);
    updateResetPasswordState(user);
    updateUserStatusPanel(user);
}


function loadUserGroupsToSelect(user) {
    const groupSelect =
        document.getElementById("edit-group-id");

    groupSelect.innerHTML = "";

    const option =
        document.createElement("option");

    option.value =
        user.group_id;

    option.textContent =
        user.group_name || "--";

    groupSelect.appendChild(option);

    groupSelect.value =
        String(user.group_id);
}


function loadRoleToSelect(user) {
    const roleSelect =
        document.getElementById("edit-role");

    const groupSelect =
        document.getElementById("edit-group-id");

    const updateButton =
        document.getElementById("update-user-button");

    const messageBox =
        document.getElementById("update-user-message");

    roleSelect.value = "";

    if (messageBox) {
        messageBox.innerText = "";
        messageBox.style.color = "#ff8a8a";
    }

    if (user.role === "admin") {
        roleSelect.disabled = true;
        groupSelect.disabled = true;

        if (updateButton) {
            updateButton.disabled = true;
        }

        if (messageBox) {
            messageBox.innerText =
                t("adminModifyForbidden");
        }

        return;
    }

    roleSelect.disabled = false;
    groupSelect.disabled = false;

    if (updateButton) {
        updateButton.disabled = false;
    }

    roleSelect.value =
        user.role || "";
}


function updateResetPasswordState(user) {
    const resetButton =
        document.getElementById("reset-password-button");

    const messageBox =
        document.getElementById("reset-password-message");

    if (messageBox) {
        messageBox.innerText = "";
        messageBox.style.color = "#ff8a8a";
    }

    if (!resetButton) {
        return;
    }

    if (user.role === "admin") {
        resetButton.disabled = true;

        if (messageBox) {
            messageBox.innerText =
                t("adminResetForbidden");
        }

        return;
    }

    resetButton.disabled = false;
}


function setDetailText(elementId, value) {
    const element =
        document.getElementById(elementId);

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


function resetSelectedUserState() {
    selectedUser = null;

    document
        .querySelectorAll("#user-table-body tr")
        .forEach(row => {
            row.classList.remove("active");
        });

    setDetailText("detail-username", "--");
    setDetailText("detail-nickname", "--");
    setDetailText("detail-role", "--");
    setDetailText("detail-group", "--");
    setDetailText("detail-created-at", "--");
    setDetailText("detail-status", "--");

    resetUserEditForm();
    resetPasswordPanelState();
    resetUserStatusPanel();
}


function refreshSelectedUserLanguage() {
    if (!selectedUser) {
        resetSelectedUserState();
        return;
    }

    setDetailText(
        "detail-status",
        isUserActive(selectedUser)
            ? t("accountEnabled")
            : t("accountDisabled")
    );

    loadRoleToSelect(selectedUser);
    updateResetPasswordState(selectedUser);
    updateUserStatusPanel(selectedUser);
}
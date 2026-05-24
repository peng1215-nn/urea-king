let pendingStatusUser = null;


function isUserActive(user) {
    return (
        user.is_active === 1 ||
        user.is_active === true ||
        user.is_active === "1" ||
        user.is_active === "true"
    );
}


function updateUserStatusPanel(user) {
    const statusText =
        document.getElementById("selected-user-status");

    const statusButton =
        document.getElementById("toggle-user-status-button");

    const messageBox =
        document.getElementById("user-status-message");

    if (messageBox) {
        messageBox.innerText = "";
        messageBox.style.color = "#ff8a8a";
    }

    if (user.role === "admin") {
        statusText.innerText = t("accountEnabled");
        statusButton.innerText = t("disableAccount");
        statusButton.disabled = true;

        if (messageBox) {
            messageBox.innerText =
                t("adminDisableForbidden");
        }

        return;
    }

    statusButton.disabled = false;

    if (isUserActive(user)) {
        statusText.innerText =
            t("accountEnabled");

        statusButton.innerText =
            t("disableAccount");
    } else {
        statusText.innerText =
            t("accountDisabled");

        statusButton.innerText =
            t("enableAccount");
    }
}


function resetUserStatusPanel() {
    const statusText =
        document.getElementById("selected-user-status");

    const statusButton =
        document.getElementById("toggle-user-status-button");

    const messageBox =
        document.getElementById("user-status-message");

    statusText.innerText = "--";

    statusButton.innerText =
        t("disableAccount");

    statusButton.disabled = false;

    if (messageBox) {
        messageBox.innerText = "";
        messageBox.style.color = "#ff8a8a";
    }
}


function openToggleUserStatusModal() {
    const messageBox =
        document.getElementById("user-status-message");

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    if (!selectedUser) {
        messageBox.innerText =
            t("pleaseSelectUser");

        return;
    }

    if (selectedUser.role === "admin") {
        messageBox.innerText =
            t("adminDisableForbidden");

        return;
    }

    pendingStatusUser = selectedUser;

    const modal =
        document.getElementById("user-status-modal");

    const text =
        document.getElementById("user-status-text");

    const actionPrefix =
        isUserActive(selectedUser)
            ? t("confirmDisableAccountPrefix")
            : t("confirmEnableAccountPrefix");

    text.innerText =
        `${actionPrefix} ${selectedUser.username}${t("accountSuffix")}`;

    modal.classList.remove("hidden");
}


function closeUserStatusModal() {
    const modal =
        document.getElementById("user-status-modal");

    modal.classList.add("hidden");

    pendingStatusUser = null;
}


async function confirmToggleUserStatus() {
    const messageBox =
        document.getElementById("user-status-message");

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    if (!pendingStatusUser) {
        closeUserStatusModal();
        return;
    }

    const formData = new FormData();

    formData.append(
        "target_user_id",
        pendingStatusUser.id
    );

    try {
        const response = await fetch(
            "/admin/toggle-user-active",
            {
                method: "POST",
                body: formData,
            }
        );

        const data = await response.json();

        if (!data.success) {
            messageBox.innerText =
                data.message || t("operationFailed");

            closeUserStatusModal();

            return;
        }

        await loadUsers();

        resetSelectedUserState();

        messageBox.style.color =
            "#5CFFB2";

        messageBox.innerText =
            data.message || t("operationSuccess");

        closeUserStatusModal();

    } catch (error) {
        console.error(error);

        messageBox.innerText =
            t("operationFailed");

        closeUserStatusModal();
    }
}
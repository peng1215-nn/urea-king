let pendingResetUser = null;


function openResetPasswordModal() {
    const messageBox =
        document.getElementById("reset-password-message");

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    if (!selectedUser) {
        messageBox.innerText =
            t("pleaseSelectUser");

        return;
    }

    if (selectedUser.role === "admin") {
        messageBox.innerText =
            t("adminResetForbidden");

        return;
    }

    pendingResetUser = selectedUser;

    const modal =
        document.getElementById("password-reset-modal");

    const text =
        document.getElementById("password-reset-text");

    text.innerText =
        t("passwordResetConfirmText").replace("{username}", selectedUser.username
);

    modal.classList.remove("hidden");
}


function closeResetPasswordModal() {
    const modal =
        document.getElementById("password-reset-modal");

    modal.classList.add("hidden");

    pendingResetUser = null;
}


async function confirmResetPassword() {
    const messageBox =
        document.getElementById("reset-password-message");

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    if (!pendingResetUser) {
        closeResetPasswordModal();
        return;
    }

    if (pendingResetUser.role === "admin") {
        messageBox.innerText =
            t("adminResetForbidden");

        closeResetPasswordModal();

        return;
    }

    const formData =
        new FormData();

    formData.append(
        "target_user_id",
        pendingResetUser.id
    );

    try {
        const response = await fetch(
            "/admin/reset-user-password",
            {
                method: "POST",
                body: formData,
            }
        );

        const data =
            await response.json();

        if (!data.success) {
            messageBox.innerText =
                data.message || t("passwordResetFailed");

            closeResetPasswordModal();

            return;
        }

        messageBox.style.color =
            "#5CFFB2";

        messageBox.innerText =
            t("passwordResetSuccess");

        closeResetPasswordModal();

        await loadUsers();

        resetSelectedUserState();

    } catch (error) {
        console.error(error);

        messageBox.innerText =
             t("passwordResetFailed");

        closeResetPasswordModal();
    }
}


function resetPasswordPanelState() {
    const resetButton =
        document.getElementById("reset-password-button");

    if (resetButton) {
        resetButton.disabled = false;
    }

    document
        .querySelectorAll("#user-table-body tr")
        .forEach(row => {
            row.classList.remove("active");
        });
}
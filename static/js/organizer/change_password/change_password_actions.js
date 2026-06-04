async function loadCurrentAccount() {
    const messageBox = document.getElementById("nickname-message");

    try {
        const data = await fetchCurrentAccount();

        if (!data.success) {
            messageBox.innerText = t(data.message || "operationFailed");
            return;
        }

        document.getElementById("current-nickname").innerText =
            data.user.nickname || "--";

        document.getElementById("new-nickname").value = "";

    } catch (error) {
        console.error(error);
        messageBox.innerText = t("operationFailed");
    }
}

async function updateNickname() {
    const nickname = document.getElementById("new-nickname").value.trim();
    const messageBox = document.getElementById("nickname-message");

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    if (!nickname) {
        messageBox.innerText = t("nicknameRequired");
        return;
    }

    try {
        const data = await updateNicknameApi(nickname);

        if (!data.success) {
            messageBox.innerText = t(data.message || "operationFailed");
            return;
        }

        messageBox.style.color = "#5CFFB2";
        messageBox.innerText = t("nicknameUpdateSuccess");

        document.getElementById("current-nickname").innerText = data.nickname;
        document.getElementById("new-nickname").value = "";

    } catch (error) {
        console.error(error);
        messageBox.innerText = t("operationFailed");
    }
}

async function updatePassword() {
    const currentPassword = document.getElementById("current-password").value;
    const newPassword = document.getElementById("new-password").value;
    const confirmPassword = document.getElementById("confirm-password").value;
    const messageBox = document.getElementById("password-message");

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    if (!currentPassword) {
        messageBox.innerText = t("currentPasswordRequired");
        return;
    }

    if (!newPassword) {
        messageBox.innerText = t("newPasswordRequired");
        return;
    }

    if (!confirmPassword) {
        messageBox.innerText = t("confirmNewPasswordRequired");
        return;
    }

    try {
        const data = await updatePasswordApi(currentPassword, newPassword, confirmPassword);

        if (!data.success) {
            messageBox.innerText = t(data.message || "operationFailed");
            return;
        }

        messageBox.style.color = "#5CFFB2";
        messageBox.innerText = t("passwordUpdateSuccessLogout");

        setTimeout(() => { window.location.href = "/login"; }, 1000);

    } catch (error) {
        console.error(error);
        messageBox.innerText = t("operationFailed");
    }
}
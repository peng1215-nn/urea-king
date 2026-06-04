async function saveNickname() {
    const messageBox = document.getElementById("nickname-message");
    messageBox.style.color = "#ff8a8a";
    messageBox.innerText = "";

    const nickname = document.getElementById("new-nickname").value.trim();
    if (!nickname) { messageBox.innerText = t("nicknameRequired"); return; }
    if (nickname.length > 50) { messageBox.innerText = t("nicknameTooLong"); return; }

    const data = await apiUpdateNickname(nickname);

    if (!data.success) {
        messageBox.innerText = t(data.message || "operationFailed");
        return;
    }

    messageBox.style.color = "#5CFFB2";
    messageBox.innerText = t("nicknameUpdateSuccess");
    document.getElementById("current-nickname").value = nickname;
    document.getElementById("new-nickname").value = "";
}

async function savePassword() {
    const messageBox = document.getElementById("password-message");
    messageBox.style.color = "#ff8a8a";
    messageBox.innerText = "";

    const current = document.getElementById("current-password").value;
    const newPwd = document.getElementById("new-password").value;
    const confirm = document.getElementById("confirm-password").value;

    if (!current) { messageBox.innerText = t("currentPasswordRequired"); return; }
    if (!newPwd) { messageBox.innerText = t("newPasswordRequired"); return; }
    if (newPwd.length < 6) { messageBox.innerText = t("newPasswordTooShort"); return; }
    if (newPwd !== confirm) { messageBox.innerText = t("newPasswordMismatch"); return; }

    const data = await apiUpdatePassword(current, newPwd, confirm);

    if (!data.success) {
        messageBox.innerText = t(data.message || "operationFailed");
        return;
    }

    messageBox.style.color = "#5CFFB2";
    messageBox.innerText = t("passwordUpdateSuccessLogout");
    setTimeout(() => { window.location.href = "/login"; }, 1500);
}
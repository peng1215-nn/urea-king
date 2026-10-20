function setMsg(id, text, type) {
    const el = document.getElementById(id);
    el.className = "operation-message" + (type ? " " + type : "");
    el.innerText = text;
}

async function saveNickname() {
    setMsg("nickname-message", "", "");

    const nickname = document.getElementById("new-nickname").value.trim();

    if (!nickname) {
        setMsg("nickname-message", t("nicknameRequired"), "error");
        return;
    }

    if (nickname.length > 50) {
        setMsg("nickname-message", t("nicknameTooLong"), "error");
        return;
    }

    try {
        const data = await apiUpdateNickname(nickname);

        if (!data.success) {
            setMsg("nickname-message", t(data.message || "operationFailed"), "error");
            return;
        }

        setMsg("nickname-message", t("nicknameUpdateSuccess"), "success");

        document.getElementById("current-nickname").value = data.nickname || nickname;
        document.getElementById("new-nickname").value = "";

    } catch (error) {
        console.error(error);
        setMsg("nickname-message", t("operationFailed"), "error");
    }
}


async function savePassword() {
    setMsg("password-message", "", "");

    const current = document.getElementById("current-password").value;
    const newPwd = document.getElementById("new-password").value;
    const confirm = document.getElementById("confirm-password").value;

    if (!current) {
        setMsg("password-message", t("currentPasswordRequired"), "error");
        return;
    }

    if (!newPwd) {
        setMsg("password-message", t("newPasswordRequired"), "error");
        return;
    }

    if (newPwd.length < 6) {
        setMsg("password-message", t("newPasswordTooShort"), "error");
        return;
    }

    if (newPwd !== confirm) {
        setMsg("password-message", t("newPasswordMismatch"), "error");
        return;
    }

    try {
        const data = await apiUpdatePassword(current, newPwd, confirm);

        if (!data.success) {
            setMsg("password-message", t(data.message || "operationFailed"), "error");
            return;
        }

        setMsg("password-message", t("passwordUpdateSuccessLogout"), "success");

        setTimeout(() => { window.location.href = "/login"; }, 1500);

    } catch (error) {
        console.error(error);
        setMsg("password-message", t("operationFailed"), "error");
    }
}

async function groupJoin() {
    const usernameEl = document.getElementById("username");
    const passwordEl = document.getElementById("password");
    const isLoggedIn = !usernameEl; // 已登录时账号密码字段不存在

    const inviteCode =
        document.getElementById("invite-code")
            .value
            .trim();

    const messageBox =
        document.getElementById("message-box");

    messageBox.innerText = "";
    messageBox.style.color = "#ff7b7b";

    if (!isLoggedIn) {
        const username = usernameEl.value.trim();
        const password = passwordEl.value;

        if (!username) {
            messageBox.innerText = t("groupJoinUsernameRequired");
            return;
        }
        if (!password) {
            messageBox.innerText = t("groupJoinPasswordRequired");
            return;
        }
    }

    if (!inviteCode) {
        messageBox.innerText =
            t("groupJoinInviteCodeRequired");

        return;
    }

    const formData = new FormData();

    if (!isLoggedIn) {
        formData.append("username", usernameEl.value.trim());
        formData.append("password", passwordEl.value);
    }
    formData.append("invite_code", inviteCode);

    try {
        const response = await fetch(
            "/group-join",
            {
                method: "POST",
                body: formData,
            }
        );

        const data =
            await response.json();

        if (!data.success) {
            console.log(data);

            messageBox.innerText =
                t(data.message || "groupJoinFailed");

            return;
        }

        messageBox.style.color = "#5cffb2";

        messageBox.innerText =
            t("groupJoinSuccess");

        setTimeout(
            function () {
                window.location.href = isLoggedIn ? "/group-select" : "/login";
            },
            1400
        );

    } catch (error) {
        console.error(error);

        messageBox.innerText =
            t("groupJoinFailed");
    }
}


document.addEventListener(
    "DOMContentLoaded",
    function () {
        applyLanguage();
    }
);
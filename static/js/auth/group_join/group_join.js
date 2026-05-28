async function groupJoin() {
    const username =
        document.getElementById("username")
            .value
            .trim();

    const password =
        document.getElementById("password")
            .value;

    const inviteCode =
        document.getElementById("invite-code")
            .value
            .trim();

    const messageBox =
        document.getElementById("message-box");

    messageBox.innerText = "";
    messageBox.style.color = "#ff7b7b";

    if (!username) {
        messageBox.innerText =
            t("groupJoinUsernameRequired");

        return;
    }

    if (!password) {
        messageBox.innerText =
            t("groupJoinPasswordRequired");

        return;
    }

    if (!inviteCode) {
        messageBox.innerText =
            t("groupJoinInviteCodeRequired");

        return;
    }

    const formData = new FormData();

    formData.append("username", username);
    formData.append("password", password);
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
                window.location.href = "/login";
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
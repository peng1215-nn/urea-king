let groupJoinSubmitting = false;

async function groupJoin() {
    if (groupJoinSubmitting) {
        return;
    }

    const usernameEl = document.getElementById("username");
    const passwordEl = document.getElementById("password");
    const isLoggedIn = !usernameEl; // 已登录时账号密码字段不存在

    const inviteCode =
        document.getElementById("invite-code")
            .value
            .trim();

    const messageBox =
        document.getElementById("message-box");

    const button =
        document.getElementById("group-join-button");

    messageBox.innerText = "";
    messageBox.style.color = "#ff7b7b";

    if (!isLoggedIn) {
        const username = usernameEl.value.trim();
        const password = passwordEl.value;

        if (!username) {
            messageBox.innerText = t("groupJoinUsernameRequired");
            authFocus("username");
            return;
        }
        if (!password) {
            messageBox.innerText = t("groupJoinPasswordRequired");
            authFocus("password");
            return;
        }
    }

    if (!inviteCode) {
        messageBox.innerText =
            t("groupJoinInviteCodeRequired");
        authFocus("invite-code");

        return;
    }

    const formData = new FormData();

    if (!isLoggedIn) {
        formData.append("username", usernameEl.value.trim());
        formData.append("password", passwordEl.value);
    }
    formData.append("invite_code", inviteCode);

    let redirecting = false;

    groupJoinSubmitting = true;
    authSetBusy(button, true);

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
            // /group-join 登录失效时也能打开：服务端会清掉过期的登录，再按未登录处理，
            // 所以这里收到“请输入用户名”也说明登录已过期
            if (
                isLoggedIn
                && (authIsSessionExpired(data) || data.message === "groupJoinUsernameRequired")
            ) {
                redirecting = true;
                authRedirectExpired();
                return;
            }

            const code = data.message || data.error_code || "groupJoinFailed";

            messageBox.innerText = authMessage(code, data);

            if (code === "groupJoinEmailNotVerified") {
                const link = document.createElement("a");
                link.className = "message-action-link";
                link.href = "/register#resend";
                link.textContent = t("resendVerifyLink");
                messageBox.appendChild(document.createElement("br"));
                messageBox.appendChild(link);
            }

            return;
        }

        messageBox.style.color = "#5cffb2";

        messageBox.innerText = authFormat(
            t(isLoggedIn ? "groupJoinSuccessLoggedIn" : "groupJoinSuccess"),
            { group: data.group_name || "" }
        );

        redirecting = true;

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

    } finally {
        if (!redirecting) {
            groupJoinSubmitting = false;
            authSetBusy(button, false);
        }
    }
}


authBindSubmit("group-join-form", groupJoin);

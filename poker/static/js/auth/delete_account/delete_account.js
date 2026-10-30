let deleteAccountSubmitting = false;

// 登录页的注销账号。规则由后端判断，这里只做必填校验和结果展示。
async function deleteAccount() {
    if (deleteAccountSubmitting) {
        return;
    }

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const confirmText = document.getElementById("confirm-text").value.trim();
    const messageBox = document.getElementById("message-box");
    const button = document.getElementById("delete-account-button");

    messageBox.innerText = "";
    messageBox.style.color = "#ff7b7b";

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

    const word = confirmText.toLowerCase();
    if (word !== "注销" && word !== "delete") {
        messageBox.innerText = t("accountDeleteConfirmMismatch");
        authFocus("confirm-text");
        return;
    }

    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);
    formData.append("confirm_text", confirmText);

    let redirecting = false;

    deleteAccountSubmitting = true;
    authSetBusy(button, true);

    try {
        const response = await fetch("/account/delete", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (!data.success) {
            if (authIsSessionExpired(data)) {
                redirecting = true;
                authRedirectExpired();
                return;
            }

            // innerText 不解析 HTML，组名直接替换进去是安全的
            messageBox.innerText = authFormat(
                authMessage(data.message || data.error_code || "accountDeleteFailed", data),
                { group: data.group_name || "" }
            );
            return;
        }

        messageBox.style.color = "#5cffb2";
        messageBox.innerText = t("accountDeleteSuccess");
        redirecting = true;

        setTimeout(function () {
            window.location.href = "/login";
        }, 1800);

    } catch (error) {
        console.error(error);
        messageBox.innerText = t("accountDeleteFailed");

    } finally {
        if (!redirecting) {
            deleteAccountSubmitting = false;
            authSetBusy(button, false);
        }
    }
}


authBindSubmit("delete-account-form", deleteAccount);

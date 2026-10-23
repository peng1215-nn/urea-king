// 登录页的注销账号。规则由后端判断，这里只做必填校验和结果展示。
async function deleteAccount() {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const confirmText = document.getElementById("confirm-text").value.trim();
    const messageBox = document.getElementById("message-box");
    const button = document.getElementById("delete-account-button");

    messageBox.innerText = "";
    messageBox.style.color = "#ff7b7b";

    if (!username) {
        messageBox.innerText = t("groupJoinUsernameRequired");
        return;
    }

    if (!password) {
        messageBox.innerText = t("groupJoinPasswordRequired");
        return;
    }

    const word = confirmText.toLowerCase();
    if (word !== "注销" && word !== "delete") {
        messageBox.innerText = t("accountDeleteConfirmMismatch");
        return;
    }

    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);
    formData.append("confirm_text", confirmText);

    button.disabled = true;

    try {
        const response = await fetch("/account/delete", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (!data.success) {
            // innerText 不解析 HTML，组名直接替换进去是安全的
            messageBox.innerText = t(data.message || "accountDeleteFailed")
                .replace("{group}", data.group_name || "");
            button.disabled = false;
            return;
        }

        messageBox.style.color = "#5cffb2";
        messageBox.innerText = t("accountDeleteSuccess");

        setTimeout(function () {
            window.location.href = "/login";
        }, 1800);

    } catch (error) {
        console.error(error);
        messageBox.innerText = t("accountDeleteFailed");
        button.disabled = false;
    }
}


document.addEventListener("DOMContentLoaded", function () {
    applyLanguage();
});

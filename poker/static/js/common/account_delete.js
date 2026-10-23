/**
 * account_delete.js — 局头和普通用户的“注销账号”。
 * 需要页面上有 #delete-account-modal 及其中的输入框；文案来自各角色的 i18n 文件。
 */
function openDeleteAccountModal() {
    document.getElementById("delete-account-password").value = "";
    document.getElementById("delete-account-confirm").value = "";
    document.getElementById("delete-account-message").innerText = "";
    document.getElementById("delete-account-submit").disabled = false;
    document.getElementById("delete-account-modal").style.display = "flex";
    document.getElementById("delete-account-password").focus();
}


function closeDeleteAccountModal() {
    document.getElementById("delete-account-modal").style.display = "none";
}


function deleteAccountMessage(data) {
    const text = t(data.message || "operationFailed");

    if (data.message === "accountDeleteGroupHasMembers") {
        return text.replace("{group}", data.group_name || "");
    }

    return text;
}


async function confirmDeleteAccount() {
    const messageBox = document.getElementById("delete-account-message");
    const submit = document.getElementById("delete-account-submit");
    const password = document.getElementById("delete-account-password").value;
    const confirmText = document.getElementById("delete-account-confirm").value.trim();

    messageBox.style.color = "#ff8a8a";

    if (!password) {
        messageBox.innerText = t("currentPasswordRequired");
        return;
    }

    if (!confirmText) {
        messageBox.innerText = t("accountDeleteConfirmMismatch");
        return;
    }

    const formData = new FormData();
    formData.append("password", password);
    formData.append("confirm_text", confirmText);

    submit.disabled = true;

    try {
        const response = await fetch("/account/delete", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (!data.success) {
            messageBox.innerText = deleteAccountMessage(data);
            submit.disabled = false;
            return;
        }

        messageBox.style.color = "#5CFFB2";
        messageBox.innerText = t("accountDeleted");

        setTimeout(() => {
            window.location.href = "/login";
        }, 1500);

    } catch (error) {
        console.error(error);
        messageBox.innerText = t("operationFailed");
        submit.disabled = false;
    }
}

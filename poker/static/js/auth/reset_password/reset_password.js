// 这些错误说明链接本身已失效，需要重新申请
const RESET_LINK_ERRORS = ["resetTokenInvalid", "resetTokenUsed", "resetTokenExpired", "resetInvalidLink"];

let resetSubmitting = false;

async function resetPassword() {
    if (resetSubmitting) {
        return;
    }

    const msgBox = document.getElementById("message-box");
    const btn = document.getElementById("rp-btn");
    const newPwd = document.getElementById("new-password").value;
    const confirmPwd = document.getElementById("confirm-password").value;

    const RESET_TOKEN = btn.dataset.token || "";

    if (!RESET_TOKEN) {
        msgBox.textContent = t("resetInvalidLink");
        msgBox.style.color = "#e55";
        showRequestNewLink();
        return;
    }

    if (newPwd.length < 8) {
        msgBox.textContent = t("resetPasswordTooShort");
        msgBox.style.color = "#e55";
        authFocus("new-password");
        return;
    }

    if (newPwd !== confirmPwd) {
        msgBox.textContent = t("resetPasswordMismatch");
        msgBox.style.color = "#e55";
        authFocus("confirm-password");
        return;
    }

    resetSubmitting = true;
    authSetBusy(btn, true, "resetting");

    try {
        const fd = new FormData();
        fd.append("token", RESET_TOKEN);
        fd.append("new_password", newPwd);
        fd.append("confirm_password", confirmPwd);

        const res = await fetch("/reset-password", { method: "POST", body: fd });
        const data = await res.json();

        if (data.success) {
            msgBox.textContent = t("resetSuccessMsg");
            msgBox.style.color = "#5c5";
            document.getElementById("reset-form").style.display = "none";
        } else {
            msgBox.textContent = authMessage(data.error_code || "resetFailed", data);
            msgBox.style.color = "#e55";
            if (RESET_LINK_ERRORS.includes(data.error_code)) {
                showRequestNewLink();
            }
        }
    } catch (e) {
        msgBox.textContent = t("requestFailed");
        msgBox.style.color = "#e55";
    } finally {
        resetSubmitting = false;
        authSetBusy(btn, false);
    }
}


function showRequestNewLink() {
    const link = document.getElementById("request-new-link");
    if (link) {
        link.hidden = false;
    }
}


authBindSubmit("reset-form", resetPassword);

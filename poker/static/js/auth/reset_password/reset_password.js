async function resetPassword() {
    const msgBox = document.getElementById("message-box");
    const btn = document.getElementById("rp-btn");
    const newPwd = document.getElementById("new-password").value;
    const confirmPwd = document.getElementById("confirm-password").value;

    const RESET_TOKEN = btn.dataset.token || "";

    if (!RESET_TOKEN) {
        msgBox.textContent = t("resetInvalidLink");
        msgBox.style.color = "#e55";
        return;
    }

    btn.disabled = true;
    btn.textContent = t("resetting");

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
            msgBox.textContent = t(data.error_code) || t("resetFailed");
            msgBox.style.color = "#e55";
            btn.disabled = false;
            btn.textContent = t("resetPasswordBtn");
        }
    } catch (e) {
        msgBox.textContent = t("requestFailed");
        msgBox.style.color = "#e55";
        btn.disabled = false;
        btn.textContent = t("resetPasswordBtn");
    }
}

document.getElementById("rp-btn").addEventListener("click", resetPassword);

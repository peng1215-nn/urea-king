const ERROR_MESSAGES = {
    resetPasswordMismatch: "两次输入的密码不一致。",
    resetPasswordTooShort: "密码长度至少为 8 位。",
    resetPasswordTooLong: "密码不能超过 128 位。",
    resetTokenInvalid: "重置链接无效，请重新申请。",
    resetTokenUsed: "该重置链接已使用，请重新申请。",
    resetTokenExpired: "重置链接已过期，请重新申请。",
    resetFailed: "重置失败，请稍后重试。",
};

async function resetPassword() {
    const msgBox = document.getElementById("message-box");
    const btn = document.getElementById("rp-btn");
    const newPwd = document.getElementById("new-password").value;
    const confirmPwd = document.getElementById("confirm-password").value;

    // 从 data attribute 读取 token（避免 inline script CSP 问题）
    const RESET_TOKEN = document.getElementById("rp-btn").dataset.token || "";

    if (!RESET_TOKEN) {
        msgBox.textContent = "无效的重置链接，请从邮件中点击链接进入。";
        msgBox.style.color = "#e55";
        return;
    }

    btn.disabled = true;
    btn.textContent = "重置中…";

    try {
        const fd = new FormData();
        fd.append("token", RESET_TOKEN);
        fd.append("new_password", newPwd);
        fd.append("confirm_password", confirmPwd);

        const res = await fetch("/reset-password", { method: "POST", body: fd });
        const data = await res.json();

        if (data.success) {
            msgBox.textContent = "密码重置成功！请使用新密码登录。";
            msgBox.style.color = "#5c5";
            document.getElementById("reset-form").style.display = "none";
        } else {
            msgBox.textContent = ERROR_MESSAGES[data.error_code] || "重置失败，请稍后重试。";
            msgBox.style.color = "#e55";
            btn.disabled = false;
            btn.textContent = "重置密码";
        }
    } catch (e) {
        msgBox.textContent = "请求失败，请稍后重试。";
        msgBox.style.color = "#e55";
        btn.disabled = false;
        btn.textContent = "重置密码";
    }
}

document.getElementById("rp-btn").addEventListener("click", resetPassword);

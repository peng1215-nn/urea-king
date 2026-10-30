async function sendForgotPassword() {
    const lang = localStorage.getItem("language") || "zh";
    const t = (window.forgotPasswordTranslations || {})[lang] || (window.forgotPasswordTranslations || {}).zh || {};

    const email = document.getElementById("fp-email").value.trim();
    const msgBox = document.getElementById("message-box");
    const btn = document.getElementById("fp-btn");

    if (!email) {
        msgBox.textContent = t.emailRequired || "请输入邮箱地址。";
        msgBox.style.color = "#e55";
        return;
    }

    btn.disabled = true;
    btn.textContent = t.sending || "发送中…";

    try {
        const fd = new FormData();
        fd.append("email", email);
        const res = await fetch("/forgot-password", { method: "POST", body: fd });
        const data = await res.json();

        if (!data.success) {
            if (data.error_code === "forgotPasswordTooManyAttempts") {
                msgBox.textContent = t.forgotPasswordTooManyAttempts || "尝试次数过多，请 15 分钟后再试。";
                msgBox.style.color = "#e55";
                btn.disabled = false;
                btn.textContent = t.sendBtn || "发送重置邮件";
            } else if (data.error_code === "resetTooFrequent") {
                const wait = Math.ceil((data.wait_seconds || 300) / 60);
                const msg = (t.resetTooFrequent || "请 {wait} 分钟后再试。").replace("{wait}", wait);
                msgBox.textContent = msg;
                msgBox.style.color = "#e55";
                btn.disabled = false;
                btn.textContent = t.sendBtn || "发送重置邮件";
            } else if (data.error_code === "resetDailyLimit") {
                msgBox.textContent = t.resetDailyLimit || "今日发送次数已达上限，请明天再试。";
                msgBox.style.color = "#e55";
                btn.disabled = false;
                btn.textContent = t.sendBtn || "发送重置邮件";
            } else {
                // 其他错误显示通用提示（防枚举）
                msgBox.textContent = t.resetSuccess || "如果该邮箱已注册，重置链接已发送，请查收邮件。";
                msgBox.style.color = "#5c5";
                btn.style.display = "none";
            }
        } else {
            // 成功或邮箱不存在都显示同一提示（防枚举）
            msgBox.textContent = t.resetSuccess || "如果该邮箱已注册，重置链接已发送，请查收邮件。";
            msgBox.style.color = "#5c5";
            btn.style.display = "none";
        }
    } catch (e) {
        msgBox.textContent = t.requestFailed || "请求失败，请稍后重试。";
        msgBox.style.color = "#e55";
        btn.disabled = false;
        btn.textContent = t.sendBtn || "发送重置邮件";
    }
}

document.getElementById("fp-btn").addEventListener("click", sendForgotPassword);

async function sendForgotPassword() {
    const email = document.getElementById("fp-email").value.trim();
    const msgBox = document.getElementById("message-box");
    const btn = document.getElementById("fp-btn");

    if (!email) {
        msgBox.textContent = "请输入邮箱地址。";
        msgBox.style.color = "#e55";
        return;
    }

    btn.disabled = true;
    btn.textContent = "发送中…";

    try {
        const fd = new FormData();
        fd.append("email", email);
        const res = await fetch("/forgot-password", { method: "POST", body: fd });
        await res.json();

        // 无论成功失败都显示同一提示（防枚举）
        msgBox.textContent = "如果该邮箱已注册，重置链接已发送，请查收邮件。链接 15 分钟内有效。";
        msgBox.style.color = "#5c5";
        btn.style.display = "none";
    } catch (e) {
        msgBox.textContent = "请求失败，请稍后重试。";
        msgBox.style.color = "#e55";
        btn.disabled = false;
        btn.textContent = "发送重置邮件";
    }
}

document.getElementById("fp-btn").addEventListener("click", sendForgotPassword);

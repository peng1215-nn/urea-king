// 发送后按钮保留，60 秒后可以再发一次（服务端另有频率限制）
const FORGOT_COOLDOWN_SECONDS = 60;

let forgotSending = false;
let forgotCooldownLeft = 0;
let forgotCooldownTimer = null;
// 记住最后一条提示，切换语言时重新翻译
let forgotLastMessage = null;


function renderForgotMessage() {
    const msgBox = document.getElementById("message-box");

    if (!forgotLastMessage) {
        msgBox.textContent = "";
        return;
    }

    msgBox.textContent = authMessage(forgotLastMessage.key, forgotLastMessage.data);
    msgBox.style.color = forgotLastMessage.success ? "#5c5" : "#e55";
}


function setForgotMessage(key, success, data) {
    forgotLastMessage = { key, success, data };
    renderForgotMessage();
}


function renderForgotButton() {
    const btn = document.getElementById("fp-btn");

    if (forgotSending) {
        btn.disabled = true;
        btn.textContent = t("sending");
        return;
    }

    if (forgotCooldownLeft > 0) {
        btn.disabled = true;
        btn.textContent = authFormat(t("resendCountdown"), { seconds: forgotCooldownLeft });
        return;
    }

    btn.disabled = false;
    btn.textContent = t("sendBtn");
}


function startForgotCooldown() {
    forgotCooldownLeft = FORGOT_COOLDOWN_SECONDS;
    clearInterval(forgotCooldownTimer);

    forgotCooldownTimer = setInterval(() => {
        forgotCooldownLeft -= 1;
        if (forgotCooldownLeft <= 0) {
            forgotCooldownLeft = 0;
            clearInterval(forgotCooldownTimer);
        }
        renderForgotButton();
    }, 1000);

    renderForgotButton();
}


async function sendForgotPassword() {
    if (forgotSending || forgotCooldownLeft > 0) {
        return;
    }

    const email = document.getElementById("fp-email").value.trim();

    if (!email) {
        setForgotMessage("emailRequired", false);
        authFocus("fp-email");
        return;
    }

    forgotSending = true;
    renderForgotButton();

    let cooldown = false;

    try {
        const fd = new FormData();
        fd.append("email", email);
        const res = await fetch("/forgot-password", { method: "POST", body: fd });
        const data = await res.json();

        if (!data.success && data.error_code === "forgotPasswordTooManyAttempts") {
            setForgotMessage("forgotPasswordTooManyAttempts", false, data);
        } else {
            // 成功、邮箱不存在或其他错误都显示同一提示（防枚举）
            setForgotMessage("resetSuccess", true);
            cooldown = true;
        }
    } catch (e) {
        setForgotMessage("requestFailed", false);
    } finally {
        forgotSending = false;
        if (cooldown) {
            startForgotCooldown();
        } else {
            renderForgotButton();
        }
    }
}


authBindSubmit("fp-form", sendForgotPassword);

document.addEventListener("languageChanged", function () {
    renderForgotMessage();
    renderForgotButton();
});

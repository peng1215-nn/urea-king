/*
 * 个人资料页“更换邮箱”卡片（user / organizer / admin 共用）。
 * 文字来自 i18n/account_email.js，按 language.js 的当前语言显示，切换语言时跟着更新。
 */
(function () {
    const card = document.getElementById("account-email-card");
    if (!card) return;

    let state = { email: "", pending_email: "" };
    let lastMessage = null; // { key, vars, type }，切换语言后重新翻译

    function lang() {
        return typeof getCurrentLanguage === "function" ? getCurrentLanguage() : "zh";
    }

    function ae(key, vars) {
        const map = (window.accountEmailTranslations || {})[lang()] || {};
        let text = map[key];
        if (text === undefined) text = typeof t === "function" ? t(key) : key;
        Object.entries(vars || {}).forEach(([name, value]) => {
            text = String(text).split(`{${name}}`).join(String(value));
        });
        return text;
    }

    function minutes(data) {
        const seconds = Number(data && data.retry_after);
        return Number.isFinite(seconds) && seconds > 0 ? Math.max(1, Math.ceil(seconds / 60)) : 15;
    }

    function showMessage(key, vars, type) {
        lastMessage = key ? { key, vars, type } : null;
        const box = document.getElementById("ae-message");
        box.innerText = key ? ae(key, vars) : "";
        box.style.color = type === "success" ? "#5cffb2" : "#ff8a8a";
    }

    function applyTexts() {
        card.querySelectorAll("[data-ae]").forEach(el => {
            el.innerText = ae(el.getAttribute("data-ae"));
        });
        document.getElementById("ae-new-email").placeholder = ae("aeNewEmailPlaceholder");
        document.getElementById("ae-password").placeholder = ae("aePasswordPlaceholder");
        render();
        if (lastMessage) showMessage(lastMessage.key, lastMessage.vars, lastMessage.type);
    }

    function render() {
        document.getElementById("ae-current-email").value = state.email || "";
        const pending = document.getElementById("ae-pending");
        if (state.pending_email) {
            document.getElementById("ae-pending-text").innerText = ae("aePendingText", { email: state.pending_email });
            pending.hidden = false;
        } else {
            pending.hidden = true;
        }
    }

    async function request(url, options) {
        let res;
        try {
            res = await fetch(url, options);
        } catch (error) {
            return { success: false, message: "networkError" };
        }
        if (res.status === 401) {
            window.location.href = "/login?reason=expired";
            return null;
        }
        try {
            return await res.json();
        } catch (error) {
            return { success: false, message: "operationFailed" };
        }
    }

    async function load() {
        const data = await request("/account/email");
        if (data && data.success) {
            state = { email: data.email || "", pending_email: data.pending_email || "" };
            render();
        }
    }

    async function submit() {
        const emailInput = document.getElementById("ae-new-email");
        const passwordInput = document.getElementById("ae-password");
        const newEmail = emailInput.value.trim();
        const password = passwordInput.value;

        if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(newEmail)) {
            showMessage("accountEmailInvalid", null, "error");
            emailInput.focus();
            return;
        }
        if (!password) {
            showMessage("accountEmailPasswordRequired", null, "error");
            passwordInput.focus();
            return;
        }

        const button = document.getElementById("ae-submit");
        if (button.disabled) return;
        button.disabled = true;
        button.innerText = ae("aeSending");

        const fd = new FormData();
        fd.append("new_email", newEmail);
        fd.append("current_password", password);
        const data = await request("/account/change-email", { method: "POST", body: fd });

        button.disabled = false;
        button.innerText = ae("aeSubmit");
        if (!data) return;

        if (data.success) {
            passwordInput.value = "";
            emailInput.value = "";
            state.pending_email = data.pending_email || newEmail;
            render();
            showMessage("accountEmailSent", { email: state.pending_email }, "success");
        } else {
            if (data.message === "accountEmailWrongPassword") passwordInput.focus();
            showMessage(data.message || "operationFailed", { minutes: minutes(data) }, "error");
        }
    }

    async function cancel() {
        const data = await request("/account/change-email/cancel", { method: "POST" });
        if (!data) return;
        if (data.success) {
            state.pending_email = "";
            render();
            showMessage("accountEmailCancelled", null, "success");
        } else {
            showMessage(data.message || "operationFailed", null, "error");
        }
    }
    window.__accountEmail = { cancel };

    document.getElementById("ae-form").addEventListener("submit", function (event) {
        event.preventDefault();
        submit();
    });
    document.addEventListener("languageChanged", applyTexts);

    applyTexts();
    load();
})();

// 由 actions.js 调用（data-on-click="cancelAccountEmailChange"）
function cancelAccountEmailChange() {
    return window.__accountEmail ? window.__accountEmail.cancel() : undefined;
}

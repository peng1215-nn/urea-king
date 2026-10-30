/**
 * 修改注册邮箱面板逻辑
 * - 账号未验证时可用，需输入用户名 + 密码 + 新邮箱
 * - 5 分钟内不能重复操作
 */

(function () {
    const t = (key, vars) => {
        const lang = typeof getCurrentLanguage === "function"
            ? getCurrentLanguage()
            : (localStorage.getItem("lang") || "zh");
        const map = window.registerTranslations?.[lang] || {};
        let str = map[key] || key;
        if (vars) {
            Object.entries(vars).forEach(([k, v]) => {
                str = str.replace(`{${k}}`, v);
            });
        }
        return str;
    };

    function retryMinutes(data) {
        const seconds = Number(data && data.retry_after);
        return seconds > 0 ? Math.max(1, Math.ceil(seconds / 60)) : 15;
    }

    function buildPanel() {
        if (document.getElementById("change-email-panel")) return null;

        const panel = document.createElement("form");
        panel.id = "change-email-panel";
        panel.className = "register-panel";
        panel.noValidate = true;
        panel.hidden = true;

        panel.innerHTML = `
            <p class="register-panel-title" id="ce-title"></p>
            <input type="text"     id="ce-username" name="username" autocomplete="username"
                   autocapitalize="off" autocorrect="off" spellcheck="false">
            <input type="password" id="ce-password" name="password" autocomplete="current-password">
            <input type="email"    id="ce-new-email" name="new_email" autocomplete="email"
                   autocapitalize="off" spellcheck="false">
            <div class="register-panel-actions">
                <button type="submit" id="ce-submit" class="register-panel-submit"></button>
                <button type="button" id="ce-cancel" class="register-panel-cancel"></button>
            </div>
            <div id="ce-msg" class="register-panel-msg" role="alert" aria-live="polite"></div>
        `;

        return panel;
    }

    function initChangeEmail() {
        const trigger = document.getElementById("change-email-trigger");
        if (!trigger) return;

        const panel = buildPanel();
        if (!panel) return;
        // 插在 resend-panel 后面（如果有），否则插在 trigger 的父元素后
        const resendPanel = document.getElementById("resend-panel");
        const anchor = resendPanel || trigger.parentNode;
        anchor.insertAdjacentElement("afterend", panel);

        const titleEl       = document.getElementById("ce-title");
        const usernameInput = document.getElementById("ce-username");
        const passwordInput = document.getElementById("ce-password");
        const newEmailInput = document.getElementById("ce-new-email");
        const submitBtn    = document.getElementById("ce-submit");
        const cancelBtn    = document.getElementById("ce-cancel");
        const msgBox       = document.getElementById("ce-msg");
        let sending = false;

        function setField(input, key) {
            input.placeholder = t(key);
            input.setAttribute("aria-label", t(key));
        }

        function applyI18n() {
            titleEl.textContent = t("changeEmailTitle");
            setField(usernameInput, "changeEmailUsernamePlaceholder");
            setField(passwordInput, "changeEmailPasswordPlaceholder");
            setField(newEmailInput, "changeEmailNewPlaceholder");
            submitBtn.textContent     = sending ? t("processing") : t("changeEmailSubmit");
            cancelBtn.textContent     = t("changeEmailCancel");
        }
        applyI18n();
        document.addEventListener("languageChanged", applyI18n);

        trigger.addEventListener("click", (e) => {
            e.preventDefault();
            // 关闭重发面板（互斥）
            const rp = document.getElementById("resend-panel");
            if (rp) rp.hidden = true;
            msgBox.textContent = "";

            if (!panel.hidden) {
                panel.hidden = true;
                return;
            }

            panel.hidden = false;
            // 面板在页面底部，打开后滚到可见位置并聚焦第一个输入框
            panel.scrollIntoView({ behavior: "smooth", block: "center" });
            usernameInput.focus({ preventScroll: true });
        });

        cancelBtn.addEventListener("click", () => {
            panel.hidden = true;
            msgBox.textContent = "";
        });

        panel.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (sending) return;

            const username = usernameInput.value.trim();
            const password = passwordInput.value;
            const newEmail = newEmailInput.value.trim();

            if (!username) {
                msgBox.style.color = "#e05050";
                msgBox.textContent = t("changeEmailUserRequired");
                usernameInput.focus();
                return;
            }
            if (!password) {
                msgBox.style.color = "#e05050";
                msgBox.textContent = t("changeEmailPasswordRequired");
                passwordInput.focus();
                return;
            }
            if (!newEmail) {
                msgBox.style.color = "#e05050";
                msgBox.textContent = t("changeEmailInvalidEmail");
                newEmailInput.focus();
                return;
            }

            sending = true;
            submitBtn.disabled = true;
            submitBtn.textContent = t("processing");
            msgBox.style.color = "#aaa";
            msgBox.textContent = "…";

            try {
                const fd = new FormData();
                fd.append("username", username);
                fd.append("password", password);
                fd.append("new_email", newEmail);
                const resp = await fetch("/change-email", { method: "POST", body: fd });
                const data = await resp.json();

                if (data.success) {
                    msgBox.style.color = "#4caf50";
                    msgBox.textContent = t("changeEmailSuccess");
                } else {
                    msgBox.style.color = "#e05050";
                    if (data.error_code === "changeEmailTooFrequent") {
                        const wait = Math.ceil((data.wait_seconds || 300) / 60);
                        msgBox.textContent = t("changeEmailTooFrequent", { wait });
                    } else {
                        msgBox.textContent = t(data.error_code || "changeEmailFailed", { minutes: retryMinutes(data) });
                    }
                }
            } catch {
                msgBox.style.color = "#e05050";
                msgBox.textContent = t("changeEmailFailed");
            } finally {
                sending = false;
                submitBtn.disabled = false;
                submitBtn.textContent = t("changeEmailSubmit");
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initChangeEmail);
    } else {
        initChangeEmail();
    }
})();

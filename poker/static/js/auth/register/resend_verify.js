/**
 * 重发验证邮件面板逻辑
 * - 点击"重发验证邮件"链接展开面板；从其他页面带 #resend 进入时自动展开
 * - 填邮箱提交，显示结果，处理频率限制
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
        // 已存在则跳过
        if (document.getElementById("resend-panel")) return null;

        const panel = document.createElement("form");
        panel.id = "resend-panel";
        panel.className = "register-panel";
        panel.noValidate = true;
        panel.hidden = true;

        panel.innerHTML = `
            <p class="register-panel-title" id="resend-title"></p>
            <input type="email" id="resend-email" name="email"
                   autocomplete="email" autocapitalize="off" spellcheck="false">
            <div class="register-panel-actions">
                <button type="submit" id="resend-submit" class="register-panel-submit"></button>
                <button type="button" id="resend-cancel" class="register-panel-cancel"></button>
            </div>
            <div id="resend-msg" class="register-panel-msg" role="alert" aria-live="polite"></div>
        `;

        return panel;
    }

    function initResend() {
        const trigger = document.getElementById("resend-trigger");
        if (!trigger) return;

        const panel = buildPanel();
        if (!panel) return;
        trigger.parentNode.insertAdjacentElement("afterend", panel);

        const emailInput = document.getElementById("resend-email");
        const submitBtn = document.getElementById("resend-submit");
        const cancelBtn = document.getElementById("resend-cancel");
        const msgBox = document.getElementById("resend-msg");
        const titleEl = document.getElementById("resend-title");
        let sending = false;

        function applyI18n() {
            titleEl.textContent = t("resendVerifyTitle");
            emailInput.placeholder = t("resendEmailPlaceholder");
            emailInput.setAttribute("aria-label", t("resendEmailPlaceholder"));
            submitBtn.textContent = sending ? t("processing") : t("resendSubmit");
            cancelBtn.textContent = t("resendCancel");
        }
        applyI18n();
        document.addEventListener("languageChanged", applyI18n);

        function openPanel() {
            // 关闭修改邮箱面板（互斥）
            const other = document.getElementById("change-email-panel");
            if (other) other.hidden = true;

            panel.hidden = false;
            msgBox.textContent = "";
            emailInput.value = "";
            // 面板在页面底部，打开后滚到可见位置并聚焦输入框
            panel.scrollIntoView({ behavior: "smooth", block: "center" });
            emailInput.focus({ preventScroll: true });
        }

        trigger.addEventListener("click", (e) => {
            e.preventDefault();
            if (panel.hidden) {
                openPanel();
            } else {
                panel.hidden = true;
            }
        });

        cancelBtn.addEventListener("click", () => {
            panel.hidden = true;
            msgBox.textContent = "";
        });

        panel.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (sending) return;

            const email = emailInput.value.trim();
            if (!email) {
                msgBox.style.color = "#e05050";
                msgBox.textContent = t("resendEmailRequired");
                emailInput.focus();
                return;
            }

            sending = true;
            submitBtn.disabled = true;
            submitBtn.textContent = t("processing");
            msgBox.style.color = "#aaa";
            msgBox.textContent = "…";

            try {
                const fd = new FormData();
                fd.append("email", email);
                const resp = await fetch("/resend-verify-email", { method: "POST", body: fd });
                const data = await resp.json();

                if (data.success) {
                    msgBox.style.color = "#4caf50";
                    msgBox.textContent = t("resendSent");
                } else {
                    msgBox.style.color = "#e05050";
                    msgBox.textContent = t(data.error_code || "resendFailed", { minutes: retryMinutes(data) });
                }
            } catch {
                msgBox.style.color = "#e05050";
                msgBox.textContent = t("resendFailed");
            } finally {
                sending = false;
                submitBtn.disabled = false;
                submitBtn.textContent = t("resendSubmit");
            }
        });

        // 从验证页、登录页的“重发验证邮件”链接进入时直接展开
        if (window.location.hash === "#resend") {
            openPanel();
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initResend);
    } else {
        initResend();
    }
})();

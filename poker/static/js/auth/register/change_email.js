/**
 * 修改注册邮箱面板逻辑
 * - 账号未验证时可用，需输入用户名 + 密码 + 新邮箱
 * - 5 分钟内不能重复操作
 */

(function () {
    const t = (key, vars) => {
        const lang = window.__lang || "zh";
        const map = window.registerTranslations?.[lang] || {};
        let str = map[key] || key;
        if (vars) {
            Object.entries(vars).forEach(([k, v]) => {
                str = str.replace(`{${k}}`, v);
            });
        }
        return str;
    };

    function buildPanel() {
        if (document.getElementById("change-email-panel")) return;

        const panel = document.createElement("div");
        panel.id = "change-email-panel";
        panel.style.cssText = [
            "display:none",
            "margin-top:16px",
            "padding:16px",
            "border:1px solid #333",
            "border-radius:8px",
            "background:#111",
        ].join(";");

        const inputStyle = [
            "width:100%",
            "box-sizing:border-box",
            "padding:10px 14px",
            "border-radius:6px",
            "border:1px solid #444",
            "background:#1a1a1a",
            "color:#fff",
            "font-size:14px",
            "margin-bottom:10px",
        ].join(";");

        panel.innerHTML = `
            <input type="text"     id="ce-username" style="${inputStyle}">
            <input type="password" id="ce-password" style="${inputStyle}">
            <input type="email"    id="ce-new-email" style="${inputStyle}">
            <div style="display:flex;gap:8px;">
                <button id="ce-submit"
                    style="flex:1;padding:10px;border:none;border-radius:6px;
                           background:#fff;color:#111;font-weight:bold;
                           cursor:pointer;font-size:14px;"></button>
                <button id="ce-cancel"
                    style="flex:1;padding:10px;border:1px solid #444;border-radius:6px;
                           background:transparent;color:#aaa;cursor:pointer;font-size:14px;"></button>
            </div>
            <div id="ce-msg" style="margin-top:10px;font-size:13px;min-height:18px;"></div>
        `;

        return panel;
    }

    function initChangeEmail() {
        const trigger = document.getElementById("change-email-trigger");
        if (!trigger) return;

        const panel = buildPanel();
        // 插在 resend-panel 后面（如果有），否则插在 trigger 的父元素后
        const resendPanel = document.getElementById("resend-panel");
        const anchor = resendPanel || trigger.parentNode;
        anchor.insertAdjacentElement("afterend", panel);

        const usernameInput = document.getElementById("ce-username");
        const passwordInput = document.getElementById("ce-password");
        const newEmailInput = document.getElementById("ce-new-email");
        const submitBtn    = document.getElementById("ce-submit");
        const cancelBtn    = document.getElementById("ce-cancel");
        const msgBox       = document.getElementById("ce-msg");

        function applyI18n() {
            usernameInput.placeholder = t("changeEmailUsernamePlaceholder");
            passwordInput.placeholder = t("changeEmailPasswordPlaceholder");
            newEmailInput.placeholder = t("changeEmailNewPlaceholder");
            submitBtn.textContent     = t("changeEmailSubmit");
            cancelBtn.textContent     = t("changeEmailCancel");
        }
        applyI18n();
        document.addEventListener("languageChanged", applyI18n);

        trigger.addEventListener("click", (e) => {
            e.preventDefault();
            // 关闭重发面板（互斥）
            const rp = document.getElementById("resend-panel");
            if (rp) rp.style.display = "none";
            panel.style.display = panel.style.display === "none" ? "block" : "none";
            msgBox.textContent = "";
        });

        cancelBtn.addEventListener("click", () => {
            panel.style.display = "none";
            msgBox.textContent = "";
        });

        submitBtn.addEventListener("click", async () => {
            const username = usernameInput.value.trim();
            const password = passwordInput.value;
            const newEmail = newEmailInput.value.trim();

            if (!username) {
                msgBox.style.color = "#e05050";
                msgBox.textContent = t("changeEmailUserRequired");
                return;
            }
            if (!password) {
                msgBox.style.color = "#e05050";
                msgBox.textContent = t("changeEmailPasswordRequired");
                return;
            }
            if (!newEmail) {
                msgBox.style.color = "#e05050";
                msgBox.textContent = t("changeEmailInvalidEmail");
                return;
            }

            submitBtn.disabled = true;
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
                    submitBtn.disabled = false;
                } else {
                    msgBox.style.color = "#e05050";
                    if (data.error_code === "changeEmailTooFrequent") {
                        const wait = Math.ceil((data.wait_seconds || 300) / 60);
                        msgBox.textContent = t("changeEmailTooFrequent", { wait });
                    } else {
                        msgBox.textContent = t(data.error_code || "changeEmailFailed");
                    }
                    submitBtn.disabled = false;
                }
            } catch {
                msgBox.style.color = "#e05050";
                msgBox.textContent = t("changeEmailFailed");
                submitBtn.disabled = false;
            }
        });

        // 互斥：打开重发面板时关闭本面板
        document.getElementById("resend-trigger")?.addEventListener("click", () => {
            panel.style.display = "none";
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initChangeEmail);
    } else {
        initChangeEmail();
    }
})();

/**
 * 重发验证邮件面板逻辑
 * - 点击"重发验证邮件"链接展开面板
 * - 填邮箱提交，显示结果，处理频率限制
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
        // 已存在则跳过
        if (document.getElementById("resend-panel")) return;

        const panel = document.createElement("div");
        panel.id = "resend-panel";
        panel.style.cssText = [
            "display:none",
            "margin-top:16px",
            "padding:16px",
            "border:1px solid #333",
            "border-radius:8px",
            "background:#111",
        ].join(";");

        panel.innerHTML = `
            <p style="color:#aaa;font-size:13px;margin:0 0 10px;"
               id="resend-title"></p>
            <input type="email" id="resend-email"
                style="width:100%;box-sizing:border-box;padding:10px 14px;
                       border-radius:6px;border:1px solid #444;background:#1a1a1a;
                       color:#fff;font-size:14px;margin-bottom:10px;"
            >
            <div style="display:flex;gap:8px;">
                <button id="resend-submit"
                    style="flex:1;padding:10px;border:none;border-radius:6px;
                           background:#fff;color:#111;font-weight:bold;
                           cursor:pointer;font-size:14px;"></button>
                <button id="resend-cancel"
                    style="flex:1;padding:10px;border:1px solid #444;border-radius:6px;
                           background:transparent;color:#aaa;cursor:pointer;font-size:14px;"></button>
            </div>
            <div id="resend-msg" style="margin-top:10px;font-size:13px;min-height:18px;"></div>
        `;

        return panel;
    }

    function initResend() {
        const trigger = document.getElementById("resend-trigger");
        if (!trigger) return;

        const panel = buildPanel();
        trigger.parentNode.insertAdjacentElement("afterend", panel);

        const emailInput = document.getElementById("resend-email");
        const submitBtn = document.getElementById("resend-submit");
        const cancelBtn = document.getElementById("resend-cancel");
        const msgBox = document.getElementById("resend-msg");
        const titleEl = document.getElementById("resend-title");

        function applyI18n() {
            titleEl.textContent = t("resendVerifyTitle");
            emailInput.placeholder = t("resendEmailPlaceholder");
            submitBtn.textContent = t("resendSubmit");
            cancelBtn.textContent = t("resendCancel");
        }
        applyI18n();
        document.addEventListener("languageChanged", applyI18n);

        trigger.addEventListener("click", (e) => {
            e.preventDefault();
            panel.style.display = panel.style.display === "none" ? "block" : "none";
            msgBox.textContent = "";
            emailInput.value = "";
        });

        cancelBtn.addEventListener("click", () => {
            panel.style.display = "none";
            msgBox.textContent = "";
        });

        submitBtn.addEventListener("click", async () => {
            const email = emailInput.value.trim();
            if (!email) {
                msgBox.style.color = "#e05050";
                msgBox.textContent = t("resendEmailRequired");
                return;
            }

            submitBtn.disabled = true;
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
                    submitBtn.disabled = false;
                } else {
                    msgBox.style.color = "#e05050";
                    if (data.error_code === "resendTooFrequent") {
                        const wait = Math.ceil((data.wait_seconds || 300) / 60);
                        msgBox.textContent = t("resendTooFrequent", { wait });
                    } else {
                        msgBox.textContent = t(data.error_code || "resendFailed");
                    }
                    submitBtn.disabled = false;
                }
            } catch {
                msgBox.style.color = "#e05050";
                msgBox.textContent = t("resendFailed");
                submitBtn.disabled = false;
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initResend);
    } else {
        initResend();
    }
})();

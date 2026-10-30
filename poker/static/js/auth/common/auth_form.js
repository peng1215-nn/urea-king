/*
 * 登录类页面共用的小工具：提交按钮的处理中状态、限流提示里的分钟数、登录过期跳转。
 * 依赖 common/language.js 里的 t()。
 */

// 把 "{minutes}" 这类占位符替换成实际值
function authFormat(text, vars) {
    let result = String(text);
    Object.entries(vars || {}).forEach(([name, value]) => {
        result = result.split(`{${name}}`).join(String(value));
    });
    return result;
}


// 后端在限流时返回 retry_after（秒）；没有时按限流窗口 15 分钟提示
function authRetryMinutes(data) {
    const seconds = Number(data && data.retry_after);
    if (!Number.isFinite(seconds) || seconds <= 0) {
        return 15;
    }
    return Math.max(1, Math.ceil(seconds / 60));
}


// 翻译一条提示；*TooManyAttempts 这类带 {minutes} 的会替换成实际等待时间
function authMessage(key, data) {
    return authFormat(t(key), { minutes: authRetryMinutes(data) });
}


// 提交中禁用按钮并显示“处理中…”，结束后恢复按钮原本的翻译文字
function authSetBusy(button, busy, busyKey = "processing") {
    if (!button) {
        return;
    }

    button.disabled = busy;
    button.setAttribute("aria-busy", busy ? "true" : "false");

    if (busy) {
        button.innerText = t(busyKey);
        return;
    }

    const key = button.getAttribute("data-i18n");
    if (key) {
        button.innerText = t(key);
    }
}


// 登录状态已失效（会话过期或未登录）
function authIsSessionExpired(data) {
    const code = data && (data.error_code || data.message);
    return code === "sessionExpired" || code === "loginRequired";
}


function authRedirectExpired() {
    window.location.href = "/login?reason=expired";
}


// 让表单支持回车 / 手机键盘“前往”提交
function authBindSubmit(formId, handler) {
    const form = document.getElementById(formId);
    if (!form) {
        return;
    }

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        handler();
    });
}


// 客户端校验失败时把焦点放到对应输入框
function authFocus(id) {
    const element = document.getElementById(id);
    if (element) {
        element.focus();
    }
}

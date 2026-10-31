// 隐私说明页：中英文全文都写在页面里，按当前语言只显示一份。
(function () {
    function show(lang) {
        const current = lang === "en" ? "en" : "zh";
        document.querySelectorAll("[data-privacy-lang]").forEach(el => {
            el.hidden = el.getAttribute("data-privacy-lang") !== current;
        });
        document.title = current === "en"
            ? "Privacy Notice - UREAKING POKER"
            : "隐私说明 - UREAKING POKER";
        const back = document.querySelector("[data-privacy-back]");
        if (back) back.innerText = current === "en" ? "← Back to sign in" : "← 返回登录";
    }

    document.addEventListener("languageChanged", event => show(event.detail && event.detail.lang));
    document.addEventListener("DOMContentLoaded", () => show(getCurrentLanguage()));
})();

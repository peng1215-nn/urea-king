window.verifyEmailTranslations = {
    zh: {
        pageTitle: "邮箱验证 - UREAKING POKER",
        verifyPendingTitle: "确认验证邮箱",
        verifyPendingMsg: "点击下方按钮完成邮箱验证。",
        verifyConfirmBtn: "确认验证",
        verifySuccessTitle: "邮箱验证成功",
        verifySuccessMsg: "您的邮箱已验证，现在可以登录了。",
        goLogin: "前往登录",
        verifyUsedTitle: "链接已失效",
        verifyUsedMsg: "该验证链接已被使用，或因更换了邮箱而失效。如果您的邮箱尚未验证，请使用最新一封验证邮件中的链接。",
        backLogin: "返回登录",
        verifyExpiredTitle: "链接已过期",
        verifyExpiredMsg: "验证链接已过期（有效期 15 分钟）。请重新注册以获取新的验证邮件。",
        reRegister: "重新注册",
        verifyInvalidTitle: "验证失败",
        verifyInvalidMsg: "验证链接无效或已过期。请检查链接是否完整，或重新注册。",
        verifyTokenInvalid: "验证链接无效，请重新注册。",
        verifyTokenUsed: "该验证链接已使用或已失效。",
        verifyTokenExpired: "验证链接已过期，请重新注册。",
        verifyFailed: "验证失败，请稍后重试。",
    },
    en: {
        pageTitle: "Email Verification - UREAKING POKER",
        verifyPendingTitle: "Confirm Email Verification",
        verifyPendingMsg: "Click the button below to complete email verification.",
        verifyConfirmBtn: "Confirm Verification",
        verifySuccessTitle: "Email Verified",
        verifySuccessMsg: "Your email has been verified. You can now log in.",
        goLogin: "Go to Login",
        verifyUsedTitle: "Link No Longer Valid",
        verifyUsedMsg: "This verification link has already been used, or it stopped working because the email address was changed. If your email is not yet verified, please use the link in the most recent verification email.",
        backLogin: "Back to Login",
        verifyExpiredTitle: "Link Expired",
        verifyExpiredMsg: "The verification link has expired (valid for 15 minutes). Please register again to receive a new verification email.",
        reRegister: "Register Again",
        verifyInvalidTitle: "Verification Failed",
        verifyInvalidMsg: "The verification link is invalid or has expired. Please check the link or register again.",
        verifyTokenInvalid: "The verification link is invalid. Please register again.",
        verifyTokenUsed: "This verification link has already been used or is no longer valid.",
        verifyTokenExpired: "The verification link has expired. Please register again.",
        verifyFailed: "Verification failed. Please try again later.",
    }
};

// 应用翻译
(function () {
    const lang = localStorage.getItem("lang") || "zh";
    const t = (window.verifyEmailTranslations[lang] || window.verifyEmailTranslations.zh);
    document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (t[key]) el.textContent = t[key];
    });
    const titleEl = document.querySelector("title");
    if (titleEl && t.pageTitle) titleEl.textContent = t.pageTitle;
})();

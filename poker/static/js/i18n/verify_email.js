window.verifyEmailTranslations = {
    zh: {
        pageTitle: "邮箱验证 - UREAKING POKER",
        verifyPendingTitle: "确认验证邮箱",
        verifyPendingMsg: "请确认下面是你注册的账号和邮箱，再点击确认。如果不是你注册的账号，请不要确认。",
        verifyAccountLabel: "账号",
        verifyEmailLabel: "邮箱",
        verifyEmailTakenTitle: "邮箱已被验证",
        verifyEmailTakenMsg: "这个邮箱已经被另一个账号验证过了，不能再用于这个账号。如果那个账号是你的，请直接登录；如果不是，请用找回密码重置它的密码。",
        verifyEmailTaken: "这个邮箱已经被另一个账号验证过了。",
        verifyConfirmBtn: "确认验证",
        verifySuccessTitle: "邮箱验证成功",
        verifySuccessMsg: "您的邮箱已验证，现在可以登录了。",
        goLogin: "前往登录",
        verifyUsedTitle: "链接已失效",
        verifyUsedMsg: "该验证链接已被使用，或因更换了邮箱而失效。如果您的邮箱尚未验证，请使用最新一封验证邮件中的链接。",
        backLogin: "返回登录",
        verifyExpiredTitle: "链接已过期",
        verifyExpiredMsg: "验证链接已过期（有效期 15 分钟）。你的账号已经保留，不需要重新注册，点击下方按钮输入注册邮箱，重新获取验证邮件即可。",
        reRegister: "重新注册",
        resendVerifyBtn: "重发验证邮件",
        verifyInvalidTitle: "验证失败",
        verifyInvalidMsg: "验证链接无效或已过期。请检查链接是否完整；如果账号已注册但还没验证，不需要重新注册，点击下方按钮重新获取验证邮件即可。",
        verifyTokenInvalid: "验证链接无效，请重新获取验证邮件。",
        verifyTokenUsed: "该验证链接已使用或已失效。",
        verifyTokenExpired: "验证链接已过期，请重新获取验证邮件。",
        verifyFailed: "验证失败，请稍后重试。",
        changePendingTitle: "确认更换邮箱",
        changePendingMsg: "确认后，这个账号的邮箱会换成下面的新邮箱，以后找回密码的邮件也会发到这里。如果不是你本人申请的，请不要确认。",
        changeNewEmailLabel: "新邮箱",
        changeConfirmBtn: "确认更换",
        changeSuccessTitle: "邮箱已更换",
        changeSuccessMsg: "新邮箱已经生效，原邮箱会收到一封通知。",
        changeLinkInvalidTitle: "链接已失效",
        changeLinkInvalidMsg: "这个更换邮箱的链接已过期、已使用，或已被更新的申请取代（有效期 30 分钟，只有最新一封有效）。邮箱没有更换，请回到个人资料页重新申请。",
        backHome: "返回网站",
    },
    en: {
        pageTitle: "Email Verification - UREAKING POKER",
        verifyPendingTitle: "Confirm Email Verification",
        verifyPendingMsg: "Please check that the account and email below are yours, then confirm. If this isn't the account you registered, don't confirm.",
        verifyAccountLabel: "Account",
        verifyEmailLabel: "Email",
        verifyEmailTakenTitle: "Email Already Verified",
        verifyEmailTakenMsg: "This email has already been verified by another account and can't be used for this one. If that account is yours, just log in; if not, use Forgot Password to reset its password.",
        verifyEmailTaken: "This email has already been verified by another account.",
        verifyConfirmBtn: "Confirm Verification",
        verifySuccessTitle: "Email Verified",
        verifySuccessMsg: "Your email has been verified. You can now log in.",
        goLogin: "Go to Login",
        verifyUsedTitle: "Link No Longer Valid",
        verifyUsedMsg: "This verification link has already been used, or it stopped working because the email address was changed. If your email is not yet verified, please use the link in the most recent verification email.",
        backLogin: "Back to Login",
        verifyExpiredTitle: "Link Expired",
        verifyExpiredMsg: "The verification link has expired (valid for 15 minutes). Your account is kept, so there's no need to register again — tap the button below and enter your registration email to get a new verification email.",
        reRegister: "Register Again",
        resendVerifyBtn: "Resend verification email",
        verifyInvalidTitle: "Verification Failed",
        verifyInvalidMsg: "The verification link is invalid or has expired. Please check that the link is complete. If your account is registered but not yet verified, there's no need to register again — tap the button below to get a new verification email.",
        verifyTokenInvalid: "The verification link is invalid. Please request a new verification email.",
        verifyTokenUsed: "This verification link has already been used or is no longer valid.",
        verifyTokenExpired: "The verification link has expired. Please request a new verification email.",
        verifyFailed: "Verification failed. Please try again later.",
        changePendingTitle: "Confirm Email Change",
        changePendingMsg: "After you confirm, this account's email will change to the new address below, and password reset emails will go there. If you didn't request this, don't confirm.",
        changeNewEmailLabel: "New email",
        changeConfirmBtn: "Confirm Change",
        changeSuccessTitle: "Email Changed",
        changeSuccessMsg: "Your new email is now in use. A notice has been sent to your previous address.",
        changeLinkInvalidTitle: "Link No Longer Valid",
        changeLinkInvalidMsg: "This email change link has expired, been used, or been replaced by a newer request (valid for 30 minutes; only the latest one works). Your email was not changed — please request again from your profile page.",
        backHome: "Back to site",
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

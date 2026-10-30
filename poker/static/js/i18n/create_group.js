window.createGroupTranslations = {
    zh: {
        invalidRequest: "提交的内容格式不正确，请检查后重试。",
        requestTooLarge: "提交的内容太大（普通请求上限 1 MB，头像上限 10 MB），请缩小后再试。",
        pageTitle: "创建组 - UREAKING POKER",
        createGroupDesc: "创建自己的组，成为局头。每个账号只能创建一个组。",
        createGroupDesc2: "成员加入需使用邀请码。",
        groupNameLabel: "组名",
        groupNamePlaceholder: "请输入组名（最多 50 字符）",
        createGroupBtn: "创建组",
        creatingBtn: "创建中…",
        backToGroupSelect: "返回选组",
        createGroupNameRequired: "请输入组名。",
        createGroupNameTooLong: "组名不能超过 50 个字符。",
        createGroupNameInvalid: "组名包含非法字符。",
        createGroupNotVerified: "请先验证邮箱。",
        createGroupAlreadyOwner: "您已创建过一个组，每个账号只能创建一个组。",
        createGroupFailed: "创建失败，请稍后重试。",
        createGroupSuccess: "创建成功！",
        createGroupSuccessMsg: "组「{name}」创建成功！组代码：{code}",
        requestFailed: "请求失败，请稍后重试。",
    },
    en: {
        invalidRequest: "Some of the submitted values are not in the right format. Please check and try again.",
        requestTooLarge: "The submitted data is too large (1 MB for normal requests, 10 MB for avatars). Please make it smaller and try again.",
        pageTitle: "Create Group - UREAKING POKER",
        createGroupDesc: "Create your own group and become the organizer. Each account can only create one group.",
        createGroupDesc2: "Members join using an invite code.",
        groupNameLabel: "Group Name",
        groupNamePlaceholder: "Enter group name (max 50 characters)",
        createGroupBtn: "Create Group",
        creatingBtn: "Creating…",
        backToGroupSelect: "Back to Group Select",
        createGroupNameRequired: "Please enter a group name.",
        createGroupNameTooLong: "Group name cannot exceed 50 characters.",
        createGroupNameInvalid: "Group name contains invalid characters.",
        createGroupNotVerified: "Please verify your email first.",
        createGroupAlreadyOwner: "You have already created a group. Each account can only create one group.",
        createGroupFailed: "Creation failed. Please try again later.",
        createGroupSuccess: "Group created!",
        createGroupSuccessMsg: "Group \"{name}\" created! Group code: {code}",
        requestFailed: "Request failed. Please try again later.",
    }
};

(function () {
    const lang = localStorage.getItem("lang") || "zh";
    const t = window.createGroupTranslations[lang] || window.createGroupTranslations.zh;
    document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (t[key]) el.textContent = t[key];
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
        const key = el.getAttribute("data-i18n-placeholder");
        if (t[key]) el.placeholder = t[key];
    });
    const titleEl = document.querySelector("title");
    if (titleEl && t.pageTitle) titleEl.textContent = t.pageTitle;
})();

const ERROR_MESSAGES = {
    loginRequired: "请先登录。",
    createGroupNameRequired: "请输入组名。",
    createGroupNameTooLong: "组名不能超过 50 个字符。",
    createGroupNameInvalid: "组名包含非法字符。",
    createGroupNotVerified: "请先验证邮箱。",
    createGroupAlreadyOwner: "您已创建过一个组，每个账号只能创建一个组。",
    createGroupFailed: "创建失败，请稍后重试。",
};

async function createGroup() {
    const msgBox = document.getElementById("message-box");
    const btn = document.getElementById("cg-btn");
    const groupName = document.getElementById("group-name").value.trim();

    if (!groupName) {
        msgBox.textContent = "请输入组名。";
        msgBox.style.color = "#e55";
        return;
    }

    btn.disabled = true;
    btn.textContent = "创建中…";

    try {
        const fd = new FormData();
        fd.append("group_name", groupName);

        const res = await fetch("/create-group", { method: "POST", body: fd });
        const data = await res.json();

        if (data.success) {
            msgBox.textContent = `组「${data.group_name}」创建成功！组代码：${data.group_code}`;
            msgBox.style.color = "#5c5";
            btn.style.display = "none";

            setTimeout(() => { window.location.href = "/group-select"; }, 3000);
        } else {
            if (data.error_code === "loginRequired") {
                window.location.href = "/login";
                return;
            }
            msgBox.textContent = ERROR_MESSAGES[data.error_code] || "创建失败，请稍后重试。";
            msgBox.style.color = "#e55";
            btn.disabled = false;
            btn.textContent = "创建组";
        }
    } catch (e) {
        msgBox.textContent = "请求失败，请稍后重试。";
        msgBox.style.color = "#e55";
        btn.disabled = false;
        btn.textContent = "创建组";
    }
}

document.getElementById("cg-btn").addEventListener("click", createGroup);

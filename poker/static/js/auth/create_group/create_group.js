let createGroupSubmitting = false;

async function createGroup() {
    if (createGroupSubmitting) {
        return;
    }

    const msgBox = document.getElementById("message-box");
    const btn = document.getElementById("cg-btn");
    const groupName = document.getElementById("group-name").value.trim();

    if (!groupName) {
        msgBox.textContent = t("createGroupNameRequired");
        msgBox.style.color = "#e55";
        authFocus("group-name");
        return;
    }

    createGroupSubmitting = true;
    btn.disabled = true;
    btn.textContent = t("creatingBtn");

    let done = false;

    try {
        const fd = new FormData();
        fd.append("group_name", groupName);

        const res = await fetch("/create-group", { method: "POST", body: fd });
        const data = await res.json();

        if (data.success) {
            // 不自动跳转：先说明下一步（生成邀请码发给朋友），由用户点“进入”
            msgBox.textContent = authFormat(t("createGroupSuccessMsg"), { name: data.group_name || groupName });
            msgBox.style.color = "#5c5";
            btn.style.display = "none";
            document.getElementById("group-name").closest(".form-group").style.display = "none";

            const continueLink = document.getElementById("cg-continue");
            continueLink.hidden = false;
            continueLink.focus();
            done = true;
            return;
        }

        if (authIsSessionExpired(data)) {
            done = true;
            authRedirectExpired();
            return;
        }

        msgBox.textContent = t(data.error_code || data.message || "createGroupFailed");
        msgBox.style.color = "#e55";
    } catch (e) {
        msgBox.textContent = t("requestFailed");
        msgBox.style.color = "#e55";
    } finally {
        if (!done) {
            createGroupSubmitting = false;
            btn.disabled = false;
            btn.textContent = t("createGroupBtn");
        }
    }
}

authBindSubmit("cg-form", createGroup);

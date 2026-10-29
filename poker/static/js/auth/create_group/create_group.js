async function createGroup() {
    const msgBox = document.getElementById("message-box");
    const btn = document.getElementById("cg-btn");
    const groupName = document.getElementById("group-name").value.trim();

    if (!groupName) {
        msgBox.textContent = t("createGroupNameRequired");
        msgBox.style.color = "#e55";
        return;
    }

    btn.disabled = true;
    btn.textContent = t("creatingBtn");

    try {
        const fd = new FormData();
        fd.append("group_name", groupName);

        const res = await fetch("/create-group", { method: "POST", body: fd });
        const data = await res.json();

        if (data.success) {
            const msg = t("createGroupSuccessMsg")
                .replace("{name}", data.group_name)
                .replace("{code}", data.group_code);
            msgBox.textContent = msg;
            msgBox.style.color = "#5c5";
            btn.style.display = "none";

            setTimeout(() => { window.location.href = "/group-select"; }, 3000);
        } else {
            if (data.error_code === "loginRequired") {
                window.location.href = "/login";
                return;
            }
            msgBox.textContent = t(data.error_code) || t("createGroupFailed");
            msgBox.style.color = "#e55";
            btn.disabled = false;
            btn.textContent = t("createGroupBtn");
        }
    } catch (e) {
        msgBox.textContent = t("requestFailed");
        msgBox.style.color = "#e55";
        btn.disabled = false;
        btn.textContent = t("createGroupBtn");
    }
}

document.getElementById("cg-btn").addEventListener("click", createGroup);

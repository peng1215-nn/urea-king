async function loadGroupInfo() {
    try {
        const data = await fetchGroupInfo();
        if (data.success) {
            document.getElementById("current-group-name").value = data.group_name || "";
        }
    } catch (e) {
        console.error(e);
    }
}

async function saveGroupName() {
    const messageBox = document.getElementById("group-name-message");
    const newName = document.getElementById("new-group-name").value.trim();

    messageBox.className = "operation-message";
    messageBox.innerText = "";

    if (!newName) {
        messageBox.classList.add("error");
        messageBox.innerText = t("groupNameRequired");
        return;
    }
    if (newName.length > 50) {
        messageBox.classList.add("error");
        messageBox.innerText = t("groupNameTooLong");
        return;
    }

    const currentName = document.getElementById("current-group-name").value.trim();
    if (newName === currentName) {
        messageBox.classList.add("error");
        messageBox.innerText = t("groupNameNoChange");
        return;
    }

    try {
        const data = await apiUpdateGroupName(newName);
        if (data.success) {
            messageBox.classList.add("success");
            messageBox.innerText = t("groupNameUpdateSuccess");
            document.getElementById("current-group-name").value = newName;
            document.getElementById("new-group-name").value = "";
        } else {
            messageBox.classList.add("error");
            messageBox.innerText = t(data.message) || data.message || t("operationFailed");
        }
    } catch (e) {
        messageBox.classList.add("error");
        messageBox.innerText = t("operationFailed");
    }
}

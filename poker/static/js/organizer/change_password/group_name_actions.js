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
    setMsg("group-name-message", "", "");

    const newName = document.getElementById("new-group-name").value.trim();

    if (!newName) {
        setMsg("group-name-message", t("groupNameRequired"), "error");
        return;
    }
    if (newName.length > 50) {
        setMsg("group-name-message", t("groupNameTooLong"), "error");
        return;
    }

    const currentName = document.getElementById("current-group-name").value.trim();
    if (newName === currentName) {
        setMsg("group-name-message", t("groupNameNoChange"), "error");
        return;
    }

    try {
        const data = await apiUpdateGroupName(newName);
        if (data.success) {
            setMsg("group-name-message", t("groupNameUpdateSuccess"), "success");
            document.getElementById("current-group-name").value = newName;
            document.getElementById("new-group-name").value = "";
        } else {
            setMsg("group-name-message", t(data.message) || data.message || t("operationFailed"), "error");
        }
    } catch (e) {
        setMsg("group-name-message", t("operationFailed"), "error");
    }
}

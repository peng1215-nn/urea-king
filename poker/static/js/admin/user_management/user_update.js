async function updateUserRole() {
    const messageBox =
        document.getElementById("update-user-message");

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    if (!selectedUser) {
        messageBox.innerText =
            t("pleaseSelectUser")

        return;
    }

    if (selectedUser.role === "admin") {
        messageBox.innerText =
           t("adminModifyForbidden")

        return;
    }

    const groupId =
        document.getElementById("edit-group-id").value;

    const role =
        document.getElementById("edit-role").value;

    if (!groupId) {
        messageBox.innerText =
            t("pleaseSelectGroup")

        return;
    }

    if (!role) {
        messageBox.innerText =
            t("pleaseSelectRole")

        return;
    }

    if (role === selectedUser.role) {
        messageBox.innerText =
            t("roleNoChange")

        return;
    }

    const formData = new FormData();

    formData.append("target_user_id", selectedUser.id);
    formData.append("group_id", groupId);
    formData.append("role", role);

    try {
        const response = await fetch(
            "/admin/update-user-role",
            {
                method: "POST",
                body: formData,
            }
        );

        const data = await response.json();

        if (!data.success) {
            messageBox.innerText =
                data.message || t("updateFailed");

            return;
        }

        await loadUsers();

        resetSelectedUserState();

        messageBox.style.color = "#5CFFB2";
        messageBox.innerText =
            t("updateSuccess");

    } catch (error) {
        console.error(error);

        messageBox.style.color = "#ff8a8a";
        messageBox.innerText =
            "修改失败。";
    }
}


function resetUserEditForm() {
    const groupSelect =
        document.getElementById("edit-group-id");

    const roleSelect =
        document.getElementById("edit-role");

    const updateButton =
        document.getElementById("update-user-button");

    groupSelect.innerHTML = `
        <option value="">${t("pleaseSelectUser")}</option>
    `;

    groupSelect.disabled = false;

    roleSelect.value = "";
    roleSelect.disabled = false;

    if (updateButton) {
        updateButton.disabled = false;
    }
}
async function updateUserRole() {
    const messageBox =
        document.getElementById("update-user-message");

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    if (!selectedUser) {
        messageBox.innerText =
            "请先选择一个用户。";

        return;
    }

    if (selectedUser.role === "admin") {
        messageBox.innerText =
            "管理员身份不可在此页面修改。";

        return;
    }

    const groupId =
        document.getElementById("edit-group-id").value;

    const role =
        document.getElementById("edit-role").value;

    if (!groupId) {
        messageBox.innerText =
            "请选择所属组。";

        return;
    }

    if (!role) {
        messageBox.innerText =
            "请选择身份。";

        return;
    }

    if (role === selectedUser.role) {
        messageBox.innerText =
            "身份无需更改。";

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
                data.message || "修改失败。";

            return;
        }

        await loadUsers();

        resetSelectedUserState();

        messageBox.style.color = "#5CFFB2";
        messageBox.innerText =
            "用户身份修改成功。";

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
        <option value="">请先选择用户</option>
    `;

    groupSelect.disabled = false;

    roleSelect.value = "";
    roleSelect.disabled = false;

    if (updateButton) {
        updateButton.disabled = false;
    }
}
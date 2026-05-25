async function loadGroupOptions() {

    const createGroupSelect =
        document.getElementById(
            "create-invite-group-id"
        );

    const deleteGroupSelect =
        document.getElementById(
            "delete-group-id"
        );

    createGroupSelect.innerHTML = `
        <option value="">
            ${t("pleaseSelectGroup")}
        </option>
    `;

    deleteGroupSelect.innerHTML = `
        <option value="">
            ${t("pleaseSelectGroup")}
        </option>
    `;

    const groupResult =
        await fetchGroupOptions();

    if (groupResult.success) {

        window.inviteManagementState.groups =
            groupResult.groups;

        groupResult.groups.forEach(group => {

            const option =
                document.createElement("option");

            option.value =
                group.id;

            option.textContent =
                `${group.group_name} (${group.group_code})`;

            createGroupSelect.appendChild(option);
        });
    }

    const deletableResult =
        await fetchDeletableGroupOptions();

    if (deletableResult.success) {

        window.inviteManagementState.deletableGroups =
            deletableResult.groups;

        deletableResult.groups.forEach(group => {

            const option =
                document.createElement("option");

            option.value =
                group.id;

            option.textContent =
                `${group.group_name} (${group.group_code})`;

            deleteGroupSelect.appendChild(option);
        });
    }
}


async function createGroup() {

    const messageBox =
        document.getElementById(
            "create-group-message"
        );

    const groupCode =
        document.getElementById(
            "create-group-code"
        ).value.trim();

    const groupName =
        document.getElementById(
            "create-group-name"
        ).value.trim();

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    if (!groupCode) {
        messageBox.innerText =
            t("groupCodeRequired");

        return;
    }

    if (!groupName) {
        messageBox.innerText =
            t("groupNameRequired");

        return;
    }

    const formData = new FormData();

    formData.append(
        "group_code",
        groupCode
    );

    formData.append(
        "group_name",
        groupName
    );

    try {
        const response = await fetch(
            "/admin/groups/create",
            {
                method: "POST",
                body: formData,
            }
        );

        const data =
            await response.json();

        if (!data.success) {
            messageBox.innerText =
                t(data.message || "operationFailed");

            return;
        }

        messageBox.style.color = "#5CFFB2";

        messageBox.innerText = t("groupCreateSuccess");

        document.getElementById("create-group-code").value = "";

        document.getElementById("create-group-name").value = "";

        await loadGroupOptions();

        await loadUnusedInvitationOptions();

    } catch (error) {
        console.error(error);

        messageBox.innerText =
            t("operationFailed");
    }
}


function openDeleteGroupModal() {

    const messageBox =
        document.getElementById(
            "delete-group-message"
        );

    const groupSelect =
        document.getElementById(
            "delete-group-id"
        );

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    if (!groupSelect.value) {
        messageBox.innerText =
            t("pleaseSelectGroup");

        return;
    }

    const selectedText =
        groupSelect.options[
            groupSelect.selectedIndex
        ].textContent;

    document.getElementById(
        "delete-group-text"
    ).innerText =
        `${t("deleteGroupConfirmText")} ${selectedText}`;

    document
        .getElementById("delete-group-modal")
        .classList.remove("hidden");
}


function closeDeleteGroupModal() {

    document
        .getElementById("delete-group-modal")
        .classList.add("hidden");
}


async function confirmDeleteGroup() {

    const messageBox =
        document.getElementById(
            "delete-group-message"
        );

    const groupId =
        document.getElementById(
            "delete-group-id"
        ).value;

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    if (!groupId) {
        messageBox.innerText =
            t("pleaseSelectGroup");

        closeDeleteGroupModal();

        return;
    }

    const formData = new FormData();

    formData.append(
        "group_id",
        groupId
    );

    try {
        const response = await fetch(
            "/admin/groups/delete",
            {
                method: "POST",
                body: formData,
            }
        );

        const data =
            await response.json();

        if (!data.success) {
            messageBox.innerText =
                t(data.message || "operationFailed");

            closeDeleteGroupModal();

            return;
        }

        messageBox.style.color =
            "#5CFFB2";

        messageBox.innerText =
            t("groupDeleteSuccess");

        closeDeleteGroupModal();

        await loadGroupOptions();

        await loadUnusedInvitationOptions();

    } catch (error) {
        console.error(error);

        messageBox.innerText =
            t("operationFailed");

        closeDeleteGroupModal();
    }
}
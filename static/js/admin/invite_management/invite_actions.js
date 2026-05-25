async function loadUnusedInvitationOptions() {

    const select =
        document.getElementById(
            "delete-invite-code"
        );

    select.innerHTML = `
        <option value="">
            ${t("pleaseSelectInviteCode")}
        </option>
    `;

    const result =
        await fetchUnusedInvitationOptions();

    if (!result.success) {
        return;
    }

    window.inviteManagementState.unusedInvitationCodes =
        result.invitation_codes;

    result.invitation_codes.forEach(invitation => {

        const option =
            document.createElement("option");

        option.value =
            invitation.id;

        option.textContent =
            `${invitation.code} | ${invitation.group_name} | ${invitation.role}`;

        select.appendChild(option);
    });
}


async function createInvitationCode() {

    const messageBox =
        document.getElementById(
            "create-invite-message"
        );

    const code =
        document.getElementById(
            "create-invite-code"
        ).value.trim();

    const groupId =
        document.getElementById(
            "create-invite-group-id"
        ).value;

    const role =
        document.getElementById(
            "create-invite-role"
        ).value;

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    if (!code) {
        messageBox.innerText =
            t("inviteCodeRequired");

        return;
    }

    if (!groupId) {
        messageBox.innerText =
            t("pleaseSelectGroup");

        return;
    }

    if (!role) {
        messageBox.innerText =
            t("pleaseSelectRole");

        return;
    }

    const formData = new FormData();

    formData.append(
        "code",
        code
    );

    formData.append(
        "group_id",
        groupId
    );

    formData.append(
        "role",
        role
    );

    try {
        const response = await fetch(
            "/admin/invitation-codes/create",
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

        messageBox.style.color =
            "#5CFFB2";

        messageBox.innerText =
            t("inviteCreateSuccess");

        document.getElementById(
            "create-invite-code"
        ).value = "";

        document.getElementById(
            "create-invite-role"
        ).value = "";

        await loadUnusedInvitationOptions();

    } catch (error) {
        console.error(error);

        messageBox.innerText =
            t("operationFailed");
    }
}


function openDeleteInviteModal() {

    const messageBox =
        document.getElementById(
            "delete-invite-message"
        );

    const select =
        document.getElementById(
            "delete-invite-code"
        );

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    if (!select.value) {
        messageBox.innerText =
            t("pleaseSelectInviteCode");

        return;
    }

    const selectedText =
        select.options[
            select.selectedIndex
        ].textContent;

    document.getElementById(
        "delete-invite-text"
    ).innerText =
        `${t("deleteInviteConfirmText")} ${selectedText}`;

    document
        .getElementById("delete-invite-modal")
        .classList.remove("hidden");
}


function closeDeleteInviteModal() {

    document
        .getElementById("delete-invite-modal")
        .classList.add("hidden");
}


async function confirmDeleteInvitationCode() {

    const messageBox =
        document.getElementById(
            "delete-invite-message"
        );

    const invitationId =
        document.getElementById(
            "delete-invite-code"
        ).value;

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    closeDeleteInviteModal();

    if (!invitationId) {
        messageBox.innerText =
            t("pleaseSelectInviteCode");

        return;
    }

    const formData = new FormData();

    formData.append(
        "invitation_id",
        invitationId
    );

    try {
        const response = await fetch(
            "/admin/invitation-codes/delete",
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

        messageBox.style.color =
            "#5CFFB2";

        messageBox.innerText =
            t("inviteDeleteSuccess");

        document.getElementById(
            "delete-invite-code"
        ).value = "";

        await loadUnusedInvitationOptions();

    } catch (error) {
        console.error(error);

        messageBox.innerText =
            t("operationFailed");
    }
}
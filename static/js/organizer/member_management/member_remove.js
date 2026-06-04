let pendingRemoveMember = null;


function updateRemoveMemberPanel(member) {
    const button = document.getElementById("remove-member-button");
    const messageBox = document.getElementById("remove-member-message");

    if (messageBox) {
        messageBox.innerText = "";
        messageBox.style.color = "#ff8a8a";
    }

    if (member.role === "organizer") {
        button.disabled = true;

        if (messageBox) {
            messageBox.innerText = t("organizerRemoveForbidden");
        }

        return;
    }

    button.disabled = false;
}


function resetRemoveMemberPanel() {
    const button = document.getElementById("remove-member-button");
    const messageBox = document.getElementById("remove-member-message");

    button.disabled = false;

    if (messageBox) {
        messageBox.innerText = "";
        messageBox.style.color = "#ff8a8a";
    }
}


function openRemoveMemberModal() {
    const messageBox = document.getElementById("remove-member-message");

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    if (!selectedMember) {
        messageBox.innerText = t("pleaseSelectMember");
        return;
    }

    if (selectedMember.role === "organizer") {
        messageBox.innerText = t("organizerRemoveForbidden");
        return;
    }

    pendingRemoveMember = selectedMember;

    const modal = document.getElementById("remove-member-modal");
    const text = document.getElementById("remove-member-text");

    text.innerText = t("removeMemberConfirmPrefix") + " " + selectedMember.username + t("removeMemberConfirmSuffix");

    modal.classList.remove("hidden");
}


function closeRemoveMemberModal() {
    const modal = document.getElementById("remove-member-modal");

    modal.classList.add("hidden");

    pendingRemoveMember = null;
}


async function confirmRemoveMember() {
    const messageBox = document.getElementById("remove-member-message");

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    if (!pendingRemoveMember) {
        closeRemoveMemberModal();
        return;
    }

    const formData = new FormData();

    formData.append("target_user_id", pendingRemoveMember.id);

    try {
        const response = await fetch(
            "/organizer/remove-member",
            {
                method: "POST",
                body: formData,
            }
        );

        const data = await response.json();

        if (!data.success) {
            messageBox.innerText = data.message || t("operationFailed");

            closeRemoveMemberModal();

            return;
        }

        await loadMembers();

        resetSelectedMemberState();

        messageBox.style.color = "#5CFFB2";
        messageBox.innerText = t("removeMemberSuccess");

        closeRemoveMemberModal();

    } catch (error) {
        console.error(error);

        messageBox.innerText = t("operationFailed");

        closeRemoveMemberModal();
    }
}
function updateAliasPanel(member) {
    const input = document.getElementById("alias-input");
    const messageBox = document.getElementById("alias-message");
    if (!input || !messageBox) return;

    messageBox.innerText = "";
    // 显示当前备注值（纯备注，不含昵称）
    input.value = member.alias || "";
}


function resetAliasPanel() {
    const input = document.getElementById("alias-input");
    const messageBox = document.getElementById("alias-message");
    if (input) input.value = "";
    if (messageBox) messageBox.innerText = "";
}


async function saveAlias() {
    const input = document.getElementById("alias-input");
    const messageBox = document.getElementById("alias-message");

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    if (!selectedMember) {
        messageBox.innerText = t("pleaseSelectMember");
        return;
    }

    const alias = input.value.trim();

    const formData = new FormData();
    formData.append("target_user_id", selectedMember.id);
    formData.append("alias", alias);

    try {
        const response = await fetch("/organizer/save-member-alias", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (!data.success) {
            messageBox.innerText = data.message || t("operationFailed");
            return;
        }

        // 刷新成员列表以更新显示
        await loadMembers();

        messageBox.style.color = "#5CFFB2";
        messageBox.innerText = alias === "" ? t("aliasClearedSuccess") : t("aliasSavedSuccess");

    } catch (error) {
        console.error(error);
        messageBox.innerText = t("operationFailed");
    }
}

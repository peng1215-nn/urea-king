// 设为局头：每组最多 2 个局头，两人权限相同；设了以后不能撤销，只能由对方自己卸任，
// 所以点按钮后要再确认一次。

let pendingPromoteMember = null;


function _promoteMessage(text, success) {
    const box = document.getElementById("promote-member-message");
    if (!box) return;
    box.style.color = success ? "#5CFFB2" : "#ff8a8a";
    box.innerText = text || "";
}


function updatePromoteMemberPanel(member) {
    const button = document.getElementById("promote-member-button");
    _promoteMessage("");

    if (member.role === "organizer") {
        button.disabled = true;
        _promoteMessage(t("memberAlreadyOrganizer"));
        return;
    }
    if (organizerCount >= maxOrganizers) {
        button.disabled = true;
        _promoteMessage(t("organizerLimitReached").replace("{limit}", maxOrganizers));
        return;
    }
    button.disabled = false;
}


function resetPromoteMemberPanel() {
    document.getElementById("promote-member-button").disabled = false;
    _promoteMessage("");
}


function openPromoteMemberModal() {
    _promoteMessage("");

    if (!selectedMember) {
        _promoteMessage(t("pleaseSelectMember"));
        return;
    }
    if (selectedMember.role === "organizer") {
        _promoteMessage(t("memberAlreadyOrganizer"));
        return;
    }

    pendingPromoteMember = selectedMember;
    const name = selectedMember.alias
        ? `${selectedMember.nickname}（${selectedMember.alias}）`
        : (selectedMember.nickname || selectedMember.username);
    document.getElementById("promote-member-text").innerText = t("promoteOrganizerConfirmText")
        .replace("{name}", name)
        .replace("{username}", selectedMember.username)
        .replace("{limit}", maxOrganizers);
    document.getElementById("promote-member-confirm").disabled = false;
    document.getElementById("promote-member-modal").style.display = "flex";
}


function closePromoteMemberModal() {
    document.getElementById("promote-member-modal").style.display = "none";
    pendingPromoteMember = null;
}


async function confirmPromoteMember() {
    if (!pendingPromoteMember) {
        closePromoteMemberModal();
        return;
    }

    const confirmButton = document.getElementById("promote-member-confirm");
    if (confirmButton.disabled) return;
    confirmButton.disabled = true;

    const formData = new FormData();
    formData.append("target_user_id", pendingPromoteMember.id);

    let data;
    try {
        const response = await fetch("/organizer/promote-member", { method: "POST", body: formData });
        data = await response.json();
    } catch (error) {
        data = { success: false, message: "operationFailed" };
    }

    closePromoteMemberModal();

    if (!data.success) {
        _promoteMessage(t(data.message || "operationFailed").replace("{limit}", data.limit || maxOrganizers));
        return;
    }

    await loadMembers();
    resetSelectedMemberState();
    _promoteMessage(t("promoteOrganizerSuccess"), true);
}

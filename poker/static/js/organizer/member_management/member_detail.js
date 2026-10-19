function selectMember(member, rowElement) {
    selectedMember = member;

    document
        .querySelectorAll("#user-table-body tr")
        .forEach(row => row.classList.remove("active"));

    rowElement.classList.add("active");

    const isActive = parseInt(member.is_active) === 1;

    setDetailText("detail-username",   member.username   || "--");
    setDetailText("detail-nickname",   member.nickname   || "--");
    setDetailText("detail-role",       member.role       || "--");
    setDetailText("detail-group",      member.group_name || "--");
    setDetailText("detail-created-at", member.created_at || "--");
    setDetailText(
        "detail-status",
        isActive ? t("accountEnabled") : t("accountDisabled")
    );

    updateRemoveMemberPanel(member);
}


function resetSelectedMemberState() {
    selectedMember = null;

    document
        .querySelectorAll("#user-table-body tr")
        .forEach(row => row.classList.remove("active"));

    setDetailText("detail-username",   "--");
    setDetailText("detail-nickname",   "--");
    setDetailText("detail-role",       "--");
    setDetailText("detail-group",      "--");
    setDetailText("detail-created-at", "--");
    setDetailText("detail-status",     "--");

    resetRemoveMemberPanel();
}


function refreshSelectedMemberLanguage() {
    if (!selectedMember) {
        resetSelectedMemberState();
        return;
    }

    const isActive = parseInt(selectedMember.is_active) === 1;

    setDetailText(
        "detail-status",
        isActive ? t("accountEnabled") : t("accountDisabled")
    );

    updateRemoveMemberPanel(selectedMember);
}


function setDetailText(elementId, value) {
    const element = document.getElementById(elementId);

    if (!element) return;

    element.innerHTML = `
        <span
            class="truncate-text detail-truncate"
            title="${value}"
        >
            ${value}
        </span>
    `;
}
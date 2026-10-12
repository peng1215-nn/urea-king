async function fetchGroupOptions() {

    const response = await fetch(
        "/admin/groups/options"
    );

    return await response.json();
}


async function fetchDeletableGroupOptions() {

    const response = await fetch(
        "/admin/groups/deletable-options"
    );

    return await response.json();
}


async function fetchUnusedInvitationOptions() {

    const response = await fetch(
        "/admin/invitation-codes/options"
    );

    return await response.json();
}
async function forceDeleteGroupRequest(groupId, groupCode) {
    const form = new FormData();
    form.append("group_id", groupId);
    form.append("group_code", groupCode);
    const response = await fetch("/admin/groups/force-delete", {method: "POST", body: form});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
}

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
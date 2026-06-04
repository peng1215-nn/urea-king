async function fetchInviteCodes() {
    const res = await fetch("/organizer/invite/list");
    return await res.json();
}

async function apiCreateInviteCode(code) {
    const fd = new FormData();
    fd.append("code", code);
    const res = await fetch("/organizer/invite/create", { method: "POST", body: fd });
    return await res.json();
}

async function apiDeleteInviteCode(inviteId) {
    const fd = new FormData();
    fd.append("invite_id", inviteId);
    const res = await fetch("/organizer/invite/delete", { method: "POST", body: fd });
    return await res.json();
}
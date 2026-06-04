function openJoinGroupModal() {
    document.getElementById("join-group-modal").style.display = "flex";
}

function closeJoinGroupModal() {
    document.getElementById("join-group-modal").style.display = "none";
}

async function confirmJoinGroup() {
    await fetch("/logout");
    window.location.replace("/group-join");
}
function openJoinGroupModal() {
    const modal = document.getElementById("join-group-modal");
    if (modal) {
        modal.style.display = "flex";
    }
}


function closeJoinGroupModal() {
    const modal = document.getElementById("join-group-modal");
    if (modal) {
        modal.style.display = "none";
    }
}


function confirmJoinGroup() {
    window.location.href = "/organizer/logout-to-join";
}
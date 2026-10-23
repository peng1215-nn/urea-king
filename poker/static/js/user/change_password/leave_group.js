// 普通用户退出当前组
function openLeaveGroupModal() {
    document.getElementById("leave-group-modal").style.display = "flex";
}

function closeLeaveGroupModal() {
    const modal = document.getElementById("leave-group-modal");
    if (modal) {
        modal.style.display = "none";
    }
}

async function confirmLeaveGroup() {
    const button = document.getElementById("leave-group-confirm");
    const messageBox = document.getElementById("leave-group-message");

    button.disabled = true;
    messageBox.innerText = "";
    messageBox.style.color = "#ff7b7b";

    try {
        const response = await fetch("/user/leave-group", { method: "POST" });
        const data = await response.json();

        closeLeaveGroupModal();

        if (!data.success) {
            messageBox.innerText = t(data.message || "leaveGroupFailed");
            button.disabled = false;
            return;
        }

        messageBox.style.color = "#5cffb2";
        messageBox.innerText = t("leaveGroupSuccess");

        setTimeout(function () {
            window.location.replace("/login");
        }, 1400);

    } catch (error) {
        console.error(error);
        closeLeaveGroupModal();
        messageBox.innerText = t("leaveGroupFailed");
        button.disabled = false;
    }
}

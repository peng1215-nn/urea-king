function showMessage(message, success = false) {
    const box = document.getElementById("message-box");

    box.innerText = message;
    box.style.display = "block";

    if (success) {
        box.className = "message-box success-message";
    } else {
        box.className = "message-box error-message";
    }
}

function resetMessage() {
    const box = document.getElementById("message-box");

    box.innerText = "";
    box.style.display = "none";
    box.className = "message-box";
}
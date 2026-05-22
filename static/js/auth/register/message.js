function showMessage(message, success = false) {
    const box = document.getElementById("message-box");

    box.innerText = message;

    if (success) {
        box.style.color = "#5CFFB2";
    } else {
        box.style.color = "#FF6B6B";
    }
}

function resetMessage() {
    const box = document.getElementById("message-box");

    box.innerText = "";
    box.style.color = "";
}
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


// 提示后面附一个操作链接（如邮箱未验证时的“重发验证邮件”）
function showMessageWithLink(message, linkText, href) {
    showMessage(message, false);

    const box = document.getElementById("message-box");
    const link = document.createElement("a");

    link.className = "message-action-link";
    link.href = href;
    link.textContent = linkText;

    box.appendChild(document.createElement("br"));
    box.appendChild(link);
}


function showNotice(message) {
    const box = document.getElementById("message-box");

    box.innerText = message;
    box.style.display = "block";
    box.className = "message-box notice-message";
}


function resetMessage() {
    const box = document.getElementById("message-box");

    box.innerText = "";
    box.style.display = "none";
    box.className = "message-box";
}

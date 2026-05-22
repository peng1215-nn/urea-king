function getLoginFormData() {
    return {
        username: document.getElementById("username").value.trim(),
        password: document.getElementById("password").value
    };
}

function validateLoginForm(username, password) {
    if (username.length === 0) {
        showMessage("请输入用户名。");
        return false;
    }

    if (password.length === 0) {
        showMessage("请输入密码。");
        return false;
    }

    return true;
}

function buildLoginFormData(username, password) {
    const formData = new FormData();

    formData.append("username", username);
    formData.append("password", password);

    return formData;
}
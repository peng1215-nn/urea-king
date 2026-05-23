function getLoginFormData() {
    return {
        username: document.getElementById("username").value.trim(),
        password: document.getElementById("password").value
    };
}


function validateLoginForm(username, password) {
    if (username.length === 0) {
        showMessage(t("loginUsernameRequired"), false);
        return false;
    }

    if (password.length === 0) {
        showMessage(t("loginPasswordRequired"), false);
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
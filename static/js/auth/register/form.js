function getRegisterFormData() {
    return {
        username: document.getElementById("username").value.trim(),
        nickname: document.getElementById("nickname").value.trim(),
        password: document.getElementById("password").value,
        confirmPassword: document.getElementById("confirm-password").value,
        inviteCode: document.getElementById("invite-code").value.trim()
    };
}

function validateRegisterForm(form) {
    const usernamePattern = /^[A-Za-z][A-Za-z0-9_]{4,}$/;

    if (!usernamePattern.test(form.username)) {
        showMessage("用户名必须以字母开头，且至少 5 位，只能包含字母、数字和下划线。");
        return false;
    }

    if (form.nickname.length === 0) {
        showMessage("昵称不能为空。");
        return false;
    }

    if (form.password.length < 6) {
        showMessage("密码长度必须大于等于 6 位。");
        return false;
    }

    if (form.password !== form.confirmPassword) {
        showMessage("两次输入的密码不一致。");
        return false;
    }

    if (form.inviteCode.length === 0) {
        showMessage("请输入邀请码。");
        return false;
    }

    return true;
}

function buildRegisterFormData(form) {
    const formData = new FormData();

    formData.append("username", form.username);
    formData.append("nickname", form.nickname);
    formData.append("password", form.password);
    formData.append("confirm_password", form.confirmPassword);
    formData.append("invite_code", form.inviteCode);

    return formData;
}
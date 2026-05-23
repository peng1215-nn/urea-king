function getRegisterFormData() {
    return {
        username:
            document
                .getElementById("username")
                .value
                .trim(),

        nickname:
            document
                .getElementById("nickname")
                .value
                .trim(),

        password:
            document
                .getElementById("password")
                .value,

        confirmPassword:
            document
                .getElementById("confirm-password")
                .value,

        inviteCode:
            document
                .getElementById("invite-code")
                .value
                .trim(),
    };
}


function validateRegisterForm(form) {
    const usernamePattern =
        /^[A-Za-z][A-Za-z0-9_]{4,}$/;

    if (!usernamePattern.test(form.username)) {
        showMessage(
            t("usernameRule"),
        );

        return false;
    }

    if (form.nickname.length === 0) {
        showMessage(
            t("nicknameRequired"),
        );

        return false;
    }

    if (form.password.length < 6) {
        showMessage(
            t("passwordTooShort"),
        );

        return false;
    }

    if (
        form.password
        !==
        form.confirmPassword
    ) {
        showMessage(
            t("passwordMismatch"),
        );

        return false;
    }

    if (form.inviteCode.length === 0) {
        showMessage(
            t("inviteCodeRequired"),
        );

        return false;
    }

    return true;
}


function buildRegisterFormData(form) {
    const formData = new FormData();

    formData.append(
        "username",
        form.username,
    );

    formData.append(
        "nickname",
        form.nickname,
    );

    formData.append(
        "password",
        form.password,
    );

    formData.append(
        "confirm_password",
        form.confirmPassword,
    );

    formData.append(
        "invite_code",
        form.inviteCode,
    );

    return formData;
}
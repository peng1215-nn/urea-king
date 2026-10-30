let registerSubmitting = false;

async function register() {
    if (registerSubmitting) {
        return;
    }

    const form = getRegisterFormData();

    if (!validateRegisterForm(form)) {
        return;
    }

    const formData =
        buildRegisterFormData(form);

    const button = document.getElementById("register-button");

    registerSubmitting = true;
    authSetBusy(button, true);

    try {
        const response = await fetch("/register", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (data.success === true) {
            // 注册成功：显示"请查收验证邮件"提示，隐藏注册按钮，避免重复提交
            showMessage(
                t("registerSuccess"),
                true,
            );

            if (button) button.style.display = "none";

            return;
        }

        showMessage(
            authMessage(data.error_code || "registerFailed", data),
            false,
        );

    } catch (error) {
        console.error(error);

        showMessage(
            t("registerFailed"),
            false,
        );

    } finally {
        registerSubmitting = false;
        authSetBusy(button, false);
    }
}

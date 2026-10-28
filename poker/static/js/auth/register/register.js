async function register() {
    const form = getRegisterFormData();

    if (!validateRegisterForm(form)) {
        return;
    }

    const formData =
        buildRegisterFormData(form);

    try {
        const response = await fetch("/register", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (data.success === true) {
            // 注册成功：显示"请查收验证邮件"提示，隐藏表单
            showMessage(
                t("registerSuccess"),
                true,
            );

            // 隐藏注册按钮，避免重复提交
            const btn = document.querySelector(".register-button");
            if (btn) btn.style.display = "none";

            return;
        }

        showMessage(
            t(data.error_code || "registerFailed"),
            false,
        );

    } catch (error) {
        console.error(error);

        showMessage(
            t("registerFailed"),
            false,
        );
    }
}

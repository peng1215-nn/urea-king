async function register() {
    const form = getRegisterFormData();

    if (!validateRegisterForm(form)) {
        return;
    }

    const formData = buildRegisterFormData(form);

    try {
        const response = await fetch("/register", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        showMessage(data.message, data.success);

        if (data.success) {
            redirectToLogin();
        }

    } catch (error) {
        console.error(error);
        showMessage("注册请求失败。");
    }
}
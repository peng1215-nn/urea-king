async function login() {
    const { username, password } = getLoginFormData();

    if (!validateLoginForm(username, password)) {
        return;
    }

    const formData = buildLoginFormData(username, password);

    try {
        const response = await fetch("/login", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        showMessage(data.message, data.success);

        if (data.success) {
            redirectByRole(data.role);
        }

    } catch (error) {
        console.error(error);
        showMessage("登录请求失败。");
    }
}
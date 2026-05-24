async function login() {
    const { username, password } =
        getLoginFormData();

    if (!validateLoginForm(username, password)) {
        return;
    }

    const formData =
        buildLoginFormData(username, password);

    try {
        const response = await fetch("/login", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (data.success === true) {
            showMessage(
                `${data.display_name}·${t("loginSuccess")}`,
                true
            );

            sessionStorage.setItem(
                "available_groups",
                JSON.stringify(data.groups || [])
            );

            setTimeout(() => {
                window.location.href = "/group-select";
                }, 3000);

            return;
        }

        showMessage(
            t(data.error_code || "loginFailed"),
            false,
        );

    } catch (error) {
        console.error(error);

        showMessage(
            t("loginFailed"),
            false,
        );
    }
}
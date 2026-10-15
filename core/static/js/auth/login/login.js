async function login() {
    const { username, password } =
        getLoginFormData();

    if (!validateLoginForm(username, password)) {
        return;
    }

    const formData =
        buildLoginFormData(username, password);

    try {
        const response = await fetch("/poker/login", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (data.success === true) {
            showMessage(
                `${data.display_name} ${t("loginSuccess")}`,
                true
            );

            const groups = data.groups || [];
            sessionStorage.setItem(
                "available_groups",
                JSON.stringify(groups)
            );

            setTimeout(() => {
                if (groups.length === 0) {
                    window.location.href = "/group-join";
                } else {
                    window.location.href = "/group-select";
                }
            }, 1500);

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
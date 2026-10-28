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
                `${data.display_name} ${t("loginSuccess")}`,
                true
            );

            sessionStorage.setItem(
                "available_groups",
                JSON.stringify(data.groups || [])
            );

            // 没有任何组时引导创建或加入
            if (!data.has_groups) {
                sessionStorage.setItem("login_no_group", "1");
            } else {
                sessionStorage.removeItem("login_no_group");
            }

            setTimeout(() => {
                window.location.href = "/group-select";
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

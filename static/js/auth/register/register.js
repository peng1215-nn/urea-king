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
            showMessage(
                `${t(data.error_code || "registerSuccess")} ${data.nickname}。`,
                true,
            );

            redirectToLogin();

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
let loginSubmitting = false;

async function login() {
    if (loginSubmitting) {
        return;
    }

    const { username, password } =
        getLoginFormData();

    if (!validateLoginForm(username, password)) {
        return;
    }

    const formData =
        buildLoginFormData(username, password);

    const button = document.getElementById("login-button");
    let redirecting = false;

    loginSubmitting = true;
    authSetBusy(button, true);

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

            redirecting = true;

            setTimeout(() => {
                window.location.href = "/group-select";
            }, 1500);

            return;
        }

        const errorCode = data.error_code || data.message || "loginFailed";

        if (errorCode === "loginEmailNotVerified") {
            showMessageWithLink(
                t(errorCode),
                t("resendVerifyLink"),
                "/register#resend"
            );
            return;
        }

        showMessage(
            authMessage(errorCode, data),
            false,
        );

    } catch (error) {
        console.error(error);

        showMessage(
            t("loginFailed"),
            false,
        );

    } finally {
        // 登录成功、即将跳转时保持禁用，避免重复提交
        if (!redirecting) {
            loginSubmitting = false;
            authSetBusy(button, false);
        }
    }
}

async function loadCurrentAccount() {
    const messageBox =
        document.getElementById("nickname-message");

    try {
        const data =
            await fetchCurrentAccount();

        if (!data.success || !data.user) {
            messageBox.innerText =
                t(data.message || "operationFailed");

            return;
        }

        document.getElementById(
            "current-nickname"
        ).value =
            data.user.nickname ||
            data.user.username ||
            "";

        document.getElementById(
            "new-nickname"
        ).value = "";

    } catch (error) {
        console.error(error);

        messageBox.innerText =
            t("operationFailed");
    }
}


document.addEventListener(
    "DOMContentLoaded",
    async function () {
        applyLanguage();

        await loadCurrentAccount();
    }
);
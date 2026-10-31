// 卸任局头：确认后变回普通成员，登录状态失效，回到登录页重新进入。

function _stepDownMessage(text, success) {
    const box = document.getElementById("step-down-message");
    box.style.color = success ? "#5CFFB2" : "#ff8a8a";
    box.innerText = text || "";
}

function openStepDownModal() {
    _stepDownMessage("");
    document.getElementById("step-down-confirm").disabled = false;
    document.getElementById("step-down-modal").style.display = "flex";
}

function closeStepDownModal() {
    document.getElementById("step-down-modal").style.display = "none";
}

async function confirmStepDown() {
    const button = document.getElementById("step-down-confirm");
    if (button.disabled) return;
    button.disabled = true;

    let data;
    try {
        const response = await fetch("/organizer/step-down", { method: "POST" });
        data = await response.json();
    } catch (error) {
        data = { success: false, message: "operationFailed" };
    }

    closeStepDownModal();

    if (!data.success) {
        _stepDownMessage(t(data.message || "operationFailed"));
        return;
    }

    _stepDownMessage(t("stepDownSuccess"), true);
    setTimeout(() => { window.location.href = "/login"; }, 1500);
}

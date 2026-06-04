async function fetchCurrentAccount() {
    const response = await fetch("/organizer/change-password/current");
    return await response.json();
}

async function updateNicknameApi(nickname) {
    const formData = new FormData();
    formData.append("nickname", nickname);

    const response = await fetch("/organizer/change-password/update-nickname", {
        method: "POST",
        body: formData,
    });

    return await response.json();
}

async function updatePasswordApi(currentPassword, newPassword, confirmPassword) {
    const formData = new FormData();
    formData.append("current_password", currentPassword);
    formData.append("new_password", newPassword);
    formData.append("confirm_password", confirmPassword);

    const response = await fetch("/organizer/change-password/update-password", {
        method: "POST",
        body: formData,
    });

    return await response.json();
}
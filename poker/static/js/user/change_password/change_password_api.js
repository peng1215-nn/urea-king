async function fetchCurrentAccount() {
    const res = await fetch("/user/change-password/current");
    return await res.json();
}

async function apiUpdateNickname(nickname) {
    const fd = new FormData();
    fd.append("nickname", nickname);
    const res = await fetch("/user/change-password/update-nickname", { method: "POST", body: fd });
    return await res.json();
}

async function apiUpdatePassword(currentPassword, newPassword, confirmPassword) {
    const fd = new FormData();
    fd.append("current_password", currentPassword);
    fd.append("new_password", newPassword);
    fd.append("confirm_password", confirmPassword);
    const res = await fetch("/user/change-password/update-password", { method: "POST", body: fd });
    return await res.json();
}
function validateAvatarFile(file) {
    const allowedTypes = [
        "image/jpeg",
        "image/png",
        "image/webp",
    ];

    if (!allowedTypes.includes(file.type)) {
        alert(avatarText("avatarInvalidType"));

        return false;
    }

    return true;
}

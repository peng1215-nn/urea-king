function redirectByRole(role) {
    setTimeout(() => {
        if (role === "admin") {
            window.location.replace("/admin-dashboard");

        } else if (role === "organizer") {
            window.location.replace("/organizer-dashboard");

        } else {
            window.location.replace("/user-dashboard");
        }
    }, 3000);
}
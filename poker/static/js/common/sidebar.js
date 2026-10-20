function toggleSidebar() {
    const sidebar = document.querySelector(".sidebar");
    const overlay = document.querySelector(".sidebar-overlay");
    if (!sidebar) return;
    sidebar.classList.toggle("open");
    overlay.classList.toggle("active");
}

function closeSidebar() {
    const sidebar = document.querySelector(".sidebar");
    const overlay = document.querySelector(".sidebar-overlay");
    if (!sidebar) return;
    sidebar.classList.remove("open");
    overlay.classList.remove("active");
}

// Close sidebar on navigation (menu item click)
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".menu-item").forEach(function (item) {
        item.addEventListener("click", function () {
            closeSidebar();
        });
    });
});

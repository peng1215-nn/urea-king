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

// Mobile topbar: inject row-break div between upload-button and avatar
// so first row = language + upload-avatar, second row = avatar + role-tag
(function injectTopbarBreak() {
    function doInject() {
        if (window.innerWidth > 768) return;
        const actions = document.querySelector('.topbar-actions');
        if (!actions || actions.querySelector('.topbar-row-break')) return;
        const avatar = actions.querySelector('.avatar');
        if (!avatar) return;
        const br = document.createElement('div');
        br.className = 'topbar-row-break';
        actions.insertBefore(br, avatar);
    }
    document.addEventListener('DOMContentLoaded', doInject);
    window.addEventListener('resize', doInject);
})();

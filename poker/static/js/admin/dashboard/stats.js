async function loadAdminStats() {
    try {
        const response = await fetch("/admin/stats");
        const data = await response.json();

        if (!data.success) {
            return;
        }

        document.getElementById("total-users").innerText =
            data.total_users;

        document.getElementById("total-groups").innerText =
            data.total_groups;

        document.getElementById("admin-count").innerText =
            data.admin_count;

        document.getElementById("organizer-count").innerText =
            data.organizer_count;

        document.getElementById("user-count").innerText =
            data.user_count;

        document.getElementById("unused-invite-count").innerText =
            data.unused_invitation_codes;

    } catch (error) {
        console.error("加载管理员统计数据失败：", error);
    }
}
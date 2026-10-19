function escapeHtml(value) {
    return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function renderAnnouncements(announcements) {
    const list =
        document.getElementById("announcement-list");

    list.innerHTML = "";

    if (!announcements || announcements.length === 0) {
        list.innerHTML = `
            <div class="empty-announcement">
                ${t("noAnnouncements")}
            </div>
        `;

        renderAnnouncementPagination();

        return;
    }

    const page =
        window.announcementState.page;

    const pageSize =
        window.announcementState.pageSize;

    const startIndex =
        (page - 1) * pageSize;

    const currentPageItems =
        announcements.slice(
            startIndex,
            startIndex + pageSize
        );

    currentPageItems.forEach(announcement => {
        const item =
            document.createElement("div");

        item.className =
            "announcement-item";

        item.innerHTML = `
            <div class="announcement-header">
                <div class="announcement-title">
                    ${escapeHtml(announcement.title)}
                </div>

                <div class="announcement-time">
                    ${escapeHtml(announcement.created_at)}
                </div>
            </div>

            <div class="announcement-content">
                ${escapeHtml(announcement.content)}
            </div>

            <div class="announcement-actions">
                <button
                    class="announcement-action-button edit"
                    onclick="startEditAnnouncement(${announcement.id})"
                >
                    ${t("edit")}
                </button>

                <button
                    class="announcement-action-button delete"
                    onclick="openDeleteAnnouncementModal(${announcement.id})"
                >
                    ${t("delete")}
                </button>
            </div>
        `;

        list.appendChild(item);
    });

    renderAnnouncementPagination();
}


function renderAnnouncementPagination() {
    const total =
        window.announcementState.announcements.length;

    const page =
        window.announcementState.page;

    const pageSize =
        window.announcementState.pageSize;

    const totalPages =
        Math.max(
            Math.ceil(total / pageSize),
            1
        );

    document.getElementById(
        "announcement-pagination-info"
    ).innerText =
        `${page} / ${totalPages}`;

    document.getElementById(
        "announcement-previous-button"
    ).disabled =
        page <= 1;

    document.getElementById(
        "announcement-next-button"
    ).disabled =
        page >= totalPages;
}
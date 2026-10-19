async function fetchAnnouncements() {
    const response =
        await fetch("/admin/announcements");

    return await response.json();
}


async function createAnnouncementApi(
    title,
    content,
) {
    const formData =
        new FormData();

    formData.append(
        "title",
        title
    );

    formData.append(
        "content",
        content
    );

    const response =
        await fetch(
            "/admin/announcements/create",
            {
                method: "POST",
                body: formData,
            }
        );

    return await response.json();
}


async function updateAnnouncementApi(
    announcementId,
    title,
    content,
) {
    const formData =
        new FormData();

    formData.append(
        "announcement_id",
        announcementId
    );

    formData.append(
        "title",
        title
    );

    formData.append(
        "content",
        content
    );

    const response =
        await fetch(
            "/admin/announcements/update",
            {
                method: "POST",
                body: formData,
            }
        );

    return await response.json();
}


async function deleteAnnouncementApi(
    announcementId,
) {
    const formData =
        new FormData();

    formData.append(
        "announcement_id",
        announcementId
    );

    const response =
        await fetch(
            "/admin/announcements/delete",
            {
                method: "POST",
                body: formData,
            }
        );

    return await response.json();
}
async function loadAnnouncements() {
    const messageBox =
        document.getElementById(
            "announcement-list-message"
        );

    messageBox.innerText = "";

    try {
        const data =
            await fetchAnnouncements();

        if (!data.success) {
            messageBox.innerText =
                t(data.message || "operationFailed");

            return;
        }

        window.announcementState.announcements =
            data.announcements;

        window.announcementState.page = 1;

        renderAnnouncements(
            data.announcements
        );

    } catch (error) {
        console.error(error);

        messageBox.innerText =
            t("operationFailed");
    }
}


async function saveAnnouncement() {
    const titleInput =
        document.getElementById(
            "announcement-title"
        );

    const contentInput =
        document.getElementById(
            "announcement-content"
        );

    const messageBox =
        document.getElementById(
            "announcement-form-message"
        );

    const title =
        titleInput.value.trim();

    const content =
        contentInput.value.trim();

    messageBox.innerText = "";
    messageBox.style.color = "#ff8a8a";

    if (!title) {
        messageBox.innerText =
            t("announcementTitleRequired");

        return;
    }

    if (!content) {
        messageBox.innerText =
            t("announcementContentRequired");

        return;
    }

    try {
        let data;

        if (window.announcementState.editingId) {
            data =
                await updateAnnouncementApi(
                    window.announcementState.editingId,
                    title,
                    content
                );
        } else {
            data =
                await createAnnouncementApi(
                    title,
                    content
                );
        }

        if (!data.success) {
            messageBox.innerText =
                t(data.message || "operationFailed");

            return;
        }

        messageBox.style.color =
            "#5CFFB2";

        messageBox.innerText =
            window.announcementState.editingId
                ? t("announcementUpdateSuccess")
                : t("announcementCreateSuccess");

        resetAnnouncementForm();

        await loadAnnouncements();

    } catch (error) {
        console.error(error);

        messageBox.innerText =
            t("operationFailed");
    }
}


function startEditAnnouncement(
    announcementId,
) {
    const announcement =
        window.announcementState
            .announcements
            .find(item => item.id === announcementId);

    if (!announcement) {
        return;
    }

    window.announcementState.editingId =
        announcement.id;

    document.getElementById(
        "announcement-title"
    ).value =
        announcement.title;

    document.getElementById(
        "announcement-content"
    ).value =
        announcement.content;

    document.getElementById(
        "announcement-form-title"
    ).innerText =
        t("editAnnouncement");

    document.getElementById(
        "save-announcement-button"
    ).innerText =
        t("saveChanges");

    document.getElementById(
        "cancel-edit-button"
    ).classList.remove("hidden");

    document.getElementById(
        "announcement-form-message"
    ).innerText = "";
}


function cancelEditAnnouncement() {
    resetAnnouncementForm();
}


function resetAnnouncementForm() {
    window.announcementState.editingId =
        null;

    document.getElementById(
        "announcement-title"
    ).value = "";

    document.getElementById(
        "announcement-content"
    ).value = "";

    document.getElementById(
        "announcement-form-title"
    ).innerText =
        t("createAnnouncement");

    document.getElementById(
        "save-announcement-button"
    ).innerText =
        t("publishAnnouncement");

    document.getElementById(
        "cancel-edit-button"
    ).classList.add("hidden");
}


function openDeleteAnnouncementModal(
    announcementId,
) {
    window.announcementState.deletingId =
        announcementId;

    document.getElementById(
        "delete-announcement-modal"
    ).classList.remove("hidden");
}


function closeDeleteAnnouncementModal() {
    window.announcementState.deletingId =
        null;

    document.getElementById(
        "delete-announcement-modal"
    ).classList.add("hidden");
}


async function confirmDeleteAnnouncement() {
    const messageBox =
        document.getElementById(
            "announcement-list-message"
        );

    const announcementId =
        window.announcementState.deletingId;

    closeDeleteAnnouncementModal();

    if (!announcementId) {
        return;
    }

    try {
        const data =
            await deleteAnnouncementApi(
                announcementId
            );

        if (!data.success) {
            messageBox.style.color =
                "#ff8a8a";

            messageBox.innerText =
                t(data.message || "operationFailed");

            return;
        }

        messageBox.style.color =
            "#5CFFB2";

        messageBox.innerText =
            t("announcementDeleteSuccess");

        await loadAnnouncements();

    } catch (error) {
        console.error(error);

        messageBox.style.color =
            "#ff8a8a";

        messageBox.innerText =
            t("operationFailed");
    }
}


function goToPreviousAnnouncementPage() {
    if (window.announcementState.page <= 1) {
        return;
    }

    window.announcementState.page -= 1;

    renderAnnouncements(
        window.announcementState.announcements
    );
}


function goToNextAnnouncementPage() {
    const total =
        window.announcementState.announcements.length;

    const totalPages =
        Math.max(
            Math.ceil(
                total / window.announcementState.pageSize
            ),
            1
        );

    if (window.announcementState.page >= totalPages) {
        return;
    }

    window.announcementState.page += 1;

    renderAnnouncements(
        window.announcementState.announcements
    );
}
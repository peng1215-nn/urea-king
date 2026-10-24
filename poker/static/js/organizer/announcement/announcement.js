// 原来写在页面里的内联脚本，移到单独文件（安全策略禁止内联脚本）
async function loadAnnouncements() {
    const res = await fetch("/organizer/announcements");
    const data = await res.json();
    const list = document.getElementById("announcement-list");

    if (!data.success || !data.announcements || data.announcements.length === 0) {
        list.innerHTML = `<div class="announcement-empty">${t("noAnnouncements")}</div>`;
        return;
    }

    list.innerHTML = "";
    data.announcements.forEach(a => {
        const card = document.createElement("div");
        card.className = "announcement-card";
        const preview = a.content.length > 100 ? a.content.slice(0, 100) + "..." : a.content;
        card.innerHTML = `
            <div class="announcement-card-header">
                <div class="announcement-card-title">${escapeHtml(a.title)}</div>
                <div class="announcement-card-date">${escapeHtml(a.updated_at || a.created_at)}</div>
            </div>
            <div class="announcement-card-preview">${escapeHtml(preview)}</div>
        `;
        card.onclick = () => openDetailModal(a);
        list.appendChild(card);
    });
}

function openDetailModal(a) {
    document.getElementById("detail-title").innerText = a.title;
    document.getElementById("detail-date").innerText = a.updated_at || a.created_at;
    document.getElementById("detail-content").innerText = a.content;
    document.getElementById("announcement-detail-modal").style.display = "flex";
}

function closeDetailModal() {
    document.getElementById("announcement-detail-modal").style.display = "none";
}

window.addEventListener("pageshow", function () {
    closeJoinGroupModal();
    applyLanguage();
    loadCurrentUser();
    loadAnnouncements();
});

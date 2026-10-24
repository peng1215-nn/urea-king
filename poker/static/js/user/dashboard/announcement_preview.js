// 原来写在页面里的内联脚本，移到单独文件（安全策略禁止内联脚本）
async function loadAnnouncementPreview() {
    const res = await fetch("/user/announcements");
    const data = await res.json();
    const list = document.getElementById("announcement-preview-list");
    if (!data.success || !data.announcements || data.announcements.length === 0) {
        list.innerHTML = `<div class="announcement-empty" data-i18n="noAnnouncements">${t("noAnnouncements")}</div>`;
        return;
    }
    list.innerHTML = "";
    const a = data.announcements[0];
    const item = document.createElement("div");
    item.className = "announcement-preview-item";
    const titleText = a.title.length > 30 ? a.title.slice(0, 30) + "..." : a.title;
    const contentText = a.content.length > 50 ? a.content.slice(0, 50) + "..." : a.content;
    item.innerHTML = `
        <div class="announcement-preview-title">${escapeHtml(titleText)}</div>
        <div class="announcement-preview-content">${escapeHtml(contentText)}</div>
        <div class="announcement-preview-date">${escapeHtml(a.updated_at || a.created_at)}</div>
    `;
    list.appendChild(item);
}

window.addEventListener("pageshow", function (e) {
    if (e.persisted) {
        window.location.reload();
        return;
    }
    closeJoinGroupModal();
    applyLanguage();
    loadCurrentUser();
    loadAnnouncementPreview();
});

// 语言切换后重新渲染公告
const _origApplyLanguage = window.applyLanguage;
window.applyLanguage = function(lang) {
    _origApplyLanguage(lang);
    loadAnnouncementPreview();
};

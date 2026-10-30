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

// ── 全部公告弹窗：点公告卡片打开，按时间从新到旧显示每条公告的完整内容 ──

let announcementsModalOpen = false;
let announcementsLastFocus = null;
let announcementsRequestSeq = 0;

function announcementDateText(a) {
    const created = a.created_at || "";
    // 接口里的时间精确到分钟；和发布时间不同才算编辑过
    if (a.updated_at && a.updated_at !== created) {
        return `${created} · ${t("announcementEdited")} ${a.updated_at}`;
    }
    return created;
}

function renderAnnouncementsModalList(data) {
    const list = document.getElementById("announcements-modal-list");
    if (!data || !data.success) {
        const key = data && data.message ? data.message : "connectionLostFirst";
        list.innerHTML = `<div class="announcements-modal-empty">${escapeHtml(t(key))}</div>`;
        return;
    }
    const items = data.announcements || [];
    if (items.length === 0) {
        list.innerHTML = `<div class="announcements-modal-empty">${escapeHtml(t("noAnnouncements"))}</div>`;
        return;
    }
    list.innerHTML = items.map(a => `
        <article class="announcements-modal-item">
            <div class="announcements-modal-item-title">${escapeHtml(a.title)}</div>
            <div class="announcements-modal-item-date">${escapeHtml(announcementDateText(a))}</div>
            <div class="announcements-modal-item-content">${escapeHtml(a.content)}</div>
        </article>
    `).join("");
}

async function loadAnnouncementsModalList() {
    const seq = ++announcementsRequestSeq;
    const list = document.getElementById("announcements-modal-list");
    list.innerHTML = `<div class="announcements-modal-empty">${escapeHtml(t("loading"))}</div>`;
    let data;
    try {
        const res = await fetch("/user/announcements");
        data = await res.json();
    } catch (error) {
        data = null;
    }
    // 已关闭或又打开了一次：丢掉过期的结果
    if (seq !== announcementsRequestSeq || !announcementsModalOpen) return;
    renderAnnouncementsModalList(data);
}

function openAnnouncementsModal() {
    if (announcementsModalOpen) return;
    announcementsModalOpen = true;
    announcementsLastFocus = document.activeElement;
    const modal = document.getElementById("announcements-modal");
    modal.style.display = "flex";
    document.body.classList.add("modal-open");
    document.getElementById("announcements-modal-list").scrollTop = 0;
    const closeBtn = document.getElementById("announcements-close-button");
    if (closeBtn) closeBtn.focus();
    loadAnnouncementsModalList();
}

function closeAnnouncementsModal() {
    if (!announcementsModalOpen) return;
    announcementsModalOpen = false;
    document.getElementById("announcements-modal").style.display = "none";
    document.body.classList.remove("modal-open");
    if (announcementsLastFocus && typeof announcementsLastFocus.focus === "function") {
        announcementsLastFocus.focus();
    }
    announcementsLastFocus = null;
}

// 点在弹窗外面的遮罩上才关闭（点弹窗里面的内容时事件也会冒泡到遮罩）
function onAnnouncementsOverlayClick(event) {
    if (event && event.target && event.target.id === "announcements-modal") {
        closeAnnouncementsModal();
    }
}

document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && announcementsModalOpen) {
        e.preventDefault();
        closeAnnouncementsModal();
        return;
    }
    // 公告卡片是 role="button"：回车、空格也能打开
    if ((e.key === "Enter" || e.key === " ") && e.target && e.target.id === "announcement-overview-card") {
        e.preventDefault();
        openAnnouncementsModal();
    }
});

window.addEventListener("pageshow", function (e) {
    if (e.persisted) {
        window.location.reload();
        return;
    }
    closeJoinGroupModal();
    closeAnnouncementsModal();
    applyLanguage();
    loadCurrentUser();
    loadAnnouncementPreview();
});

// 语言切换后重新渲染公告
const _origApplyLanguage = window.applyLanguage;
window.applyLanguage = function(lang) {
    _origApplyLanguage(lang);
    loadAnnouncementPreview();
    if (announcementsModalOpen) loadAnnouncementsModalList();
};

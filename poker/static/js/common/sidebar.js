// ── 汉堡按钮拖拽 ──────────────────────────────────────────
(function makeDraggable() {
    var STORAGE_KEY = 'hamburger_pos';

    function clamp(val, min, max) { return Math.max(min, Math.min(max, val)); }

    function applyPos(btn, x, y) {
        btn.style.left = x + 'px';
        btn.style.top  = y + 'px';
    }

    function savePos(x, y) {
        try { localStorage.setItem(STORAGE_KEY, JSON.stringify({x: x, y: y})); } catch(e) {}
    }

    function loadPos() {
        try { return JSON.parse(localStorage.getItem(STORAGE_KEY)); } catch(e) { return null; }
    }

    document.addEventListener('DOMContentLoaded', function () {
        var btn = document.querySelector('.hamburger-btn');
        if (!btn) return;

        // 恢复上次位置
        var saved = loadPos();
        if (saved) {
            var maxX = window.innerWidth  - btn.offsetWidth;
            var maxY = window.innerHeight - btn.offsetHeight;
            applyPos(btn, clamp(saved.x, 0, maxX), clamp(saved.y, 0, maxY));
        }

        var dragging = false;
        var startX, startY, origX, origY;

        btn.addEventListener('mousedown', function (e) {
            dragging = false;
            startX = e.clientX;
            startY = e.clientY;
            origX  = btn.getBoundingClientRect().left;
            origY  = btn.getBoundingClientRect().top;

            function onMove(e) {
                var dx = e.clientX - startX;
                var dy = e.clientY - startY;
                if (!dragging && Math.abs(dx) < 4 && Math.abs(dy) < 4) return;
                dragging = true;
                var maxX = window.innerWidth  - btn.offsetWidth;
                var maxY = window.innerHeight - btn.offsetHeight;
                applyPos(btn, clamp(origX + dx, 0, maxX), clamp(origY + dy, 0, maxY));
            }

            function onUp(e) {
                document.removeEventListener('mousemove', onMove);
                document.removeEventListener('mouseup',   onUp);
                if (dragging) {
                    savePos(btn.getBoundingClientRect().left, btn.getBoundingClientRect().top);
                    e.stopPropagation();
                }
            }

            document.addEventListener('mousemove', onMove);
            document.addEventListener('mouseup',   onUp);
        });

        // 触摸拖拽
        btn.addEventListener('touchstart', function (e) {
            dragging = false;
            var t0 = e.touches[0];
            startX = t0.clientX;
            startY = t0.clientY;
            origX  = btn.getBoundingClientRect().left;
            origY  = btn.getBoundingClientRect().top;

            function onMove(e) {
                var t = e.touches[0];
                var dx = t.clientX - startX;
                var dy = t.clientY - startY;
                if (!dragging && Math.abs(dx) < 4 && Math.abs(dy) < 4) return;
                dragging = true;
                e.preventDefault();
                var maxX = window.innerWidth  - btn.offsetWidth;
                var maxY = window.innerHeight - btn.offsetHeight;
                applyPos(btn, clamp(origX + dx, 0, maxX), clamp(origY + dy, 0, maxY));
            }

            function onEnd() {
                btn.removeEventListener('touchmove', onMove);
                btn.removeEventListener('touchend',  onEnd);
                if (dragging) {
                    savePos(btn.getBoundingClientRect().left, btn.getBoundingClientRect().top);
                }
            }

            btn.addEventListener('touchmove', onMove, { passive: false });
            btn.addEventListener('touchend',  onEnd);
        }, { passive: true });

        // 拖拽时不触发 toggleSidebar
        btn.addEventListener('click', function (e) {
            if (dragging) { e.stopImmediatePropagation(); dragging = false; }
        }, true);
    });
})();

// ─────────────────────────────────────────────────────────────

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

// Close sidebar on navigation (menu item click)；切换语言时不收起，方便看到切换结果
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".menu-item:not(.sidebar-language-toggle)").forEach(function (item) {
        item.addEventListener("click", function () {
            closeSidebar();
        });
    });
});

// 侧边栏语言切换按钮的文字：显示“要切换到的语言”（和登录页、控制台的按钮一致）
function updateSidebarLanguageLabel() {
    var lang = typeof getCurrentLanguage === "function" ? getCurrentLanguage() : "zh";
    document.querySelectorAll(".sidebar-language-label").forEach(function (label) {
        label.innerText = lang === "zh" ? "English" : "中文";
        label.setAttribute("lang", lang === "zh" ? "en" : "zh");
    });
}

document.addEventListener("languageChanged", updateSidebarLanguageLabel);
document.addEventListener("DOMContentLoaded", updateSidebarLanguageLabel);

// Mobile topbar: inject row-break div between upload-button and avatar
// so first row = language + upload-avatar, second row = avatar + role-tag
(function injectTopbarBreak() {
    function doInject() {
        if (window.innerWidth > 768) return;
        const actions = document.querySelector('.topbar-actions');
        if (!actions || actions.querySelector('.topbar-row-break')) return;
        // 只有同时存在语言切换和更换头像按钮时才需要换行（dashboard页面）
        const hasLangToggle = actions.querySelector('.dashboard-language-toggle');
        const hasUploadBtn = actions.querySelector('.upload-avatar-button');
        if (!hasLangToggle || !hasUploadBtn) return;
        const avatar = actions.querySelector('.avatar');
        if (!avatar) return;
        const br = document.createElement('div');
        br.className = 'topbar-row-break';
        actions.insertBefore(br, avatar);
    }
    document.addEventListener('DOMContentLoaded', doInject);
    window.addEventListener('resize', doInject);
})();


// 无障碍：侧边栏菜单项是带 data-href / data-on-click 的 div，补上键盘可达（Tab 聚焦、Enter / 空格触发）
// 和读屏语义；弹窗标记为 dialog；没有 alt 的图片补空 alt。
(function enhanceAccessibility() {
    function run() {
        document.querySelectorAll("div.menu-item[data-href], div.menu-item[data-on-click]").forEach(item => {
            if (item.dataset.a11yReady) {
                return;
            }

            item.dataset.a11yReady = "1";

            if (!item.hasAttribute("tabindex")) {
                item.setAttribute("tabindex", "0");
            }

            if (!item.hasAttribute("role")) {
                item.setAttribute("role", "link");
            }

            if (item.classList.contains("active")) {
                item.setAttribute("aria-current", "page");
            }

            item.addEventListener("keydown", event => {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    item.click();
                }
            });
        });

        document
            .querySelectorAll(".custom-modal-content, .logs-modal-content")
            .forEach(dialog => {
                dialog.setAttribute("role", "dialog");
                dialog.setAttribute("aria-modal", "true");
            });

        document.querySelectorAll("img:not([alt])").forEach(img => {
            img.setAttribute("alt", "");
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", run);
    } else {
        run();
    }
})();

/**
 * onboarding.js — 各角色首页的“快速上手”卡片。
 * 用法：页面上放一个 <div id="onboarding-slot" data-role="admin|organizer|user"></div>。
 * 关闭后记在本浏览器里（localStorage），不再显示；读写失败时照常显示，不影响页面。
 */
(function () {
    const STEPS = {
        admin: [
            { key: "onboardingAdmin1", href: "/invite-management" },
            { key: "onboardingAdmin2", href: "/invite-management" },
            { key: "onboardingAdmin3", href: "/user-management" },
            { key: "onboardingAdmin4", href: "/admin-game-logs" },
        ],
        organizer: [
            { key: "onboardingOrganizer1", href: "/organizer-invite-management" },
            { key: "onboardingOrganizer2", href: "/organizer-members" },
            { key: "onboardingOrganizer3", href: "/organizer-games" },
            { key: "onboardingOrganizerLeaveRule", href: "/organizer-games" },
            { key: "onboardingOrganizer4", href: "/organizer-game-logs" },
        ],
        user: [
            { key: "onboardingUser1", href: "/user-game" },
            { key: "onboardingUser2", href: "/user-game" },
            { key: "onboardingUser3", href: "/user-game-logs" },
        ],
    };

    function storageKey(role) {
        return `onboarding-dismissed-${role}`;
    }

    function isDismissed(role) {
        try {
            return localStorage.getItem(storageKey(role)) === "1";
        } catch (error) {
            return false;
        }
    }

    function dismiss(role) {
        try {
            localStorage.setItem(storageKey(role), "1");
        } catch (error) {
            // 存不了也没关系，本次关闭仍然生效
        }
    }

    // 设置 data-i18n，切换语言时由 language.js 的 applyLanguage() 自动更新
    function setText(element, key) {
        element.setAttribute("data-i18n", key);
        element.textContent = typeof t === "function" ? t(key) : key;
    }

    function render(slot) {
        const role = slot.dataset.role;
        const steps = STEPS[role];

        slot.textContent = "";

        if (!steps || isDismissed(role)) {
            slot.hidden = true;
            return;
        }

        slot.hidden = false;

        const card = document.createElement("section");
        card.className = "onboarding-card";
        card.setAttribute("aria-labelledby", "onboarding-title");

        const header = document.createElement("div");
        header.className = "onboarding-header";

        const title = document.createElement("h2");
        title.id = "onboarding-title";
        title.className = "onboarding-title";
        setText(title, "onboardingTitle");

        const close = document.createElement("button");
        close.type = "button";
        close.className = "onboarding-dismiss";
        setText(close, "onboardingDismiss");
        close.addEventListener("click", () => {
            dismiss(role);
            slot.hidden = true;
        });

        header.append(title, close);

        const list = document.createElement("ol");
        list.className = "onboarding-steps";

        steps.forEach(step => {
            const item = document.createElement("li");
            const link = document.createElement("a");
            link.href = step.href;
            setText(link, step.key);
            item.append(link);
            list.append(item);
        });

        card.append(header, list);
        slot.append(card);
    }

    function renderAll() {
        document.querySelectorAll("#onboarding-slot[data-role]").forEach(render);
    }

    window.renderOnboarding = renderAll;

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", renderAll);
    } else {
        renderAll();
    }
})();

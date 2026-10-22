window.adminGameLogState = { groupId: null };

async function onGroupChange() {
    const select = document.getElementById("admin-group-select");
    const groupId = select.value;
    window.adminGameLogState.groupId = groupId || null;

    const content = document.getElementById("admin-log-content");
    if (!groupId) {
        content.style.display = "none";
        return;
    }

    // 更新顶部组名
    const text = select.options[select.selectedIndex].textContent;
    document.getElementById("current-group-text").innerText = text;

    content.style.display = "block";
    currentPage = 1;
    currentSearch = "";
    currentView = "logs";
    if (document.getElementById("log-search-input")) {
        document.getElementById("log-search-input").value = "";
    }

    // 重置 tab 状态
    document.getElementById("view-logs").style.display = "block";
    document.getElementById("view-stats").style.display = "none";
    document.getElementById("view-member-stats").style.display = "none";
    document.getElementById("btn-logs").classList.add("active");
    document.getElementById("btn-stats").classList.remove("active");
    document.getElementById("btn-member-stats").classList.remove("active");

    loadGameLogs(1);
}

async function loadGroupSelect() {
    const select = document.getElementById("admin-group-select");
    const data = await fetchAdminGroupOptions();
    if (!data.success) return;
    data.groups.forEach(g => {
        const opt = document.createElement("option");
        opt.value = g.id;
        opt.textContent = `${g.group_name} (${g.group_code})`;
        select.appendChild(opt);
    });
}

window.addEventListener("pageshow", function () {
    applyLanguage();
    loadCurrentUser();
    loadGroupSelect();
});

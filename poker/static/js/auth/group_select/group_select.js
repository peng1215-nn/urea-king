window.addEventListener("pageshow", function () {
    renderGroups();
});


function renderGroups() {
    const groupList =
        document.getElementById("group-list");

    // 优先使用服务器端注入的最新数据（避免 CSP，用 data 属性传递）
    // 降级到 sessionStorage（登录时缓存）
    let groups;
    try {
        const raw = groupList.dataset.serverGroups;
        groups = raw ? JSON.parse(raw) : null;
    } catch (e) {
        groups = null;
    }
    if (!groups) {
        groups = JSON.parse(sessionStorage.getItem("available_groups") || "[]");
    }

    if (groups.length === 0) {
        // 未加入任何组，引导用户创建或加入
        groupList.innerHTML = `
            <div class="group-card" style="text-align:center;color:#aaa;font-size:14px;margin-bottom:12px;">
                ${t("noAvailableGroup")}
            </div>
            <div style="display:flex;flex-direction:column;gap:12px;margin-top:8px;">
                <button class="group-action-btn" id="btn-create-group">
                    🎯 ${t("createGroupBtn") || "创建自己的组（局头）"}
                </button>
                <button class="group-action-btn secondary" id="btn-join-group">
                    🤝 ${t("joinGroupBtn") || "使用邀请码加入组"}
                </button>
            </div>
        `;

        document.getElementById("btn-create-group").addEventListener("click", function () {
            window.location.href = "/create-group";
        });
        document.getElementById("btn-join-group").addEventListener("click", function () {
            window.location.href = "/group-join";
        });

        sessionStorage.removeItem("login_no_group");
        return;
    }

    sessionStorage.removeItem("login_no_group");
    groupList.innerHTML = "";

    groups.forEach(group => {
        const card =
            document.createElement("div");

        card.className = "group-card";

        card.onclick = function () {
            selectGroup(group.group_id);
        };

        card.innerHTML = `
            <div class="group-name">
                ${escapeHtml(group.group_code)} - ${escapeHtml(group.group_name || "")}
            </div>

            <div class="group-role">${t("role")}：${escapeHtml(group.role)}
            </div>
        `;

        groupList.appendChild(card);
    });
}


async function selectGroup(groupId) {
    const formData =
        new FormData();

    formData.append(
        "group_id",
        groupId
    );

    try {
        const response = await fetch(
            "/select-group",
            {
                method: "POST",
                body: formData,
            }
        );

        const data =
            await response.json();

        if (!data.success) {
            showMessage(
                t(
                    data.error_code ||
                    "groupSelectFailed"
                )
            );

            return;
        }

        if (data.redirect_url) {
            window.location.replace(
                data.redirect_url
            );

            return;
        }

        window.location.replace("/login");

    } catch (error) {
        console.error(error);

        showMessage(
            t("groupSelectFailed")
        );
    }
}


function showMessage(message) {
    document.getElementById("message-box").innerText =
        message;
}

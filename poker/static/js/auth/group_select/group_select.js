window.addEventListener("pageshow", function () {
    groupSelecting = false;
    renderGroups();
});


// 切换语言时重新渲染（身份等文字由脚本生成）
document.addEventListener("languageChanged", function () {
    if (!groupSelecting) {
        renderGroups();
    }
});


let groupSelecting = false;

const ROLE_LABEL_KEYS = {
    admin: "roleAdmin",
    organizer: "roleOrganizer",
    user: "roleUser",
};


function roleLabel(role) {
    const key = ROLE_LABEL_KEYS[role];
    return key ? t(key) : (role || "");
}


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
        // 用 <button>：键盘可以 Tab 选中、回车 / 空格进入
        const card =
            document.createElement("button");

        card.type = "button";
        card.className = "group-card";

        card.addEventListener("click", function () {
            selectGroup(group.group_id, card);
        });

        card.innerHTML = `
            <div class="group-name">
                ${escapeHtml(group.group_code)} - ${escapeHtml(group.group_name || "")}
            </div>

            <div class="group-role">${escapeHtml(t("role"))}：${escapeHtml(roleLabel(group.role))}
            </div>
        `;

        groupList.appendChild(card);
    });

    // 有组的用户也可以加入其他组或创建新组
    const extraBtns = document.createElement("div");
    extraBtns.style.cssText = "display:flex;flex-direction:column;gap:12px;margin-top:16px;";
    extraBtns.innerHTML = `
        <button class="group-action-btn secondary" id="btn-join-group">
            🤝 ${t("joinGroupBtn") || "使用邀请码加入组"}
        </button>
        <button class="group-action-btn secondary" id="btn-create-group">
            🎯 ${t("createGroupBtn") || "创建自己的组（局头）"}
        </button>
    `;
    groupList.appendChild(extraBtns);

    document.getElementById("btn-join-group").addEventListener("click", function () {
        window.location.href = "/group-join";
    });
    document.getElementById("btn-create-group").addEventListener("click", function () {
        window.location.href = "/create-group";
    });
}


function setGroupSelecting(card, busy) {
    groupSelecting = busy;

    document
        .querySelectorAll("#group-list button")
        .forEach(button => {
            button.disabled = busy;
        });

    if (!card) {
        return;
    }

    card.classList.toggle("is-loading", busy);
    card.setAttribute("aria-busy", busy ? "true" : "false");

    const roleLine = card.querySelector(".group-role");
    if (roleLine && busy) {
        roleLine.textContent = t("groupSelecting");
    }
}


async function selectGroup(groupId, card) {
    if (groupSelecting) {
        return;
    }

    setGroupSelecting(card, true);

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
            if (authIsSessionExpired(data)) {
                authRedirectExpired();
                return;
            }

            renderGroups();
            groupSelecting = false;

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

        renderGroups();
        groupSelecting = false;

        showMessage(
            t("groupSelectFailed")
        );
    }
}


function showMessage(message) {
    document.getElementById("message-box").innerText =
        message;
}

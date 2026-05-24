window.addEventListener("pageshow", function () {
    renderGroups();
});


function renderGroups() {
    const groupList =
        document.getElementById("group-list");

    const groups = JSON.parse(
        sessionStorage.getItem("available_groups") || "[]"
    );

    if (groups.length === 0) {
        groupList.innerHTML =
            `<div class="group-card">没有可进入的组别。</div>`;

        return;
    }

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
                ${group.group_code} - ${group.group_name || ""}
            </div>

            <div class="group-role">
                身份：${group.role}
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
        const response = await fetch("/select-group", {
            method: "POST",
            body: formData,
        });

        const data =
            await response.json();

        if (!data.success) {
            showMessage(
                data.error_code || "组别选择失败。"
            );

            return;
        }

        redirectByRole(
            data.role
        );

    } catch (error) {
        console.error(error);

        showMessage(
            "组别选择失败。"
        );
    }
}


function redirectByRole(role) {
    if (role === "admin") {
        window.location.replace("/admin-dashboard");
        return;
    }

    if (role === "organizer") {
        window.location.replace("/admin-dashboard");
        return;
    }

    window.location.replace("/login");
}


function showMessage(message) {
    document.getElementById("message-box").innerText =
        message;
}
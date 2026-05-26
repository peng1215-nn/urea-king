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
            `<div class="group-card">${t("noAvailableGroup")}</div>`;

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

            <div class="group-role">${t("role")}：${group.role}
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
async function loadAuditLogs() {
    const messageBox =
        document.getElementById("logs-message");

    messageBox.innerText = "";

    try {
        const data =
            await fetchAuditLogs();

        if (!data.success) {
            messageBox.style.color =
                "#ff8a8a";

            messageBox.innerText =
                t(data.message || "operationFailed");

            return;
        }

        window.systemLogsState.logs =
            data.logs;

        // 翻页/筛选后重新选择，避免误删不可见的记录
        window.systemLogsState.selectedIds.clear();

        window.systemLogsState.page =
            data.pagination.page;

        window.systemLogsState.pageSize =
            data.pagination.page_size;

        window.systemLogsState.total =
            data.pagination.total;

        window.systemLogsState.totalPages =
            data.pagination.total_pages;

        renderLogs(data.logs);

        updateSelectionUI();

        renderPagination();

        renderLogsMessage();

    } catch (error) {
        console.error(error);

        messageBox.style.color =
            "#ff8a8a";

        messageBox.innerText =
            t("operationFailed");
    }
}


function renderLogsMessage() {
    const messageBox =
        document.getElementById("logs-message");

    const username =
        document.getElementById("log-username-filter").value.trim();

    const action =
        document.getElementById("log-action-filter").value;

    const total =
        window.systemLogsState.total;

    if (username || action) {
        if (total > 0) {
            messageBox.style.color =
                "#5CFFB2";
        } else {
            messageBox.style.color =
                "#ff8a8a";
        }

        messageBox.innerText =
            `${t("searchResultPrefix")} ${total} ${t("logSearchResultSuffix")}`;
    } else {
        messageBox.style.color =
            "#9aa4b2";

        messageBox.innerText =
            `${t("totalLogsPrefix")} ${total} ${t("totalLogsSuffix")}`;
    }
}


function searchLogs() {
    window.systemLogsState.page = 1;

    loadAuditLogs();
}


function clearLogFilters() {
    const actionSelect =
        document.getElementById("log-action-filter");

    const usernameInput =
        document.getElementById("log-username-filter");

    const pageSizeSelect =
        document.getElementById("log-page-size");

    actionSelect.selectedIndex = 0;
    actionSelect.value = "";

    usernameInput.value = "";

    pageSizeSelect.value = "5";

    window.systemLogsState.page = 1;
    window.systemLogsState.pageSize = 5;

    loadAuditLogs();
}


function goToPreviousPage() {
    if (window.systemLogsState.page <= 1) {
        return;
    }

    window.systemLogsState.page -= 1;

    loadAuditLogs();
}


function goToNextPage() {
    if (
        window.systemLogsState.page >=
        window.systemLogsState.totalPages
    ) {
        return;
    }

    window.systemLogsState.page += 1;

    loadAuditLogs();
}


function updateSelectionUI() {
    const selected =
        window.systemLogsState.selectedIds;

    const logs =
        window.systemLogsState.logs || [];

    const button =
        document.getElementById("bulk-delete-button");

    const counter =
        document.getElementById("selected-count");

    const selectAll =
        document.getElementById("select-all-logs");

    button.disabled = selected.size === 0;

    counter.innerText =
        selected.size > 0 ? `(${selected.size})` : "";

    selectAll.checked =
        logs.length > 0 && logs.every(log => selected.has(log.id));

    selectAll.indeterminate =
        selected.size > 0 && !selectAll.checked;
}


function toggleLogSelection(id, checked) {
    if (checked) {
        window.systemLogsState.selectedIds.add(id);
    } else {
        window.systemLogsState.selectedIds.delete(id);
    }

    updateSelectionUI();
}


function toggleSelectAll(checked) {
    (window.systemLogsState.logs || []).forEach(log => {
        if (checked) {
            window.systemLogsState.selectedIds.add(log.id);
        } else {
            window.systemLogsState.selectedIds.delete(log.id);
        }
    });

    document.querySelectorAll(".log-checkbox").forEach(box => {
        box.checked = checked;
    });

    updateSelectionUI();
}


function exportLogs() {
    const params =
        new URLSearchParams();

    params.append(
        "action",
        document.getElementById("log-action-filter").value
    );

    params.append(
        "username",
        document.getElementById("log-username-filter").value.trim()
    );

    const link =
        document.createElement("a");

    link.href =
        `/admin/audit-logs/export?${params.toString()}`;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}


function openBulkDeleteModal() {
    const count =
        window.systemLogsState.selectedIds.size;

    if (count === 0) {
        return;
    }

    document.getElementById("bulk-delete-count").innerText = count;
    document.getElementById("bulk-delete-modal").hidden = false;
}


function closeBulkDeleteModal() {
    document.getElementById("bulk-delete-modal").hidden = true;
}


async function confirmBulkDelete() {
    const messageBox =
        document.getElementById("logs-message");

    const confirmButton =
        document.getElementById("bulk-delete-confirm");

    const ids =
        Array.from(window.systemLogsState.selectedIds);

    confirmButton.disabled = true;

    try {
        const data =
            await deleteAuditLogs(ids);

        closeBulkDeleteModal();

        if (!data.success) {
            messageBox.style.color = "#ff8a8a";
            messageBox.innerText = t(data.message || "operationFailed");
            return;
        }

        // 当前页被删空时回到上一页
        const remaining =
            window.systemLogsState.logs.length - data.deleted;

        if (remaining <= 0 && window.systemLogsState.page > 1) {
            window.systemLogsState.page -= 1;
        }

        await loadAuditLogs();

        messageBox.style.color = "#5CFFB2";
        messageBox.innerText =
            `${t("bulkDeleteDonePrefix")} ${data.deleted} ${t("bulkDeleteDoneSuffix")}`;

    } catch (error) {
        console.error(error);
        closeBulkDeleteModal();
        messageBox.style.color = "#ff8a8a";
        messageBox.innerText = t("operationFailed");
    } finally {
        confirmButton.disabled = false;
    }
}

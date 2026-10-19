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

        window.systemLogsState.page =
            data.pagination.page;

        window.systemLogsState.pageSize =
            data.pagination.page_size;

        window.systemLogsState.total =
            data.pagination.total;

        window.systemLogsState.totalPages =
            data.pagination.total_pages;

        renderLogs(data.logs);

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
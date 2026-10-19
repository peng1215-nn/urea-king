function getLogActionText(action) {
    return t(action || "unknown");
}


function getSafeValue(value) {
    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "--";
    }

    return value;
}


function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function renderLogs(logs) {
    const tableBody =
        document.getElementById("logs-table-body");

    tableBody.innerHTML = "";

    if (!logs || logs.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="9" class="empty-row">
                    ${t("noLogsFound")}
                </td>
            </tr>
        `;

        return;
    }

    logs.forEach(log => {
        const row =
            document.createElement("tr");

        row.innerHTML = `
            <td title="${escapeHtml(getSafeValue(log.operator_username))}">
                ${escapeHtml(getSafeValue(log.operator_username))}
            </td>

            <td title="${escapeHtml(getSafeValue(log.operator_nickname))}">
                ${escapeHtml(getSafeValue(log.operator_nickname))}
            </td>

            <td title="${escapeHtml(getLogActionText(log.action))}">
                <span class="log-action-badge">
                    ${getLogActionText(log.action)}
                </span>
            </td>

            <td title="${escapeHtml(getSafeValue(log.target_type))}">
                ${escapeHtml(getSafeValue(log.target_type))}
            </td>

            <td title="${escapeHtml(getSafeValue(log.target_id))}">
                ${escapeHtml(getSafeValue(log.target_id))}
            </td>

            <td
                class="log-value-cell"
                title="${escapeHtml(getSafeValue(log.old_value))}"
            >
                ${escapeHtml(getSafeValue(log.old_value))}
            </td>

            <td
                class="log-value-cell"
                title="${escapeHtml(getSafeValue(log.new_value))}"
            >
                ${escapeHtml(getSafeValue(log.new_value))}
            </td>

            <td title="${escapeHtml(getSafeValue(log.created_at))}">
                ${escapeHtml(getSafeValue(log.created_at))}
            </td>

            <td title="${escapeHtml(getSafeValue(log.ip_address))}">
                ${escapeHtml(getSafeValue(log.ip_address))}
            </td>
        `;

        tableBody.appendChild(row);
    });
}


function renderPagination() {
    const page =
        window.systemLogsState.page;

    const totalPages =
        window.systemLogsState.totalPages;

    document.getElementById("pagination-info").innerText =
        `${page} / ${totalPages}`;

    document.getElementById("previous-page-button").disabled =
        page <= 1;

    document.getElementById("next-page-button").disabled =
        page >= totalPages;
}
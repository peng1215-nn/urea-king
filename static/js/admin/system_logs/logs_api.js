async function fetchAuditLogs() {
    const action =
        document.getElementById("log-action-filter").value;

    const username =
        document.getElementById("log-username-filter").value.trim();

    const pageSize =
        document.getElementById("log-page-size").value || "5";

    const params =
        new URLSearchParams();

    params.append("action", action);
    params.append("username", username);
    params.append("page", window.systemLogsState.page || 1);
    params.append("page_size", pageSize);

    const response =
        await fetch(`/admin/audit-logs?${params.toString()}`);

    return await response.json();
}
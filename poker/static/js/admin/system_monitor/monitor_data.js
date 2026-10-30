async function loadSystemMonitor() {
    try {
        const response = await fetch("/admin/system-monitor");
        const data = await response.json();

        if (!data.success) {
            return;
        }

        document.getElementById("service-uptime").innerText =
            formatRuntime(data.total_runtime_seconds);

        document.getElementById("database-status").innerText =
            t(data.database_status || "unknown");

        document.getElementById("deploy-environment").innerText =
            data.deploy_environment || t("unknown");

        document.getElementById("system-version").innerText =
            data.system_version || t("unknown");

        document.getElementById("page-view-today").innerText =
            data.page_view_today ?? "--";

        document.getElementById("page-view-total").innerText =
            data.page_view_total ?? "--";

        document.getElementById("login-success-today").innerText =
            data.login_success_today ?? "--";

        document.getElementById("login-success-total").innerText =
            data.login_success_total ?? "--";

    } catch (error) {
        console.error(t("systemMonitorLoadFailed"), error);
    }
}
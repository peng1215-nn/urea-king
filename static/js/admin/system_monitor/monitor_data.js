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
            data.database_status;

        document.getElementById("deploy-environment").innerText =
            data.deploy_environment;

        document.getElementById("system-version").innerText =
            data.system_version;

    } catch (error) {
        console.error("加载系统监控数据失败：", error);
    }
}
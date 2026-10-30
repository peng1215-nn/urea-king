/**
 * 牌局日志里的"审计报告"按钮：在新标签页打开这一局的审计报告（独立页面）。
 * 管理员页面可以切换组，所以要带上当前选中的组。
 */
function openGameReport(gameId) {
    const query = new URLSearchParams({ game_id: String(gameId) });
    const adminState = window.adminGameLogState;
    if (adminState && adminState.groupId) {
        query.set("group_id", String(adminState.groupId));
    }
    window.open(`/game-report?${query.toString()}`, "_blank", "noopener");
}

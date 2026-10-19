function openGameSettings() {
    document.getElementById('game-settings-modal').style.display = 'flex';
    loadChipAuthSettings();
}

function closeGameSettings() {
    document.getElementById('game-settings-modal').style.display = 'none';
}

// 点击遮罩关闭
document.addEventListener('click', function(e) {
    const modal = document.getElementById('game-settings-modal');
    if (e.target === modal) closeGameSettings();
});

function loadChipAuthSettings() {
    const list = document.getElementById('chip-auth-list');
    list.innerHTML = '<div class="settings-loading">加载中...</div>';

    fetch('/user/game/chip-auth-settings')
        .then(r => r.json())
        .then(data => {
            if (!data.success) {
                list.innerHTML = '<div class="settings-loading">加载失败</div>';
                return;
            }
            if (data.settings.length === 0) {
                list.innerHTML = '<div class="settings-loading">暂无所属组</div>';
                return;
            }
            list.innerHTML = data.settings.map(s => `
                <div class="chip-auth-row">
                    <div class="chip-auth-group-name">${s.group_name}</div>
                    <label class="toggle-switch">
                        <input
                            type="checkbox"
                            ${s.allow_organizer_chip_op ? 'checked' : ''}
                            onchange="updateChipAuth(${s.group_id}, this.checked)"
                        >
                        <span class="toggle-slider"></span>
                    </label>
                </div>
            `).join('');
        })
        .catch(() => {
            list.innerHTML = '<div class="settings-loading">加载失败</div>';
        });
}

function updateChipAuth(groupId, allow) {
    const body = new URLSearchParams();
    body.append('group_id', groupId);
    body.append('allow', allow ? 1 : 0);

    fetch('/user/game/chip-auth-update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString(),
    })
        .then(r => r.json())
        .then(data => {
            if (!data.success) {
                // 回滚UI
                loadChipAuthSettings();
            }
        })
        .catch(() => loadChipAuthSettings());
}

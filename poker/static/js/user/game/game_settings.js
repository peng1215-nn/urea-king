// 本地暂存开关状态，点应用后才提交
let pendingChipAuth = {};

function openGameSettings() {
    document.getElementById('game-settings-modal').style.display = 'flex';
    pendingChipAuth = {};
    loadChipAuthSettings();
}

function closeGameSettings() {
    document.getElementById('game-settings-modal').style.display = 'none';
    pendingChipAuth = {};
}

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
                            data-group-id="${s.group_id}"
                            ${s.allow_organizer_chip_op ? 'checked' : ''}
                            onchange="onToggleChange(${s.group_id}, this.checked)"
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

function onToggleChange(groupId, checked) {
    pendingChipAuth[groupId] = checked ? 1 : 0;
}

function applyGameSettings() {
    const btn = document.querySelector('.settings-apply-btn');
    const keys = Object.keys(pendingChipAuth);

    if (keys.length === 0) {
        closeGameSettings();
        return;
    }

    btn.disabled = true;
    btn.textContent = '保存中...';

    const requests = keys.map(groupId =>
        fetch('/user/game/chip-auth-update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `group_id=${groupId}&allow=${pendingChipAuth[groupId]}`,
        }).then(r => r.json())
    );

    Promise.all(requests)
        .then(results => {
            const allOk = results.every(r => r.success);
            if (allOk) {
                closeGameSettings();
            } else {
                btn.textContent = '应用';
                btn.disabled = false;
                loadChipAuthSettings();
            }
        })
        .catch(() => {
            btn.textContent = '应用';
            btn.disabled = false;
        });
}

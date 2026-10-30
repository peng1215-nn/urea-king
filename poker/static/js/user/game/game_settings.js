// 本地暂存开关状态，点应用后才提交
let pendingChipAuth = {};

function setSettingsMessage(text) {
    const box = document.getElementById('settings-message');
    if (box) box.innerText = text || '';
}

function openGameSettings() {
    document.getElementById('game-settings-modal').style.display = 'flex';
    pendingChipAuth = {};
    setSettingsMessage('');
    loadChipAuthSettings();
}

function closeGameSettings() {
    document.getElementById('game-settings-modal').style.display = 'none';
    pendingChipAuth = {};
    setSettingsMessage('');
    const btn = document.querySelector('.settings-apply-btn');
    if (btn) {
        btn.disabled = false;
        btn.textContent = t('apply');
    }
}

document.addEventListener('click', function(e) {
    const modal = document.getElementById('game-settings-modal');
    if (e.target === modal) closeGameSettings();
});

function loadChipAuthSettings() {
    const list = document.getElementById('chip-auth-list');
    list.innerHTML = `<div class="settings-loading">${t('settingsLoading')}</div>`;

    fetch('/user/game/chip-auth-settings')
        .then(r => r.json())
        .then(data => {
            if (!data.success) {
                list.innerHTML = `<div class="settings-loading">${t('settingsLoadError')}</div>`;
                return;
            }
            if (data.settings.length === 0) {
                list.innerHTML = `<div class="settings-loading">${t('settingsNoGroup')}</div>`;
                return;
            }
            list.innerHTML = data.settings.map(s => `
                <div class="chip-auth-row">
                    <div class="chip-auth-group-name">${escapeHtml(s.group_name)}</div>
                    <label class="toggle-switch">
                        <input
                            type="checkbox"
                            data-group-id="${s.group_id}"
                            ${s.allow_organizer_chip_op ? 'checked' : ''}
                            data-on-change="onToggleChange" data-args="[${s.group_id},&quot;$checked&quot;]"
                        >
                        <span class="toggle-slider"></span>
                    </label>
                </div>
            `).join('');
        })
        .catch(() => {
            list.innerHTML = `<div class="settings-loading">${t('settingsLoadError')}</div>`;
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
    btn.textContent = t('settingsSaving');
    setSettingsMessage('');

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
                // 有的组没保存成功：重新加载开关（显示服务器上真实的状态），并告诉用户
                const failed = results.find(r => !r.success);
                btn.textContent = t('apply');
                btn.disabled = false;
                pendingChipAuth = {};
                loadChipAuthSettings();
                setSettingsMessage(t('settingsSaveError') + (failed && failed.message && failed.message !== 'operationFailed' ? ' ' + t(failed.message) : ''));
            }
        })
        .catch(() => {
            btn.textContent = t('apply');
            btn.disabled = false;
            pendingChipAuth = {};
            loadChipAuthSettings();
            setSettingsMessage(t('settingsSaveError'));
        });
}

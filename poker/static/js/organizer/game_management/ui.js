/*
 * 牌局管理页的通用小工具：
 * - showGameMessage：页面顶层的提示条（toast），约 3 秒后自动消失，所有操作共用；
 * - runBusy：请求进行中锁住按钮并显示“处理中…”，防止连点重复记账；
 * - displayPlayerName：和牌局日志一致的“昵称（备注）”；
 * - formatGameError：把后端返回的提示码转成文字（带人名的提示会把人名填进去）。
 */

let _gameToastTimer = null;

function showGameMessage(text, type) {
    const box = document.getElementById("game-message");
    if (!box || !text) return;

    box.innerText = text;
    box.classList.remove("success", "error");
    box.classList.add(type === "success" ? "success" : "error", "show");

    if (_gameToastTimer) clearTimeout(_gameToastTimer);
    _gameToastTimer = setTimeout(() => {
        box.classList.remove("show");
    }, type === "success" ? 3000 : 4500);
}

// 正在处理中的操作（按 key 区分），同一个操作在返回前不会被再次提交
const _busyActions = new Set();

// 已经处理完的申请：服务器下次返回的列表里可能还带着它（轮询请求在审批前就发出了），
// 这里记住，不再显示、也不再提交，避免快速连点时出现“申请不存在或已处理”
const _handledRequestIds = new Set();

function markRequestHandled(requestId, button) {
    _handledRequestIds.add(requestId);
    const card = button && button.closest ? button.closest(".request-card") : null;
    if (card) card.remove();
}

function isRequestHandled(requestId) {
    return _handledRequestIds.has(requestId);
}

function isActionBusy(key) {
    return _busyActions.has(key);
}

async function runBusy(key, buttons, fn) {
    if (_busyActions.has(key)) return undefined;
    _busyActions.add(key);

    const list = (Array.isArray(buttons) ? buttons : [buttons]).filter(Boolean);
    const saved = list.map(button => ({
        button,
        text: button.innerText,
        disabled: button.disabled,
    }));
    const processing = t("processing");

    list.forEach(button => { button.disabled = true; });
    if (list[0]) list[0].innerText = processing;

    try {
        return await fn();
    } finally {
        _busyActions.delete(key);
        saved.forEach(({ button, text, disabled }) => {
            button.disabled = disabled;
            // 处理过程中按钮文字被改过（如变成“强制结束”）就保留新文字
            if (button.innerText === processing) button.innerText = text;
        });
    }
}

function displayPlayerName(person) {
    if (!person) return "";
    const name = person.nickname || person.username || "";
    return person.alias ? `${name}（${person.alias}）` : name;
}

function formatGameError(data) {
    const message = (data && data.message) || "operationFailed";
    if (message === "playerAlreadyInAnotherGame") {
        const names = data.player_names && data.player_names.length
            ? data.player_names.join(t("nameListSep"))
            : t("thisPlayer");
        return t(message).replace("{names}", names);
    }
    return t(message);
}

// 操作失败：写到弹窗里的提示框；网络异常同时弹出顶层提示（弹窗关掉也能看到）
function reportGameFailure(data, messageBox) {
    const text = formatGameError(data);
    if (messageBox) {
        messageBox.style.color = "#ff8a8a";
        messageBox.innerText = text;
    }
    if (!messageBox || (data && data.networkError)) {
        showGameMessage(text, "error");
    }
}

// 盈亏/差额的带符号写法：+20、-20、0
function formatSigned(value) {
    return value > 0 ? `+${value}` : String(value);
}

// 差额（总卖出 − 总买入）的文字说明：筹码多了 N / 筹码少了 N / 已平衡
function describeChipDiff(diff) {
    if (diff > 0) return t("chipsOver").replace("{n}", diff);
    if (diff < 0) return t("chipsUnder").replace("{n}", -diff);
    return t("balanced");
}

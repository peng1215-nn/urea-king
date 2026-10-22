/**
 * game_export.js — 三端通用：把一局牌局渲染成图片并下载（PNG）。
 * 依赖：html2canvas（CDN）、页面上的 t() 翻译函数。
 * 用法：exportGameImage(game)；game 为牌局列表接口返回的单个牌局对象。
 */
(function () {
    const FONT = "'Noto Sans SC','PingFang SC','Microsoft YaHei',-apple-system,'Segoe UI',sans-serif";

    function esc(v) {
        return String(v == null ? "" : v)
            .replace(/&/g, "&amp;").replace(/</g, "&lt;")
            .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }

    function getGroupName() {
        const sel = document.getElementById("admin-group-select");
        if (sel && sel.selectedIndex >= 0 && sel.options[sel.selectedIndex]) {
            return sel.options[sel.selectedIndex].text.trim();
        }
        const el = document.getElementById("current-group-text");
        return el ? el.innerText.trim() : "";
    }

    function netColor(n) { return n > 0 ? "#34d399" : n < 0 ? "#f87171" : "#9aa4c0"; }

    function buildCard(game) {
        const players = (game.players || []).slice().sort((a, b) => (b.net || 0) - (a.net || 0));
        const groupName = getGroupName();
        const title = game.name || (game.started_at || "").slice(0, 10) || ("#" + game.id);
        const balanced = !!game.is_balanced;
        const badgeColor = balanced ? "#34d399" : "#f87171";

        const rows = players.map((p, i) => {
            const isWinner = p.user_id === game.top_winner_id && (p.net || 0) > 0;
            const tags =
                (p.is_organizer ? `<span style="margin-left:8px;padding:2px 8px;border-radius:6px;font-size:12px;background:rgba(92,141,255,.18);color:#8fb0ff;">${esc(t("organizer"))}</span>` : "") +
                (isWinner ? `<span style="margin-left:8px;padding:2px 8px;border-radius:6px;font-size:12px;background:rgba(250,204,21,.18);color:#facc15;">★ ${esc(t("topWinner"))}</span>` : "");
            const net = p.net || 0;
            return `<div style="display:flex;align-items:center;padding:12px 16px;border-radius:12px;margin-bottom:8px;background:${isWinner ? "rgba(250,204,21,.08)" : "rgba(255,255,255,.04)"};${isWinner ? "border-left:3px solid #facc15;" : "border-left:3px solid transparent;"}">
                <div style="width:28px;color:#7d87a6;font-size:14px;">${i + 1}</div>
                <div style="flex:1;font-size:16px;font-weight:600;color:#fff;">${esc(p.nickname)}${tags}</div>
                <div style="width:110px;text-align:right;color:#c3cae0;font-size:14px;"><div style="font-size:11px;color:#7d87a6;">${esc(t("buyIn"))}</div>${esc(p.total_buy_in)}</div>
                <div style="width:110px;text-align:right;color:#c3cae0;font-size:14px;"><div style="font-size:11px;color:#7d87a6;">${esc(t("cashOut"))}</div>${esc(p.cash_out)}</div>
                <div style="width:110px;text-align:right;font-size:18px;font-weight:700;color:${netColor(net)};"><div style="font-size:11px;font-weight:400;color:#7d87a6;">${esc(t("net"))}</div>${net > 0 ? "+" : ""}${net}</div>
            </div>`;
        }).join("");

        const note = game.note
            ? `<div style="margin-top:16px;padding:12px 16px;border-radius:10px;background:rgba(255,255,255,.04);border-left:3px solid #5c8dff;color:#c3cae0;font-size:14px;line-height:1.6;">${esc(game.note)}</div>`
            : "";

        const now = new Date();
        const pad = n => String(n).padStart(2, "0");
        const stamp = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`;

        const wrap = document.createElement("div");
        wrap.style.cssText = `position:fixed;left:-10000px;top:0;width:760px;font-family:${FONT};`;
        wrap.innerHTML = `
        <div style="width:760px;box-sizing:border-box;padding:0 0 22px;background:linear-gradient(135deg,#0f0f16,#151928,#1a2033);color:#fff;">
            <div style="padding:20px 32px;background:linear-gradient(135deg,#5c8dff,#3a6be0);display:flex;justify-content:space-between;align-items:center;">
                <div style="font-size:22px;font-weight:700;letter-spacing:2px;">UREAKING POKER</div>
                ${groupName ? `<div style="font-size:14px;opacity:.85;">${esc(groupName)}</div>` : ""}
            </div>
            <div style="padding:26px 32px 0;">
                <div style="font-size:26px;font-weight:700;margin-bottom:10px;word-break:break-all;">${esc(title)}</div>
                <div style="font-size:14px;color:#9aa4c0;margin-bottom:18px;">${esc(game.started_at)} → ${esc(game.ended_at)}${game.duration ? " · " + esc(game.duration) : ""}</div>
                <div style="display:flex;align-items:center;margin-bottom:22px;">
                    <div style="padding:10px 18px;border-radius:12px;background:rgba(92,141,255,.14);margin-right:14px;">
                        <div style="font-size:12px;color:#9aa4c0;">${esc(t("totalBuyIn"))}</div>
                        <div style="font-size:24px;font-weight:700;color:#8fb0ff;">${esc(game.total_buy_in)}</div>
                    </div>
                    <div style="padding:5px 14px;border-radius:20px;border:1.5px solid ${badgeColor};color:${badgeColor};font-size:13px;font-weight:600;">${esc(balanced ? t("balanced") : t("unbalanced"))}</div>
                </div>
                ${rows}
                ${note}
                <div style="margin-top:22px;padding-top:12px;border-top:1px solid rgba(255,255,255,.08);display:flex;justify-content:space-between;font-size:12px;color:#6b7596;">
                    <span>${stamp}</span><span>UREAKING POKER</span>
                </div>
            </div>
        </div>`;
        return wrap;
    }

    window.exportGameImage = async function (game) {
        if (!game) { alert(t("operationFailed")); return; }
        if (typeof html2canvas !== "function") { alert(t("operationFailed")); return; }
        const wrap = buildCard(game);
        document.body.appendChild(wrap);
        try {
            if (document.fonts && document.fonts.ready) { await document.fonts.ready; }
            const canvas = await html2canvas(wrap.firstElementChild, {
                scale: 2,
                backgroundColor: "#151928",
                useCORS: true,
            });
            const a = document.createElement("a");
            a.href = canvas.toDataURL("image/png");
            a.download = `game_${game.id}.png`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        } catch (e) {
            console.error(e);
            alert(t("operationFailed"));
        } finally {
            document.body.removeChild(wrap);
        }
    };
})();

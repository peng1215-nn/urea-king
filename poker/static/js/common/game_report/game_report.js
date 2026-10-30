/**
 * 牌局审计报告页：读取 /game-report/data，渲染概况、按玩家汇总、操作记录，并可导出 CSV。
 * 所有固定文字来自 i18n/game_report.js，切换语言后整页重新渲染；
 * 来自数据库的内容（牌局名、昵称、备注）一律经过 escapeHtml。
 */
(function () {
    let report = null;
    let messageKey = null;

    const MONEY_EVENTS = ["buyin_requested", "buyin_approved", "organizer_buyin", "proxy_buyin"];
    const REJECT_EVENTS = ["buyin_rejected", "buyin_auto_rejected"];
    const PEOPLE_EVENTS = ["player_added", "player_rejoined", "player_removed", "player_exited"];

    function fmt(key, vars) {
        let text = t(key);
        Object.entries(vars || {}).forEach(([name, value]) => {
            text = text.split(`{${name}}`).join(String(value));
        });
        return text;
    }

    function signed(n) {
        const value = Number(n) || 0;
        return value > 0 ? `+${value}` : String(value);
    }

    function netClass(n) {
        return n > 0 ? "net-pos" : n < 0 ? "net-neg" : "net-zero";
    }

    function buyTypeLabel(type) {
        if (type === "insurance") return t("buyInInsurance");
        if (type === "anti") return t("buyInAnti");
        if (type === "normal") return t("buyInNormal");
        return "";
    }

    function eventTagClass(type) {
        if (MONEY_EVENTS.includes(type)) return "money";
        if (REJECT_EVENTS.includes(type)) return "reject";
        if (PEOPLE_EVENTS.includes(type)) return "people";
        return "milestone";
    }

    /** 一条事件的说明文字（纯文本，页面和 CSV 共用）。 */
    function eventDetail(ev) {
        const d = ev.details || {};
        switch (ev.type) {
            case "game_started":
                return fmt("detailStartPlayers", {
                    players: (d.players || []).join(getCurrentLanguage() === "zh" ? "、" : ", "),
                });
            case "player_removed":
                return t("detailAway");
            case "player_rejoined":
                if (d.after === "exit") return fmt("detailRejoinedAfterExit", { cash_out: d.cash_out ?? 0 });
                if (d.after === "away") return t("detailRejoinedAfterAway");
                return "";
            case "player_exited":
                return fmt("detailExited", { cash_out: ev.amount ?? 0, buy_in: d.buy_in ?? 0, net: signed(d.net) });
            case "buyin_auto_rejected":
                return t("detailAutoRejected");
            case "proxy_buyin":
                return t("detailProxy");
            case "game_finished": {
                const parts = [fmt("detailFinished", { buy_in: d.total_buy_in ?? 0, cash_out: d.total_cash_out ?? 0 })];
                if (d.forced) parts.push(t("detailFinishedForced"));
                (d.players || []).forEach(p => {
                    parts.push(fmt("detailFinishedPlayer", {
                        name: p.name || "", buy_in: p.buy_in ?? 0, cash_out: p.cash_out ?? 0, net: signed(p.net),
                    }));
                });
                return parts.join(getCurrentLanguage() === "zh" ? "；" : "; ");
            }
            default:
                return "";
        }
    }

    function showMessage(key) {
        messageKey = key;
        const box = document.getElementById("report-message");
        box.hidden = false;
        box.removeAttribute("data-i18n");
        box.innerText = t(key);
        document.getElementById("report-content").hidden = true;
    }

    function renderOverview(game) {
        const fields = [
            [t("gameName"), game.name || t("unnamedGame")],
            [t("gameId"), `#${game.id}`],
            [t("startedAt"), game.started_at],
            [t("endedAt"), game.ended_at],
            [t("totalBuyIn"), game.total_buy_in],
            [t("totalCashOut"), game.total_cash_out],
            [t("balanceStatus"), game.is_balanced ? t("balanced") : t("unbalanced")],
        ];
        if (game.note) fields.push([t("gameNote"), game.note]);

        document.getElementById("report-overview").innerHTML = fields.map(([label, value]) => `
            <div>
                <div class="report-field-label">${escapeHtml(label)}</div>
                <div class="report-field-value">${escapeHtml(value)}</div>
            </div>
        `).join("");
    }

    function renderCheck(data) {
        const box = document.getElementById("report-check");
        if (!data.has_events) {
            box.className = "report-check none";
            box.innerText = t("noEvents");
        } else if (data.all_match) {
            box.className = "report-check ok";
            box.innerText = t("allMatch");
        } else {
            box.className = "report-check bad";
            box.innerText = t("someMismatch");
        }
    }

    function renderSummary(data) {
        const showCheck = data.has_events;
        const head = `
            <tr>
                <th>${escapeHtml(t("player"))}</th>
                <th class="num">${escapeHtml(t("buyIn"))}</th>
                <th class="num">${escapeHtml(t("buyInNormal"))}</th>
                <th class="num">${escapeHtml(t("buyInInsurance"))}</th>
                <th class="num">${escapeHtml(t("buyInAnti"))}</th>
                <th class="num">${escapeHtml(t("cashOut"))}</th>
                <th class="num">${escapeHtml(t("net"))}</th>
                ${showCheck ? `<th class="num">${escapeHtml(t("buyInFromEvents"))}</th><th>${escapeHtml(t("checkColumn"))}</th>` : ""}
            </tr>`;
        const rows = data.summary.map(p => `
            <tr>
                <td>${escapeHtml(p.nickname)}</td>
                <td class="num">${p.total_buy_in}</td>
                <td class="num">${p.buy_in_by_type.normal}</td>
                <td class="num">${p.buy_in_by_type.insurance}</td>
                <td class="num">${p.buy_in_by_type.anti}</td>
                <td class="num">${p.cash_out}</td>
                <td class="num ${netClass(p.net)}">${escapeHtml(signed(p.net))}</td>
                ${showCheck ? `<td class="num">${p.buy_in_from_events}</td>
                <td class="${p.matches ? "check-ok" : "check-bad"}">${escapeHtml(p.matches ? t("match") : t("mismatch"))}</td>` : ""}
            </tr>`).join("");
        document.getElementById("report-summary").innerHTML = `<thead>${head}</thead><tbody>${rows}</tbody>`;
    }

    function renderTimeline(events) {
        const table = document.getElementById("report-timeline");
        if (!events.length) {
            table.innerHTML = `<tbody><tr><td>${escapeHtml(t("noEventRows"))}</td></tr></tbody>`;
            return;
        }
        const head = `
            <tr>
                <th>${escapeHtml(t("colTime"))}</th>
                <th>${escapeHtml(t("colEvent"))}</th>
                <th>${escapeHtml(t("colOperator"))}</th>
                <th>${escapeHtml(t("colPlayer"))}</th>
                <th class="num">${escapeHtml(t("colAmount"))}</th>
                <th>${escapeHtml(t("colBuyType"))}</th>
                <th>${escapeHtml(t("colDetail"))}</th>
            </tr>`;
        const rows = events.map(ev => `
            <tr>
                <td>${escapeHtml(ev.time)}</td>
                <td><span class="event-tag ${eventTagClass(ev.type)}">${escapeHtml(t("ev_" + ev.type))}</span></td>
                <td>${escapeHtml(ev.actor_name || t("system"))}</td>
                <td>${escapeHtml(ev.target_name)}</td>
                <td class="num">${ev.amount == null ? "" : ev.amount}</td>
                <td>${escapeHtml(buyTypeLabel(ev.buy_type))}</td>
                <td class="wrap">${escapeHtml(eventDetail(ev))}</td>
            </tr>`).join("");
        table.innerHTML = `<thead>${head}</thead><tbody>${rows}</tbody>`;
    }

    function render() {
        if (!report) return;
        document.getElementById("report-message").hidden = true;
        document.getElementById("report-content").hidden = false;
        renderOverview(report.game);
        renderCheck(report);
        renderSummary(report);
        renderTimeline(report.events);
        document.getElementById("report-export-csv").disabled = false;
    }

    // ───── CSV 导出 ─────

    /**
     * 时间按文本写入：写成 ="2026-10-30 04:22:57"，Excel、WPS 会原样显示，
     * 不会自动识别成日期、按默认格式丢掉秒。
     */
    function asText(value) {
        return { asText: String(value == null ? "" : value) };
    }

    function csvCell(value) {
        if (value === null || value === undefined) return "";
        if (typeof value === "object" && "asText" in value) {
            const formula = '="' + value.asText.replace(/"/g, '""') + '"';
            return '"' + formula.replace(/"/g, '""') + '"';
        }
        let text = String(value);
        // 防止表格软件把以 = + - @ 开头的文字当成公式执行（数字本身不处理）
        if (typeof value === "string" && /^[=+\-@\t\r]/.test(text)) {
            text = "'" + text;
        }
        if (/[",\n\r]/.test(text)) {
            text = '"' + text.replace(/"/g, '""') + '"';
        }
        return text;
    }

    function csvLine(cells) {
        return cells.map(csvCell).join(",");
    }

    function buildCsv() {
        const game = report.game;
        const lines = [];

        lines.push(csvLine([t("reportTitle")]));
        lines.push(csvLine([t("csvSectionOverview")]));
        lines.push(csvLine([t("gameName"), game.name || t("unnamedGame")]));
        lines.push(csvLine([t("gameId"), game.id]));
        lines.push(csvLine([t("startedAt"), asText(game.started_at)]));
        lines.push(csvLine([t("endedAt"), asText(game.ended_at)]));
        lines.push(csvLine([t("totalBuyIn"), game.total_buy_in]));
        lines.push(csvLine([t("totalCashOut"), game.total_cash_out]));
        lines.push(csvLine([t("balanceStatus"), game.is_balanced ? t("balanced") : t("unbalanced")]));
        if (game.note) lines.push(csvLine([t("gameNote"), game.note]));
        lines.push("");

        lines.push(csvLine([t("csvSectionSummary")]));
        const summaryHead = [t("player"), t("buyIn"), t("buyInNormal"), t("buyInInsurance"), t("buyInAnti"), t("cashOut"), t("net")];
        if (report.has_events) summaryHead.push(t("buyInFromEvents"), t("checkColumn"));
        lines.push(csvLine(summaryHead));
        report.summary.forEach(p => {
            const row = [p.nickname, p.total_buy_in, p.buy_in_by_type.normal, p.buy_in_by_type.insurance,
                p.buy_in_by_type.anti, p.cash_out, p.net];
            if (report.has_events) row.push(p.buy_in_from_events, p.matches ? t("match") : t("mismatch"));
            lines.push(csvLine(row));
        });
        lines.push(csvLine([report.has_events ? (report.all_match ? t("allMatch") : t("someMismatch")) : t("noEvents")]));
        lines.push("");

        lines.push(csvLine([t("csvSectionTimeline")]));
        lines.push(csvLine([t("colTime"), t("colEvent"), t("colOperator"), t("colPlayer"), t("colAmount"), t("colBuyType"), t("colDetail")]));
        report.events.forEach(ev => {
            lines.push(csvLine([
                asText(ev.time), t("ev_" + ev.type), ev.actor_name || t("system"), ev.target_name,
                ev.amount, buyTypeLabel(ev.buy_type), eventDetail(ev),
            ]));
        });
        lines.push("");

        const now = new Date();
        const pad = n => String(n).padStart(2, "0");
        lines.push(csvLine([t("csvExportedAt"), asText(
            `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`,
        )]));

        // 开头的 BOM 让 Excel 按 UTF-8 打开，中文不乱码
        return "﻿" + lines.join("\r\n");
    }

    window.__gameReportExportCsv = function () {
        if (!report) return;
        const blob = new Blob([buildCsv()], { type: "text/csv;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const safeName = String(report.game.name || "").replace(/[\\/:*?"<>|\r\n\t]+/g, " ").trim().slice(0, 60);
        const base = safeName ? `${safeName}_${report.game.id}` : `game_${report.game.id}`;
        const a = document.createElement("a");
        a.href = url;
        a.download = `${base}_${t("csvFileSuffix")}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    };

    // ───── 加载 ─────

    async function load() {
        const params = new URLSearchParams(window.location.search);
        const gameId = params.get("game_id");
        const groupId = params.get("group_id");
        if (!gameId || !/^\d+$/.test(gameId)) {
            showMessage("invalidLink");
            return;
        }

        const query = new URLSearchParams({ game_id: gameId });
        if (groupId && /^\d+$/.test(groupId)) query.set("group_id", groupId);

        try {
            const res = await fetch(`/game-report/data?${query.toString()}`);
            const data = await res.json();
            if (!data.success) {
                showMessage(data.message || "operationFailed");
                return;
            }
            report = data;
            render();
        } catch (e) {
            showMessage("operationFailed");
        }
    }

    // 从本站牌局日志跳转过来时，"返回"用浏览器后退，回到原来的页码、搜索和选中的组；
    // 直接打开链接等其他情况，按链接回到对应角色的牌局日志
    function setupBackLink() {
        const back = document.querySelector(".report-back");
        if (!back) return;
        back.addEventListener("click", event => {
            let fromSameSite = false;
            try {
                fromSameSite = !!document.referrer && new URL(document.referrer).origin === window.location.origin;
            } catch (e) {
                fromSameSite = false;
            }
            if (fromSameSite && window.history.length > 1) {
                event.preventDefault();
                window.history.back();
            }
        });
    }

    window.onLanguageApplied = function () {
        if (report) {
            render();
        } else if (messageKey) {
            showMessage(messageKey);
        }
    };

    function init() {
        setupBackLink();
        load();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();


// 页面按钮 data-on-click="exportAuditCsv" 调用的入口
function exportAuditCsv() {
    if (typeof window.__gameReportExportCsv === "function") {
        window.__gameReportExportCsv();
    }
}

/**
 * escape.js — 通用 HTML 转义。
 * 凡是把用户可控或来自数据库的字符串拼进 innerHTML / 模板字符串的地方，都必须用 escapeHtml 包起来。
 */
function escapeHtml(value) {
    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

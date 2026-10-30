/**
 * text_format.js — 按当前界面语言选择标点。
 * 中文用全角冒号和顿号，英文用半角冒号、逗号，避免英文界面出现“Buy-in：100”“A、B”。
 * 依赖 language.js 的 getCurrentLanguage()（没有时按中文处理）。
 */
function isEnglishUi() {
    return typeof getCurrentLanguage === "function" && getCurrentLanguage() === "en";
}

// "买入" → "买入："；"Buy-in" → "Buy-in: "
function withColon(label) {
    return label + (isEnglishUi() ? ": " : "：");
}

// ["A", "B"] → "A、B" / "A, B"
function joinNames(names) {
    return (names || []).join(isEnglishUi() ? ", " : "、");
}

// 括号内的补充说明："50%（3次）" / "50% (3 times)"
function withParen(text, inner) {
    return isEnglishUi() ? `${text} (${inner})` : `${text}（${inner}）`;
}

// "3次" / "3 times"（需要页面翻译里有 times）
function countTimes(n) {
    return isEnglishUi() ? `${n} ${t("times")}` : `${n}${t("times")}`;
}

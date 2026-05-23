function getCurrentLanguage() {
    return localStorage.getItem("language") || "zh";
}


function getTranslations() {
    return {
        zh: {
            ...(window.loginTranslations?.zh || {}),
            ...(window.registerTranslations?.zh || {}),
            ...(window.adminTranslations?.zh || {})
        },

        en: {
            ...(window.loginTranslations?.en || {}),
            ...(window.registerTranslations?.en || {}),
            ...(window.adminTranslations?.en || {})
        }
    };
}


function setLanguage(language) {
    localStorage.setItem("language", language);
    applyLanguage();
}


function toggleLanguage() {
    const currentLanguage = getCurrentLanguage();

    if (currentLanguage === "zh") {
        setLanguage("en");
    } else {
        setLanguage("zh");
    }
}


function t(key) {
    const language = getCurrentLanguage();
    const translations = getTranslations();

    if (!key) {
        return "";
    }

    return translations[language][key] || key;
}


function applyLanguage() {
    const language = getCurrentLanguage();
    const translations = getTranslations();
    const dict = translations[language];

    document.querySelectorAll("[data-i18n]").forEach(element => {
        const key = element.getAttribute("data-i18n");
        element.innerText = dict[key] || key;
    });

    document.querySelectorAll("[data-i18n-placeholder]").forEach(element => {
        const key = element.getAttribute("data-i18n-placeholder");
        element.placeholder = dict[key] || key;
    });

    const toggleButton = document.getElementById("language-toggle");

    if (toggleButton) {
        toggleButton.innerText = language === "zh" ? "ENGLISH" : "中文";
    }
}


document.addEventListener("DOMContentLoaded", applyLanguage);
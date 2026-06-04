function getCurrentLanguage() {
    return (
        localStorage.getItem("language")
        || "zh"
    );
}


function getTranslations(language) {

    if (window.adminTranslations) {
        return window.adminTranslations[language];
    }

    if (window.loginTranslations) {
        return window.loginTranslations[language];
    }

    if (window.registerTranslations) {
        return window.registerTranslations[language];
    }

    if (window.groupSelectTranslations) {
        return window.groupSelectTranslations[language];
    }

     if (window.userTranslations) {
        return window.userTranslations[language];
    }

    if (window.organizerTranslations) {
        return window.organizerTranslations[language];
    }

    return {};
}


function t(key) {
    const language =
        getCurrentLanguage();

    const translations =
        getTranslations(language);

    if (
        !translations
        || !translations[key]
    ) {
        return key;
    }

    return translations[key];
}


function setLanguage(language) {
    localStorage.setItem(
        "language",
        language
    );

    applyLanguage(language);
}


function toggleLanguage() {
    const currentLanguage =
        getCurrentLanguage();

    const nextLanguage =
        currentLanguage === "zh"
            ? "en"
            : "zh";

    setLanguage(nextLanguage);
}


function applyLanguage(language = getCurrentLanguage()) {
    const translations =
        getTranslations(language);

    if (!translations) {
        return;
    }

    document.documentElement.lang =
        language;

    document
        .querySelectorAll("[data-i18n]")
        .forEach(element => {
            const key =
                element.getAttribute("data-i18n");

            if (key && translations[key]) {
                element.innerText =
                    translations[key];
            }
        });

    document
        .querySelectorAll("[data-i18n-placeholder]")
        .forEach(element => {
            const key =
                element.getAttribute("data-i18n-placeholder");

            if (key && translations[key]) {
                element.placeholder =
                    translations[key];
            }
        });

    const toggleButton =
        document.getElementById("language-toggle");

    if (toggleButton) {
        toggleButton.innerText =
            language === "zh"
                ? "ENGLISH"
                : "中文";
    }

    if (typeof renderUsers === "function" && Array.isArray(allUsers)) {
        renderUsers(allUsers);
    }

    if (typeof refreshSelectedUserLanguage === "function") {
        refreshSelectedUserLanguage();
    }
}


document.addEventListener(
    "DOMContentLoaded",
    () => {
        applyLanguage();
    }
);
/* Crowd-Funding Egypt — Admin UI
   Theme toggle (light/dark/auto) + helpful sidebar helpers.
*/
(function () {
    "use strict";

    var root = document.documentElement;

    /* ---------------------------------------------------------------
       Theme cycle: light -> dark -> auto -> light
       The class "is-dark" mirrors the icon so the sun icon shows when
       the effective theme is dark (works for explicit + auto modes).
       --------------------------------------------------------------- */
    function effectiveDark() {
        var stored = root.dataset.theme;
        if (stored === "dark") return true;
        if (stored === "light") return false;
        return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    }

    function syncToggles() {
        var dark = effectiveDark();
        document.querySelectorAll(".cf-theme-toggle").forEach(function (btn) {
            btn.classList.toggle("is-dark", dark);
        });
    }

    function setTheme(next) {
        try {
            localStorage.setItem("theme", next);
        } catch (e) {}
        root.dataset.theme = next;
        syncToggles();
    }

    function nextTheme(current) {
        if (current === "light") return "dark";
        if (current === "dark") return "auto";
        return "light";
    }

    document.querySelectorAll(".cf-theme-toggle").forEach(function (btn) {
        btn.addEventListener("click", function () {
            var current = root.dataset.theme || "auto";
            setTheme(nextTheme(current));
        });
    });

    if (window.matchMedia) {
        window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", syncToggles);
    }
    syncToggles();
})();
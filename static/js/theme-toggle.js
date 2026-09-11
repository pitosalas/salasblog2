(function () {
    const STORAGE_KEY = "theme";
    const root = document.documentElement;

    function storedOrSystemTheme() {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored === "light" || stored === "dark") return stored;
        return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }

    root.setAttribute("data-theme", storedOrSystemTheme());

    document.addEventListener("DOMContentLoaded", function () {
        const button = document.getElementById("theme-toggle");
        if (!button) return;

        function updateLabel() {
            button.textContent = root.getAttribute("data-theme") === "dark" ? "light mode" : "dark mode";
        }

        updateLabel();
        button.addEventListener("click", function () {
            const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
            localStorage.setItem(STORAGE_KEY, next);
            root.setAttribute("data-theme", next);
            updateLabel();
        });
    });
})();

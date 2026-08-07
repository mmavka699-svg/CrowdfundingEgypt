/**
 * Crowd-Funding Egypt — Global Frontend Logic & UI Interactions.
 * Powered by Vanilla JS & Bootstrap 5 Bundle.
 */
document.addEventListener("DOMContentLoaded", function () {

    // --------------------------------------------------------------
    // 1. Sticky Navbar Glass Scroll Effect
    // --------------------------------------------------------------
    const navbar = document.querySelector(".navbar");
    if (navbar) {
        window.addEventListener("scroll", function () {
            if (window.scrollY > 20) {
                navbar.classList.add("scrolled");
            } else {
                navbar.classList.remove("scrolled");
            }
        });
    }

    // --------------------------------------------------------------
    // 2. Scroll Reveal Animations (data-animate="fade-up")
    // --------------------------------------------------------------
    const animatedElements = document.querySelectorAll('[data-animate="fade-up"]');
    if (animatedElements.length > 0) {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("animated");
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.15 }
        );

        animatedElements.forEach((el) => observer.observe(el));
    }

    // --------------------------------------------------------------
    // Helper: Number Formatter (Thousands Separators)
    // --------------------------------------------------------------
    function formatNumberWithCommas(val) {
        if (val === null || val === undefined) return "";
        let str = val.toString().replace(/[^0-9.]/g, "");
        if (str === "") return "";
        const parts = str.split(".");
        if (parts.length > 2) {
            parts[1] = parts.slice(1).join("");
            parts.length = 2;
        }
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        if (parts[1] !== undefined) {
            parts[1] = parts[1].slice(0, 2);
        }
        return parts.join(".");
    }

    // --------------------------------------------------------------
    // 3. Preset Donation Chip Buttons & Financial Inputs Formatter
    // --------------------------------------------------------------
    const financialInputs = document.querySelectorAll(".number-format-input, input[name='amount'], input[name='total_target']");

    financialInputs.forEach((input) => {
        // Convert type="number" to type="text" so browser permits commas without clearing input
        if (input.type === "number") {
            input.type = "text";
        }
        input.setAttribute("inputmode", "decimal");

        // Format initial value on page load
        if (input.value) {
            input.value = formatNumberWithCommas(input.value);
        }

        input.addEventListener("input", function () {
            this.value = formatNumberWithCommas(this.value);
        });

        // Unformat on form submit so Django receives clean numeric string
        const form = input.closest("form");
        if (form && !form.dataset.numberFormatAttached) {
            form.dataset.numberFormatAttached = "true";
            form.addEventListener("submit", function () {
                form.querySelectorAll(".number-format-input, input[name='amount'], input[name='total_target']").forEach((inp) => {
                    inp.value = inp.value.replace(/,/g, "");
                });
            });
        }
    });

    const presetChips = document.querySelectorAll(".preset-chip");
    const donationInput = document.querySelector('input[name="amount"]');

    if (presetChips.length > 0 && donationInput) {
        presetChips.forEach((chip) => {
            chip.addEventListener("click", function () {
                presetChips.forEach((c) => c.classList.remove("active"));
                this.classList.add("active");
                donationInput.value = formatNumberWithCommas(this.dataset.amount);
                donationInput.focus();
            });
        });

        donationInput.addEventListener("input", function () {
            const cleanVal = this.value.replace(/,/g, "");
            presetChips.forEach((c) => {
                if (c.dataset.amount === cleanVal) {
                    c.classList.add("active");
                } else {
                    c.classList.remove("active");
                }
            });
        });
    }

    // --------------------------------------------------------------
    // 4. Toggle Nested Reply Forms (Comment Section)
    // --------------------------------------------------------------
    document.querySelectorAll(".reply-toggle").forEach(function (link) {
        link.addEventListener("click", function (e) {
            e.preventDefault();
            const commentId = this.dataset.commentId;
            const form = document.getElementById("reply-form-" + commentId);
            if (form) {
                form.classList.toggle("d-none");
                if (!form.classList.contains("d-none")) {
                    const textarea = form.querySelector("textarea");
                    if (textarea) textarea.focus();
                }
            }
        });
    });

    // --------------------------------------------------------------
    // 5. CSRF Helper Token Reader
    // --------------------------------------------------------------
    window.getCsrfToken = function () {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? match[1] : "";
    };

    // --------------------------------------------------------------
    // 6. Auto-dismiss Toast Alerts
    // --------------------------------------------------------------
    document.querySelectorAll(".alert-dismissible").forEach(function (alertEl) {
        setTimeout(function () {
            if (window.bootstrap && bootstrap.Alert) {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
                if (bsAlert) bsAlert.close();
            }
        }, 5000);
    });

    // --------------------------------------------------------------
    // 7. Stat Counter Animation
    // --------------------------------------------------------------
    const counterElements = document.querySelectorAll(".stat-value[data-count]");
    if (counterElements.length > 0) {
        const counterObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        const target = entry.target;
                        const countTo = parseInt(target.dataset.count, 10);
                        const suffix = target.dataset.suffix || "";
                        let currentCount = 0;
                        const step = Math.max(1, Math.floor(countTo / 40));

                        const timer = setInterval(() => {
                            currentCount += step;
                            if (currentCount >= countTo) {
                                target.textContent = countTo.toLocaleString() + suffix;
                                clearInterval(timer);
                            } else {
                                target.textContent = currentCount.toLocaleString() + suffix;
                            }
                        }, 30);

                        counterObserver.unobserve(target);
                    }
                });
            },
            { threshold: 0.5 }
        );

        counterElements.forEach((el) => counterObserver.observe(el));
    }

    // --------------------------------------------------------------
    // 8. Toggle Comments Hide/Show Collapse Icon & Text
    // --------------------------------------------------------------
    const commentsCollapse = document.getElementById("commentsFeedCollapse");
    const toggleCommentsBtn = document.getElementById("toggleCommentsBtn");

    if (commentsCollapse && toggleCommentsBtn) {
        commentsCollapse.addEventListener("hide.bs.collapse", function () {
            const icon = document.getElementById("toggleCommentsIcon");
            const text = document.getElementById("toggleCommentsText");
            if (icon) icon.className = "bi bi-eye-fill me-1";
            if (text) text.textContent = "Show Comments";
        });

        commentsCollapse.addEventListener("show.bs.collapse", function () {
            const icon = document.getElementById("toggleCommentsIcon");
            const text = document.getElementById("toggleCommentsText");
            if (icon) icon.className = "bi bi-eye-slash-fill me-1";
            if (text) text.textContent = "Hide Comments";
        });
    }

    // --------------------------------------------------------------
    // 9. Dynamic Nested Replies Hide/Extend Event Listeners
    // --------------------------------------------------------------
    document.addEventListener("hide.bs.collapse", function (e) {
        if (e.target.id && e.target.id.startsWith("replies-collapse-")) {
            const commentId = e.target.id.replace("replies-collapse-", "");
            const icon = document.getElementById("toggle-replies-icon-" + commentId);
            const text = document.getElementById("toggle-replies-text-" + commentId);
            const count = e.target.querySelectorAll(".comment-card").length;
            if (icon) icon.className = "bi bi-chevron-down me-1";
            if (text) text.textContent = "Show " + count + (count === 1 ? " reply" : " replies");
        }
    });

    document.addEventListener("show.bs.collapse", function (e) {
        if (e.target.id && e.target.id.startsWith("replies-collapse-")) {
            const commentId = e.target.id.replace("replies-collapse-", "");
            const icon = document.getElementById("toggle-replies-icon-" + commentId);
            const text = document.getElementById("toggle-replies-text-" + commentId);
            const count = e.target.querySelectorAll(".comment-card").length;
            if (icon) icon.className = "bi bi-chevron-up me-1";
            if (text) text.textContent = "Hide " + count + (count === 1 ? " reply" : " replies");
        }
    });

    // --------------------------------------------------------------
    // 10. Light / Dark Mode Theme Manager & Persistence
    // --------------------------------------------------------------
    const themeToggleBtn = document.getElementById("themeToggleBtn");

    function applyTheme(theme) {
        document.documentElement.setAttribute("data-theme", theme);
        localStorage.setItem("theme", theme);
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", function () {
            const currentTheme = document.documentElement.getAttribute("data-theme") || "light";
            const newTheme = currentTheme === "dark" ? "light" : "dark";
            applyTheme(newTheme);
        });
    }

    // Listen for OS color scheme changes if user hasn't set explicit preference
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener("change", function (e) {
            if (!localStorage.getItem("theme")) {
                applyTheme(e.matches ? "dark" : "light");
            }
        });
    }
});

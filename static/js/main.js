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
        if (input.type === "number") {
            input.type = "text";
        }
        input.setAttribute("inputmode", "decimal");

        if (input.value) {
            input.value = formatNumberWithCommas(input.value);
        }

        input.addEventListener("input", function () {
            this.value = formatNumberWithCommas(this.value);
        });

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

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener("change", function (e) {
            if (!localStorage.getItem("theme")) {
                applyTheme(e.matches ? "dark" : "light");
            }
        });
    }

    // --------------------------------------------------------------
    // 11. Complete Live Search Autocomplete & Keyboard Navigation
    // --------------------------------------------------------------
    const searchInput = document.querySelector(".nav-search-wrapper input");
    const dropdown = document.querySelector(".nav-search-wrapper .search-autocomplete-dropdown");
    let selectedIndex = -1;
    let searchTimeout = null;

    if (searchInput && dropdown) {

        // A. Live Fetching Data on Input (Debounced)
        searchInput.addEventListener("input", function () {
            const query = this.value.trim();
            clearTimeout(searchTimeout);

            if (!query) {
                hideDropdown();
                return;
            }

            searchTimeout = setTimeout(() => {
                fetch(`/projects/autocomplete/?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        dropdown.innerHTML = "";
                        selectedIndex = -1;

                        if (data.results && data.results.length > 0) {
                            data.results.forEach(item => {
                                const a = document.createElement("a");
                                a.href = item.url;
                                a.className = "search-autocomplete-item list-group-item list-group-item-action d-flex align-items-center gap-2 p-2";
                                a.innerHTML = `
                                    ${item.image ? `<img src="${item.image}" class="rounded" style="width: 40px; height: 40px; object-fit: cover;">` : ''}
                                    <div>
                                        <div class="fw-semibold text-truncate" style="max-width: 200px;">${item.title}</div>
                                        ${item.category ? `<small class="text-muted">${item.category}</small>` : ''}
                                    </div>
                                `;
                                dropdown.appendChild(a);
                            });
                            showDropdown();
                        } else {
                            dropdown.innerHTML = `<div class="p-3 text-muted text-center small">No campaigns found</div>`;
                            showDropdown();
                        }
                    })
                    .catch(err => {
                        console.error("Search fetch error:", err);
                        hideDropdown();
                    });
            }, 300);
        });

        // B. Re-show Dropdown on Focus
        searchInput.addEventListener("focus", function () {
            if (this.value.trim() && dropdown.children.length > 0) {
                showDropdown();
            }
        });

        // C. Keyboard Controls (Arrow Up/Down, Enter, Escape)
        searchInput.addEventListener("keydown", function (e) {
            const items = dropdown.querySelectorAll(".search-autocomplete-item");
            if (!items.length || dropdown.classList.contains("d-none")) return;

            if (e.key === "ArrowDown") {
                e.preventDefault();
                selectedIndex = (selectedIndex + 1) % items.length;
                updateHighlight(items);
            } else if (e.key === "ArrowUp") {
                e.preventDefault();
                selectedIndex = (selectedIndex - 1 + items.length) % items.length;
                updateHighlight(items);
            } else if (e.key === "Enter" && selectedIndex >= 0 && items[selectedIndex]) {
                e.preventDefault();
                items[selectedIndex].click();
            } else if (e.key === "Escape") {
                hideDropdown();
            }
        });

        // Helper Functions
        function updateHighlight(items) {
            items.forEach((item, index) => {
                if (index === selectedIndex) {
                    item.classList.add("active");
                    item.scrollIntoView({ block: "nearest" });
                } else {
                    item.classList.remove("active");
                }
            });
        }

        function showDropdown() {
            dropdown.classList.remove("d-none");
        }

        function hideDropdown() {
            dropdown.classList.add("d-none");
            selectedIndex = -1;
        }

        // D. Close Dropdown on Outside Click
        document.addEventListener("click", function (e) {
            if (!searchInput.closest(".nav-search-wrapper").contains(e.target)) {
                hideDropdown();
            }
        });
    }
});
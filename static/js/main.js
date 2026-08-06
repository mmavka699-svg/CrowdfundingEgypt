/**
 * Crowd-Funding Egypt — global front-end interactions.
 * Vanilla JS, no framework dependency beyond Bootstrap's bundle (for modals/carousels).
 */
document.addEventListener("DOMContentLoaded", function () {

    // --------------------------------------------------------------
    // Toggle nested reply forms under each comment (bonus feature UI)
    // --------------------------------------------------------------
    document.querySelectorAll(".reply-toggle").forEach(function (link) {
        link.addEventListener("click", function (e) {
            e.preventDefault();
            const commentId = this.dataset.commentId;
            const form = document.getElementById("reply-form-" + commentId);
            if (form) {
                form.classList.toggle("d-none");
                if (!form.classList.contains("d-none")) {
                    form.querySelector("textarea").focus();
                }
            }
        });
    });

    // --------------------------------------------------------------
    // Helper: read CSRF token from cookies (for any future fetch() calls)
    // --------------------------------------------------------------
    window.getCsrfToken = function () {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? match[1] : "";
    };

    // --------------------------------------------------------------
    // Auto-dismiss alert messages after 5 seconds
    // --------------------------------------------------------------
    document.querySelectorAll(".alert").forEach(function (alertEl) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
            bsAlert.close();
        }, 5000);
    });
});

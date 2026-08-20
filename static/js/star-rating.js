/**
 * Interactive 1-5 star rating widget.
 * Sends an AJAX POST to /projects/<slug>/rate/ and updates the average
 * rating shown on the page without a full reload.
 */
document.addEventListener("DOMContentLoaded", function () {
    const widget = document.querySelector(".star-rating");
    if (!widget) return;

    const slug = widget.dataset.projectSlug;
    const stars = widget.querySelectorAll(".star-icon");

    function paintStars(value) {
        stars.forEach(function (star) {
            const starValue = parseInt(star.dataset.value, 10);
            star.classList.toggle("fa-solid", starValue <= value);
            star.classList.toggle("fa-regular", starValue > value);
        });
    }

    // Hover preview
    stars.forEach(function (star) {
        star.addEventListener("mouseenter", function () {
            paintStars(parseInt(star.dataset.value, 10));
        });
    });
    widget.addEventListener("mouseleave", function () {
        paintStars(parseInt(widget.dataset.current, 10));
    });

    // Click -> submit rating via AJAX
    stars.forEach(function (star) {
        star.addEventListener("click", function () {
            const value = parseInt(star.dataset.value, 10);

            fetch(`/projects/${slug}/rate/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": window.getCsrfToken(),
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body: `stars=${value}`,
            })
                .then((res) => res.json())
                .then((data) => {
                    if (data.success) {
                        widget.dataset.current = data.your_rating;
                        paintStars(data.your_rating);

                        // Update the average rating badge shown near the title
                        const avgBadge = document.getElementById("avg-rating-display");
                        if (avgBadge) {
                            avgBadge.textContent = `${data.average_rating} / 5`;
                        }
                        const countLabel = document.getElementById("ratings-count-display");
                        if (countLabel) {
                            countLabel.textContent =
                                `(${data.ratings_count} rating${data.ratings_count === 1 ? "" : "s"})`;
                        }
                    } else {
                        alert(data.error || "Could not submit rating.");
                    }
                })
                .catch(() => alert("Network error — please try again."));
        });
    });
});

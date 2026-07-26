document.addEventListener("DOMContentLoaded", function () {



    const themeToggle =
        document.getElementById("themeToggle");

    const savedTheme =
        localStorage.getItem("whatif-theme");

    if (savedTheme === "dark") {
        document.body.classList.add("dark-mode");
        updateThemeIcon(true);
    }

    if (themeToggle) {

        themeToggle.addEventListener(
            "click",
            function () {

                const isDark =
                    document.body.classList.toggle(
                        "dark-mode"
                    );

                localStorage.setItem(
                    "whatif-theme",
                    isDark ? "dark" : "light"
                );

                updateThemeIcon(isDark);
            }
        );
    }

    function updateThemeIcon(isDark) {

        if (!themeToggle) {
            return;
        }

        themeToggle.innerHTML = isDark
            ? '<i class="bi bi-sun"></i>'
            : '<i class="bi bi-moon-stars-fill"></i>';
    }




    const textarea =
        document.getElementById("decisionText");

    const charCount =
        document.getElementById("charCount");

    if (textarea && charCount) {

        function updateCharacterCount() {
            charCount.textContent =
                textarea.value.length;
        }

        updateCharacterCount();

        textarea.addEventListener(
            "input",
            updateCharacterCount
        );
    }




    const decisionForm =
        document.getElementById("decisionForm");

    const analyzeButton =
        document.getElementById("analyzeButton");

    const analysisOverlay =
        document.getElementById("analysisOverlay");

    if (
        decisionForm &&
        analyzeButton &&
        analysisOverlay
    ) {

        decisionForm.addEventListener(
            "submit",
            function () {

                if (!decisionForm.checkValidity()) {
                    return;
                }

                analyzeButton.classList.add("loading");
                analyzeButton.disabled = true;

                analysisOverlay.classList.add("visible");

                analysisOverlay.setAttribute(
                    "aria-hidden",
                    "false"
                );

                const steps =
                    analysisOverlay.querySelectorAll(
                        ".analysis-steps p"
                    );

                let currentStep = 0;

                window.setInterval(
                    function () {

                        steps.forEach(
                            function (step, index) {

                                step.classList.toggle(
                                    "active",
                                    index === currentStep
                                );

                                const icon =
                                    step.querySelector("i");

                                if (!icon) {
                                    return;
                                }

                                if (index < currentStep) {

                                    icon.className =
                                        "bi bi-check-circle-fill";

                                } else if (
                                    index === currentStep
                                ) {

                                    icon.className =
                                        "bi bi-stars";

                                } else {

                                    icon.className =
                                        "bi bi-circle";
                                }
                            }
                        );

                        currentStep =
                            (currentStep + 1) %
                            steps.length;

                    },
                    950
                );
            }
        );
    }




    const counters =
        document.querySelectorAll(
            "[data-counter]"
        );

    counters.forEach(
        function (counter) {

            const target =
                Number(
                    counter.getAttribute(
                        "data-counter"
                    )
                ) || 0;

            const duration =  2500;

            const startTime =
                performance.now();

            counter.textContent = "0";

            function animateCounter(currentTime) {

                const elapsed =
                    currentTime - startTime;

                const progress =
                    Math.min(
                        elapsed / duration,
                        1
                    );

                const easedProgress =
                    1 -
                    Math.pow(
                        1 - progress,
                        4
                    );

                const currentValue =
                    Math.round(
                        target * easedProgress
                    );

                counter.textContent =
                    currentValue.toLocaleString("ar-SA");

                if (progress < 1) {

                    requestAnimationFrame(
                        animateCounter
                    );

                } else {

                    counter.textContent =
                        target.toLocaleString("ar-SA");
                }
            }

            requestAnimationFrame(
                animateCounter
            );
        }
    );




    const revealCards =
        document.querySelectorAll(
            ".reveal-card"
        );

    revealCards.forEach(
        function (card, index) {

            window.setTimeout(
                function () {

                    card.classList.add(
                        "visible"
                    );

                },
                250 + index * 220
            );
        }
    );
});
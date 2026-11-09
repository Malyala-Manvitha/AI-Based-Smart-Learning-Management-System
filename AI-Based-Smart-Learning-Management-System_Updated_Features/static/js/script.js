document.addEventListener("DOMContentLoaded", function () {

    // Auto-hide flash messages
    document.querySelectorAll(".alert").forEach(function (alert) {
        setTimeout(function () { alert.style.display = "none"; }, 5000);
    });

    // Quiz countdown timer: submits the form automatically at zero
    const timer = document.getElementById("quiz-timer");

    if (timer) {
        let remaining = parseInt(timer.dataset.seconds, 10) || 300;
        const form = timer.closest(".card").querySelector("form");
        const bar = timer.closest(".timer-bar");

        const tick = function () {
            const m = String(Math.floor(remaining / 60)).padStart(2, "0");
            const s = String(remaining % 60).padStart(2, "0");
            timer.textContent = m + ":" + s;

            if (remaining <= 30) { bar.classList.add("low"); }

            if (remaining <= 0) {
                clearInterval(handle);
                form.noValidate = true;   // unanswered questions are simply marked wrong
                form.submit();
            }
            remaining -= 1;
        };

        const handle = setInterval(tick, 1000);
        tick();

        form.addEventListener("submit", function () { clearInterval(handle); });
    }
});

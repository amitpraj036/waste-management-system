function getLocation() {

    const status = document.getElementById("location-status");

    if (!navigator.geolocation) {

        status.textContent =
            "❌ Geolocation is not supported by your browser.";

        return;
    }

    status.textContent =
        "📍 Getting your location...";

    navigator.geolocation.getCurrentPosition(

        function(position) {

            const latitude =
                position.coords.latitude;

            const longitude =
                position.coords.longitude;

            document.getElementById("latitude").value =
                latitude;

            document.getElementById("longitude").value =
                longitude;

            status.textContent =
                "✅ Location captured successfully.";

        },

        function(error) {

            status.textContent =
                "❌ Unable to get your location. Please allow location permission.";

        }

    );
}

/* =========================
   PASSWORD SHOW / HIDE
   ========================= */

function togglePassword(inputId, button) {

    const input = document.getElementById(inputId);

    if (!input) return;

    if (input.type === "password") {

        input.type = "text";
        button.textContent = "🙈";
        button.setAttribute("aria-label", "Hide password");

    } else {

        input.type = "password";
        button.textContent = "👁️";
        button.setAttribute("aria-label", "Show password");

    }
}


document.addEventListener("DOMContentLoaded", function () {
    getLocation();

    // Dark mode toggle
    const darkModeToggle = document.getElementById("darkModeToggle");
    darkModeToggle.addEventListener("change", function () {
        document.body.classList.toggle("dark-mode", this.checked);
    });
});

function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(showPosition, showError);
    } else {
        document.getElementById("location").innerText = "Geolocation not supported.";
    }
}

function showPosition(position) {
    document.getElementById("location").innerHTML =
        `Latitude: ${position.coords.latitude} <br> Longitude: ${position.coords.longitude}`;
}

function sendLocation() {
    navigator.geolocation.getCurrentPosition(function (position) {
        const data = {
            user_id: "123",
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
        };

        fetch('/update_location', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            console.log("Location Updated:", data);
            window.location.href = "/track";
        })
        .catch(error => {
            console.error("Error updating location:", error);
            alert("Failed to update location.");
        });
    });
}

function showError(error) {
    document.getElementById("location").innerHTML = "Error retrieving location.";
}

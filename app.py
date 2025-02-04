from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import os

app = Flask(__name__)

# Store location data
location_data = {}

@app.route("/", methods=["GET"])
def home():
    """Render the homepage"""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    return render_template("index.html", api_key=api_key)

@app.route("/update_location", methods=["POST"])
def update_location():
    """Update and store the live location"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid JSON data received"}), 400

        # Validate required fields
        if "latitude" not in data or "longitude" not in data:
            return jsonify({"error": "Missing latitude or longitude"}), 400

        location_data["user_id"] = data.get("user_id", "Unknown")
        location_data["latitude"] = data["latitude"]
        location_data["longitude"] = data["longitude"]

        return jsonify({"message": "Location updated successfully", "location": location_data})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500  # Return JSON error

@app.route("/track", methods=["GET"])
def track():
    """Render the tracking page"""
    return render_template("track.html", location=location_data)

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import os
from math import radians, cos, sin, asin, sqrt

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(basedir, 'instance', 'users.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Database Models
class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    invite_code = db.Column(db.String(50), unique=True, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'user'
    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class TargetDestination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    reached = db.Column(db.Boolean, default=False)  # To track if the user reached the destination

# Initialize Database
with app.app_context():
    db.create_all()

# Home Route
@app.route("/")
def home():
    return redirect(url_for("login"))

# Admin Registration Route
@app.route("/admin_register", methods=["GET", "POST"])
def admin_register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        org_name = request.form["org_name"]

        org = Organization.query.filter_by(name=org_name).first()
        if not org:
            return "Organization does not exist!", 400

        hashed_password = generate_password_hash(password)
        new_admin = User(email=email, password=hashed_password, role="admin", organization_id=org.id)
        db.session.add(new_admin)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("admin_register.html")

# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        org_name = request.form["org_name"]

        org = Organization.query.filter_by(name=org_name).first()
        if not org:
            return "Invalid Organization!", 400

        user = User.query.filter_by(email=email, organization_id=org.id).first()
        if not user or not check_password_hash(user.password, password):
            return "Invalid credentials!", 401

        session["user_id"] = user.id
        session["role"] = user.role
        session["org_id"] = user.organization_id

        return redirect(url_for("admin_dashboard" if user.role == "admin" else "user_dashboard"))

    return render_template("login.html")

# Admin Dashboard
@app.route("/admin_dashboard")
def admin_dashboard():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    return render_template("admin_dashboard.html")

# User Dashboard
@app.route("/user_dashboard")
def user_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("user_dashboard.html")

# Update User Location
@app.route("/update_location", methods=["POST"])
def update_location():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    user_id = session["user_id"]

    # Save the user's location
    new_location = Location(user_id=user_id, latitude=latitude, longitude=longitude)
    db.session.add(new_location)

    # Check if user reached their assigned target
    target = TargetDestination.query.filter_by(user_id=user_id, reached=False).first()
    if target:
        distance = haversine_distance(latitude, longitude, target.latitude, target.longitude)
        if distance < 0.05:  # If within 50 meters
            target.reached = True
            db.session.commit()
            notify_admin(user_id, latitude, longitude)

    db.session.commit()
    return jsonify({"message": "Location updated!"})

# Set Target Destination (Admin Only)
@app.route("/set_target_destination", methods=["POST"])
def set_target_destination():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    user_id = data.get("user_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    target = TargetDestination(user_id=user_id, latitude=latitude, longitude=longitude)
    db.session.add(target)
    db.session.commit()

    return jsonify({"message": "Target destination set successfully!"})

# Get All Users' Locations (Admin Only)
@app.route("/get_users_locations", methods=["GET"])
def get_users_locations():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    locations = (
        db.session.query(User.email, Location.latitude, Location.longitude)
        .join(Location, User.id == Location.user_id)
        .all()
    )

    location_data = [
        {"email": email, "latitude": lat, "longitude": lon}
        for email, lat, lon in locations
    ]

    return jsonify({"locations": location_data})

# Logout Route
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# Utility Functions
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of Earth in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c  # Distance in km

def notify_admin(user_id, latitude, longitude):
    admin_users = User.query.filter_by(role="admin").all()
    for admin in admin_users:
        print(f"🔔 User {user_id} reached the target at ({latitude}, {longitude})! Admin {admin.email} notified.")

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import os

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
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)

# Initialize Database
with app.app_context():
    db.create_all()

# ✅ Home Route
@app.route("/")
def home():
    return redirect(url_for("login"))

# ✅ Admin Registration Route
@app.route("/admin_register", methods=["GET", "POST"])
def admin_register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        org_name = request.form["org_name"]

        # Create organization
        org = Organization(name=org_name, invite_code=f"invite-{org_name.lower()}")
        db.session.add(org)
        db.session.commit()

        # Create admin user
        hashed_password = generate_password_hash(password)
        admin = User(email=email, password=hashed_password, role="admin", organization_id=org.id)
        db.session.add(admin)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("admin_register.html")

# ✅ Login Route
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

        return redirect(url_for("admin_dashboard") if user.role == "admin" else url_for("dashboard"))

    return render_template("login.html")

# ✅ User Dashboard
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("user_dashboard.html")

# ✅ Admin Dashboard
@app.route("/admin_dashboard")
def admin_dashboard():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    return render_template("admin_dashboard.html")

# ✅ Generate Invite Link (Admin Only)
@app.route("/get_invite_link")
def get_invite_link():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    admin_user = User.query.get(session["user_id"])
    org = Organization.query.get(admin_user.organization_id)

    invite_link = f"http://127.0.0.1:5000/register?invite={org.invite_code}"
    return jsonify({"invite_link": invite_link})

# ✅ Register Users with Invite Code
@app.route("/register", methods=["GET", "POST"])
def register():
    invite_code = request.args.get("invite")

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        org = Organization.query.filter_by(invite_code=invite_code).first()
        if not org:
            return "Invalid invite link!", 400

        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password=hashed_password, role="user", organization_id=org.id)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html", invite_code=invite_code)

# ✅ Update User Location
@app.route("/update_location", methods=["POST"])
def update_location():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    new_location = Location(user_id=session["user_id"], latitude=latitude, longitude=longitude)
    db.session.add(new_location)
    db.session.commit()

    return jsonify({"message": "Location updated!"})

# ✅ Admin View: Track Users' Locations
@app.route("/track_users")
def track_users():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    return render_template("track.html", api_key=api_key)

# ✅ API: Get Users' Locations (Admin Only)
@app.route("/get_users_locations", methods=["GET"])
def get_users_locations():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    locations = (
        db.session.query(User.email, Location.latitude, Location.longitude)
        .join(Location, User.id == Location.user_id)
        .all()
    )

    return jsonify({"locations": [{"email": email, "latitude": lat, "longitude": lon} for email, lat, lon in locations]})

# ✅ Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)

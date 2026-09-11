import os
import json
from datetime import datetime

from flask import Flask, request, render_template, jsonify, redirect, url_for, flash
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

import database as db
from retina_logic import analyze_retina

app = Flask(__name__)
app.secret_key = "change-this-secret-key-in-production"

UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db.init_db()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin):
    def __init__(self, row):
        self.id = row["id"]
        self.name = row["name"]
        self.email = row["email"]
        self.phone = row["phone"]
        self.dob = row["dob"]
        self.gender = row["gender"]
        self.blood_group = row["blood_group"]
        self.existing_conditions = row["existing_conditions"]
        self.emergency_contact = row["emergency_contact"]


@login_manager.user_loader
def load_user(user_id):
    row = db.get_user_by_id(user_id)
    return User(row) if row else None


# ---------------- Auth ----------------

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        dob = request.form.get("dob", "")
        gender = request.form.get("gender", "")
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not all([name, email, password]):
            flash("Please fill in all required fields.", "error")
            return render_template("signup.html")

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("signup.html")

        if db.get_user_by_email(email):
            flash("An account with this email already exists.", "error")
            return render_template("signup.html")

        password_hash = generate_password_hash(password)
        user_id = db.create_user(name, email, phone, dob, gender, password_hash)
        user_row = db.get_user_by_id(user_id)
        login_user(User(user_row))
        return redirect(url_for("dashboard"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        row = db.get_user_by_email(email)
        if row and check_password_hash(row["password_hash"], password):
            login_user(User(row))
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")
        return render_template("login.html")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ---------------- Core app ----------------

@app.route("/dashboard")
@login_required
def dashboard():
    stats = db.get_dashboard_stats(current_user.id)
    return render_template("dashboard.html", stats=stats)


@app.route("/scan")
@login_required
def scan():
    return render_template("scan.html")


@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    if "image" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    filename = secure_filename(file.filename)
    unique_name = f"{current_user.id}_{int(datetime.now().timestamp())}_{filename}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file.save(filepath)

    try:
        analysis = analyze_retina(filepath)
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

    scan_id = db.create_scan(
        user_id=current_user.id,
        image_path=filepath.replace("\\", "/"),
        result=analysis["result"],
        confidence=analysis["confidence"],
        explanation=analysis["explanation"],
        details=analysis["details"],
    )

    return jsonify({
        "scan_id": scan_id,
        "result": analysis["result"],
        "confidence": analysis["confidence"],
        "explanation": analysis["explanation"],
        "details": analysis["details"],
        "report_url": url_for("report", scan_id=scan_id),
    })


@app.route("/history")
@login_required
def history():
    status_filter = request.args.get("status", "All")
    scans = db.get_scans_by_user(current_user.id, status_filter)
    return render_template("history.html", scans=scans, active_filter=status_filter)


@app.route("/report/<int:scan_id>")
@login_required
def report(scan_id):
    scan_row = db.get_scan_by_id(scan_id, current_user.id)
    if not scan_row:
        flash("Report not found.", "error")
        return redirect(url_for("history"))
    details = json.loads(scan_row["details"]) if scan_row["details"] else {}
    return render_template("report.html", scan=scan_row, details=details)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        db.update_profile(
            current_user.id,
            name=request.form.get("name", current_user.name),
            phone=request.form.get("phone", ""),
            gender=request.form.get("gender", ""),
            blood_group=request.form.get("blood_group", ""),
            existing_conditions=request.form.get("existing_conditions", ""),
            emergency_contact=request.form.get("emergency_contact", ""),
        )
        flash("Profile updated.", "success")
        return redirect(url_for("profile"))

    user_row = db.get_user_by_id(current_user.id)
    return render_template("profile.html", user=user_row)


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        user_row = db.get_user_by_id(current_user.id)

        if not check_password_hash(user_row["password_hash"], current_password):
            flash("Current password is incorrect.", "error")
        elif len(new_password) < 6:
            flash("New password must be at least 6 characters.", "error")
        else:
            db.update_password(current_user.id, generate_password_hash(new_password))
            flash("Password changed successfully.", "success")

        return redirect(url_for("settings"))

    return render_template("settings.html")


if __name__ == "__main__":
    app.run(debug=True)
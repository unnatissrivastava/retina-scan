import os
import json
from datetime import datetime

from flask import (
    Flask,
    request,
    render_template,
    jsonify,
    redirect,
    url_for,
    flash
)

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.utils import secure_filename
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

import database as db
from retina_logic import analyze_retina


# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(__name__)

# Development secret key
# For production, move this to an environment variable.
app.secret_key = "change-this-secret-key-in-production"


# =========================================================
# UPLOAD CONFIGURATION
# =========================================================

UPLOAD_FOLDER = os.path.join(
    "static",
    "uploads"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Allowed image extensions
ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp"
}


def allowed_file(filename):
    """
    Check whether the uploaded file has an allowed image extension.
    """

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# =========================================================
# DATABASE
# =========================================================

db.init_db()


# =========================================================
# LOGIN MANAGER
# =========================================================

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"


# =========================================================
# USER MODEL
# =========================================================

class User(UserMixin):

    def __init__(self, row):

        self.id = row["id"]
        self.name = row["name"]
        self.email = row["email"]
        self.phone = row["phone"]
        self.dob = row["dob"]
        self.gender = row["gender"]

        self.blood_group = row["blood_group"]

        self.existing_conditions = (
            row["existing_conditions"]
        )

        self.emergency_contact = (
            row["emergency_contact"]
        )


# =========================================================
# LOAD USER
# =========================================================

@login_manager.user_loader
def load_user(user_id):

    row = db.get_user_by_id(user_id)

    if row:
        return User(row)

    return None


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    if current_user.is_authenticated:
        return redirect(
            url_for("dashboard")
        )

    return redirect(
        url_for("login")
    )


# =========================================================
# SIGN UP
# =========================================================

@app.route(
    "/signup",
    methods=["GET", "POST"]
)
def signup():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        dob = request.form.get(
            "dob",
            ""
        )

        gender = request.form.get(
            "gender",
            ""
        )

        password = request.form.get(
            "password",
            ""
        )

        confirm = request.form.get(
            "confirm_password",
            ""
        )

        # ---------------------------------------------
        # Required fields
        # ---------------------------------------------

        if not all([
            name,
            email,
            password
        ]):

            flash(
                "Please fill in all required fields.",
                "error"
            )

            return render_template(
                "signup.html"
            )

        # ---------------------------------------------
        # Password confirmation
        # ---------------------------------------------

        if password != confirm:

            flash(
                "Passwords do not match.",
                "error"
            )

            return render_template(
                "signup.html"
            )

        # ---------------------------------------------
        # Existing account
        # ---------------------------------------------

        if db.get_user_by_email(email):

            flash(
                "An account with this email already exists.",
                "error"
            )

            return render_template(
                "signup.html"
            )

        # ---------------------------------------------
        # Create user
        # ---------------------------------------------

        password_hash = generate_password_hash(
            password
        )

        user_id = db.create_user(
            name,
            email,
            phone,
            dob,
            gender,
            password_hash
        )

        user_row = db.get_user_by_id(
            user_id
        )

        login_user(
            User(user_row)
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "signup.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        # ---------------------------------------------
        # Find user
        # ---------------------------------------------

        row = db.get_user_by_email(
            email
        )

        # ---------------------------------------------
        # Validate password
        # ---------------------------------------------

        if (
            row
            and check_password_hash(
                row["password_hash"],
                password
            )
        ):

            login_user(
                User(row)
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid email or password.",
            "error"
        )

        return render_template(
            "login.html"
        )

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("login")
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    stats = db.get_dashboard_stats(
        current_user.id
    )

    return render_template(
        "dashboard.html",
        stats=stats
    )


# =========================================================
# SCAN PAGE
# =========================================================

@app.route("/scan")
@login_required
def scan():

    return render_template(
        "scan.html"
    )


# =========================================================
# ANALYZE RETINAL IMAGE
# =========================================================

@app.route(
    "/analyze",
    methods=["POST"]
)
@login_required
def analyze():

    # -----------------------------------------------------
    # Check whether image was uploaded
    # -----------------------------------------------------

    if "image" not in request.files:

        return jsonify({
            "error": "No image uploaded. Please select a retinal image."
        }), 400


    file = request.files["image"]


    # -----------------------------------------------------
    # Check empty filename
    # -----------------------------------------------------

    if file.filename == "":

        return jsonify({
            "error": "No image selected. Please choose an image."
        }), 400


    # -----------------------------------------------------
    # Check extension
    # -----------------------------------------------------

    if not allowed_file(file.filename):

        return jsonify({
            "error": (
                "Unsupported file type. "
                "Please upload a JPG, JPEG, PNG, or WEBP image."
            )
        }), 400


    # -----------------------------------------------------
    # Secure filename
    # -----------------------------------------------------

    filename = secure_filename(
        file.filename
    )


    # -----------------------------------------------------
    # Create unique filename
    # -----------------------------------------------------

    timestamp = int(
        datetime.now().timestamp()
    )

    unique_name = (
        f"{current_user.id}_"
        f"{timestamp}_"
        f"{filename}"
    )


    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        unique_name
    )


    # -----------------------------------------------------
    # Save uploaded image
    # -----------------------------------------------------

    try:

        file.save(filepath)

    except Exception as e:

        return jsonify({
            "error": (
                f"Could not save the uploaded image: {str(e)}"
            )
        }), 500


    # =====================================================
    # RUN RETINAL ANALYSIS
    # =====================================================

    try:

        analysis = analyze_retina(
            filepath
        )


    # -----------------------------------------------------
    # INVALID / NON-RETINAL IMAGE
    # -----------------------------------------------------

    except ValueError as e:

        # Delete invalid image
        if os.path.exists(filepath):

            try:
                os.remove(filepath)
            except OSError:
                pass


        return jsonify({
            "error": str(e)
        }), 400


    # -----------------------------------------------------
    # OTHER ANALYSIS ERROR
    # -----------------------------------------------------

    except Exception as e:

        # Delete failed upload
        if os.path.exists(filepath):

            try:
                os.remove(filepath)
            except OSError:
                pass


        return jsonify({
            "error": (
                f"Analysis failed: {str(e)}"
            )
        }), 500


    # =====================================================
    # SAVE SCAN TO DATABASE
    # =====================================================

    try:

        scan_id = db.create_scan(

            user_id=current_user.id,

            image_path=filepath.replace(
                "\\",
                "/"
            ),

            result=analysis["result"],

            confidence=analysis["confidence"],

            explanation=analysis["explanation"],

            details=analysis["details"]
        )

    except Exception as e:

        # If database saving fails,
        # remove uploaded image.

        if os.path.exists(filepath):

            try:
                os.remove(filepath)
            except OSError:
                pass


        return jsonify({
            "error": (
                f"Could not save scan report: {str(e)}"
            )
        }), 500


    # =====================================================
    # RETURN RESULT TO FRONTEND
    # =====================================================

    return jsonify({

        "scan_id": scan_id,

        "result": analysis["result"],

        "confidence": analysis["confidence"],

        "explanation": analysis["explanation"],

        "details": analysis["details"],

        "report_url": url_for(
            "report",
            scan_id=scan_id
        )

    })


# =========================================================
# MEDICAL HISTORY
# =========================================================

@app.route("/history")
@login_required
def history():

    status_filter = request.args.get(
        "status",
        "All"
    )

    scans = db.get_scans_by_user(
        current_user.id,
        status_filter
    )

    return render_template(
        "history.html",
        scans=scans,
        active_filter=status_filter
    )


# =========================================================
# FULL REPORT
# =========================================================

@app.route(
    "/report/<int:scan_id>"
)
@login_required
def report(scan_id):

    scan_row = db.get_scan_by_id(
        scan_id,
        current_user.id
    )

    # -----------------------------------------------------
    # Report not found
    # -----------------------------------------------------

    if not scan_row:

        flash(
            "Report not found.",
            "error"
        )

        return redirect(
            url_for("history")
        )


    # -----------------------------------------------------
    # Decode analysis details
    # -----------------------------------------------------

    try:

        details = (
            json.loads(
                scan_row["details"]
            )
            if scan_row["details"]
            else {}
        )

    except (
        json.JSONDecodeError,
        TypeError
    ):

        details = {}


    # -----------------------------------------------------
    # Render report
    # -----------------------------------------------------

    return render_template(
        "report.html",
        scan=scan_row,
        details=details
    )


# =========================================================
# PROFILE
# =========================================================

@app.route(
    "/profile",
    methods=["GET", "POST"]
)
@login_required
def profile():

    if request.method == "POST":

        db.update_profile(

            current_user.id,

            name=request.form.get(
                "name",
                current_user.name
            ),

            phone=request.form.get(
                "phone",
                ""
            ),

            gender=request.form.get(
                "gender",
                ""
            ),

            blood_group=request.form.get(
                "blood_group",
                ""
            ),

            existing_conditions=request.form.get(
                "existing_conditions",
                ""
            ),

            emergency_contact=request.form.get(
                "emergency_contact",
                ""
            )
        )


        flash(
            "Profile updated.",
            "success"
        )

        return redirect(
            url_for("profile")
        )


    # -----------------------------------------------------
    # Get latest profile information
    # -----------------------------------------------------

    user_row = db.get_user_by_id(
        current_user.id
    )


    return render_template(
        "profile.html",
        user=user_row
    )


# =========================================================
# SETTINGS
# =========================================================

@app.route(
    "/settings",
    methods=["GET", "POST"]
)
@login_required
def settings():

    if request.method == "POST":

        current_password = request.form.get(
            "current_password",
            ""
        )

        new_password = request.form.get(
            "new_password",
            ""
        )


        user_row = db.get_user_by_id(
            current_user.id
        )


        # -------------------------------------------------
        # Check current password
        # -------------------------------------------------

        if not check_password_hash(
            user_row["password_hash"],
            current_password
        ):

            flash(
                "Current password is incorrect.",
                "error"
            )


        # -------------------------------------------------
        # Check new password length
        # -------------------------------------------------

        elif len(new_password) < 6:

            flash(
                "New password must be at least 6 characters.",
                "error"
            )


        # -------------------------------------------------
        # Update password
        # -------------------------------------------------

        else:

            db.update_password(
                current_user.id,
                generate_password_hash(
                    new_password
                )
            )

            flash(
                "Password changed successfully.",
                "success"
            )


        return redirect(
            url_for("settings")
        )


    return render_template(
        "settings.html"
    )


# =========================================================
# RUN APP
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
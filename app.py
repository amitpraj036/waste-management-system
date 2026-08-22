import os
import secrets
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, session
from database import get_db_connection, init_db
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
def send_reset_email(recipient, reset_link):

    sender_email = os.environ.get("MAIL_EMAIL")
    sender_password = os.environ.get("MAIL_PASSWORD")

    if not sender_email or not sender_password:
        raise RuntimeError(
            "MAIL_EMAIL or MAIL_PASSWORD is not configured."
        )

    message = EmailMessage()

    message["Subject"] = "Waste Management - Password Reset"
    message["From"] = sender_email
    message["To"] = recipient

    message.set_content(
        f"""
Hello,

We received a request to reset your Waste Management account password.

Click the link below to reset your password:

{reset_link}

This link will expire in 30 minutes.

If you did not request a password reset, you can safely ignore this email.

Regards,
Waste Management System
"""
    )

    with smtplib.SMTP("smtp.gmail.com", 587) as server:

        server.starttls()

        server.login(
            sender_email,
            sender_password
        )

        server.send_message(message)

app = Flask(__name__)

app.secret_key = "waste-management-secret-key"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

init_db()


def admin_required():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("user_role") != "admin":
        return render_template("access_denied.html")

    return None


@app.route("/")
def home():

    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()

        try:

            conn.execute(
                """
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
                """,
                (name, email, hashed_password)
            )

            conn.commit()

        except Exception:

            conn.close()

            return "Email already registered!"

        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_role"] = user["role"]

            return redirect(url_for("home"))

        return "Invalid email or password!"

    return render_template("login.html")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form["email"]

        conn = get_db_connection()

        user = conn.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if user:

            reset_token = secrets.token_urlsafe(32)

            expiry = datetime.now() + timedelta(minutes=30)

            conn.execute(
                """
                UPDATE users
                SET
                    reset_token = ?,
                    reset_token_expiry = ?
                WHERE email = ?
                """,
                (
                    reset_token,
                    expiry,
                    email
                )
            )

            conn.commit()

            conn.close()

            return redirect(
                url_for(
                    "reset_password",
                    token=reset_token
                )
            )

        conn.close()

        return "No account found with this email."

    return render_template("forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    conn = get_db_connection()

    user = conn.execute(
        """
        SELECT id
        FROM users
        WHERE reset_token = ?
        AND reset_token_expiry > ?
        """,
        (
            token,
            datetime.now()
        )
    ).fetchone()

    if not user:
        conn.close()
        return "Invalid or expired reset link."

    if request.method == "POST":

        new_password = request.form.get("password", "")
        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if len(new_password) < 6:
            conn.close()
            return "Password must be at least 6 characters."

        if new_password != confirm_password:
            conn.close()
            return "Passwords do not match."

        hashed_password = generate_password_hash(
            new_password
        )

        conn.execute(
            """
            UPDATE users
            SET
                password = ?,
                reset_token = NULL,
                reset_token_expiry = NULL
            WHERE id = ?
            """,
            (
                hashed_password,
                user["id"]
            )
        )

        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    conn.close()

    return render_template(
        "reset_password.html",
        token=token
    )
    conn = get_db_connection()

    user = conn.execute(
        """
        SELECT id
        FROM users
        WHERE reset_token = ?
        AND reset_token_expiry > ?
        """,
        (
            token,
            datetime.now()
        )
    ).fetchone()

    if not user:

        conn.close()

        return "Invalid or expired reset link."

    if request.method == "POST":

        new_password = request.form["password"]

        hashed_password = generate_password_hash(
            new_password
        )

        conn.execute(
            """
            UPDATE users
            SET
                password = ?,
                reset_token = NULL,
                reset_token_expiry = NULL
            WHERE id = ?
            """,
            (
                hashed_password,
                user["id"]
            )
        )

        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    conn.close()

    return render_template(
        "reset_password.html",
        token=token
    )

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


@app.route("/report", methods=["GET", "POST"])
def report_waste():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        category = request.form["category"]
        location = request.form["location"]
        description = request.form["description"]

        user_id = session.get("user_id")

        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        image = request.files.get("image")

        image_filename = None

        if image and image.filename:

            image_filename = secure_filename(
                image.filename
            )

            image.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    image_filename
                )
            )

        conn = get_db_connection()

        conn.execute(
            """
            INSERT INTO waste_reports
            (
                category,
                description,
                location,
                image,
                latitude,
                longitude,
                user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                category,
                description,
                location,
                image_filename,
                latitude,
                longitude,
                user_id
            )
        )

        conn.commit()
        conn.close()

        return redirect(url_for("home"))

    return render_template("report_waste.html")


@app.route("/reports")
def reports():

    access = admin_required()

    if access:
        return access

    conn = get_db_connection()

    reports = conn.execute(
        """
        SELECT *
        FROM waste_reports
        ORDER BY created_at DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "reports.html",
        reports=reports
    )


@app.route("/my-reports")
def my_reports():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    reports = conn.execute(
        """
        SELECT *
        FROM waste_reports
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "my_reports.html",
        reports=reports
    )


@app.route("/notifications")
def notifications():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    notifications = conn.execute(
        """
        SELECT *
        FROM notifications
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "notifications.html",
        notifications=notifications
    )


@app.route(
    "/update-status/<int:report_id>",
    methods=["POST"]
)
def update_status(report_id):

    access = admin_required()

    if access:
        return access

    status = request.form["status"]

    allowed_statuses = [
        "Pending",
        "In Progress",
        "Collected"
    ]

    if status not in allowed_statuses:
        return redirect(url_for("reports"))

    conn = get_db_connection()

    report = conn.execute(
        """
        SELECT user_id
        FROM waste_reports
        WHERE id = ?
        """,
        (report_id,)
    ).fetchone()

    conn.execute(
        """
        UPDATE waste_reports
        SET status = ?
        WHERE id = ?
        """,
        (status, report_id)
    )

    if report and report["user_id"]:

        message = (
            f"Your waste report #{report_id} "
            f"status has been changed to {status}."
        )

        conn.execute(
            """
            INSERT INTO notifications
            (user_id, report_id, message)
            VALUES (?, ?, ?)
            """,
            (
                report["user_id"],
                report_id,
                message
            )
        )

    conn.commit()
    conn.close()

    return redirect(url_for("reports"))


@app.route("/dashboard")
def dashboard():

    access = admin_required()

    if access:
        return access

    conn = get_db_connection()

    total_reports = conn.execute(
        "SELECT COUNT(*) FROM waste_reports"
    ).fetchone()[0]

    pending_reports = conn.execute(
        """
        SELECT COUNT(*)
        FROM waste_reports
        WHERE status = 'Pending'
        """
    ).fetchone()[0]

    progress_reports = conn.execute(
        """
        SELECT COUNT(*)
        FROM waste_reports
        WHERE status = 'In Progress'
        """
    ).fetchone()[0]

    collected_reports = conn.execute(
        """
        SELECT COUNT(*)
        FROM waste_reports
        WHERE status = 'Collected'
        """
    ).fetchone()[0]

    category_data = conn.execute(
        """
        SELECT category, COUNT(*) as count
        FROM waste_reports
        GROUP BY category
        ORDER BY count DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_reports=total_reports,
        pending_reports=pending_reports,
        progress_reports=progress_reports,
        collected_reports=collected_reports,
        category_data=category_data
    )


@app.route("/map")
def waste_map():

    access = admin_required()

    if access:
        return access

    conn = get_db_connection()

    reports = conn.execute(
        """
        SELECT
            id,
            category,
            location,
            latitude,
            longitude,
            status
        FROM waste_reports
        WHERE latitude IS NOT NULL
        AND longitude IS NOT NULL
        ORDER BY created_at DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "map.html",
        reports=reports
    )


@app.route(
    "/schedule-collection/<int:report_id>",
    methods=["POST"]
)
def schedule_collection(report_id):

    access = admin_required()

    if access:
        return access

    collector_name = request.form["collector_name"]
    pickup_date = request.form["pickup_date"]
    pickup_time = request.form["pickup_time"]

    collection_notes = request.form.get(
        "collection_notes",
        ""
    )

    conn = get_db_connection()

    report = conn.execute(
        """
        SELECT user_id
        FROM waste_reports
        WHERE id = ?
        """,
        (report_id,)
    ).fetchone()

    conn.execute(
        """
        UPDATE waste_reports
        SET
            collector_name = ?,
            pickup_date = ?,
            pickup_time = ?,
            collection_notes = ?,
            status = 'In Progress'
        WHERE id = ?
        """,
        (
            collector_name,
            pickup_date,
            pickup_time,
            collection_notes,
            report_id
        )
    )

    if report and report["user_id"]:

        message = (
            f"Collection scheduled for your "
            f"waste report #{report_id}. "
            f"Collector: {collector_name}, "
            f"Date: {pickup_date}, "
            f"Time: {pickup_time}."
        )

        conn.execute(
            """
            INSERT INTO notifications
            (user_id, report_id, message)
            VALUES (?, ?, ?)
            """,
            (
                report["user_id"],
                report_id,
                message
            )
        )

    conn.commit()
    conn.close()

    return redirect(url_for("reports"))


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

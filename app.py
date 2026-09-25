"""
AI-Based Attendance System - Flask Backend
--------------------------------------------
Run with: python app.py
Requires WAMP running (Apache not required, only MySQL service) and the
'attendance_system' database imported from database.sql.
"""

import hashlib
from datetime import date, datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

from db_config import get_connection
from model.ai_model import predict_risk, predict_bulk, train_model

app = Flask(__name__)
app.secret_key = "change_this_secret_key_in_production"


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def get_attendance_percentage(student_id, conn=None):
    """Returns (present_count, total_count, percentage) for a student."""
    own_conn = conn is None
    if own_conn:
        conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT
            SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) AS present_count,
            COUNT(*) AS total_count
        FROM attendance WHERE student_id = %s
    """, (student_id,))
    row = cur.fetchone()
    cur.close()
    if own_conn:
        conn.close()

    present = row["present_count"] or 0
    total = row["total_count"] or 0
    percentage = round((present / total) * 100, 2) if total > 0 else 0.0
    return present, total, percentage


def get_absent_streak(student_id, conn):
    """Longest current consecutive absent streak (most recent backwards)."""
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT status FROM attendance
        WHERE student_id = %s ORDER BY attendance_date DESC
    """, (student_id,))
    rows = cur.fetchall()
    cur.close()
    streak = 0
    for r in rows:
        if r["status"] == "Absent":
            streak += 1
        else:
            break
    return streak


# ---------------------------------------------------------
# Auth Routes
# ---------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        hashed = hash_password(password)

        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (username, hashed))
        admin = cur.fetchone()
        cur.close()
        conn.close()

        if admin:
            session["admin_logged_in"] = True
            session["admin_username"] = admin["username"]
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) AS total_students FROM students")
    total_students = cur.fetchone()["total_students"]

    today = date.today().isoformat()
    cur.execute("""
        SELECT
            SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) AS present_today,
            SUM(CASE WHEN status='Absent' THEN 1 ELSE 0 END) AS absent_today
        FROM attendance WHERE attendance_date = %s
    """, (today,))
    today_stats = cur.fetchone()
    present_today = today_stats["present_today"] or 0
    absent_today = today_stats["absent_today"] or 0

    cur.execute("SELECT id, name, roll_no FROM students")
    students = cur.fetchall()
    cur.close()

    # Compute risk distribution using the AI model
    risk_counts = {"Good": 0, "Average": 0, "Shortage Risk": 0}
    bulk_input = []
    student_meta = []
    for s in students:
        present, total, pct = get_attendance_percentage(s["id"], conn)
        streak = get_absent_streak(s["id"], conn)
        bulk_input.append({
            "attendance_percentage": pct,
            "total_classes": total if total > 0 else 1,
            "absent_streak": streak
        })
        student_meta.append(s)

    if bulk_input:
        predictions = predict_bulk(bulk_input)
        for pred in predictions:
            risk_counts[pred] = risk_counts.get(pred, 0) + 1

    conn.close()

    return render_template(
        "dashboard.html",
        total_students=total_students,
        present_today=present_today,
        absent_today=absent_today,
        risk_counts=risk_counts,
        today=today
    )


# ---------------------------------------------------------
# Student CRUD
# ---------------------------------------------------------
@app.route("/students")
@login_required
def students():
    search = request.args.get("search", "").strip()
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    if search:
        like = f"%{search}%"
        cur.execute("""
            SELECT * FROM students
            WHERE name LIKE %s OR roll_no LIKE %s OR course LIKE %s
            ORDER BY id DESC
        """, (like, like, like))
    else:
        cur.execute("SELECT * FROM students ORDER BY id DESC")

    all_students = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("students.html", students=all_students, search=search)


@app.route("/students/add", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        roll_no = request.form.get("roll_no", "").strip()
        name = request.form.get("name", "").strip()
        course = request.form.get("course", "").strip()
        semester = request.form.get("semester", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        if not roll_no or not name:
            flash("Roll No and Name are required.", "danger")
            return redirect(url_for("add_student"))

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO students (roll_no, name, course, semester, email, phone)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (roll_no, name, course, semester, email, phone))
            conn.commit()
            flash("Student added successfully.", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Error: {e}", "danger")
        finally:
            cur.close()
            conn.close()
        return redirect(url_for("students"))

    return render_template("student_form.html", student=None)


@app.route("/students/edit/<int:student_id>", methods=["GET", "POST"])
@login_required
def edit_student(student_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        roll_no = request.form.get("roll_no", "").strip()
        name = request.form.get("name", "").strip()
        course = request.form.get("course", "").strip()
        semester = request.form.get("semester", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        cur.execute("""
            UPDATE students SET roll_no=%s, name=%s, course=%s, semester=%s, email=%s, phone=%s
            WHERE id=%s
        """, (roll_no, name, course, semester, email, phone, student_id))
        conn.commit()
        cur.close()
        conn.close()
        flash("Student updated successfully.", "success")
        return redirect(url_for("students"))

    cur.execute("SELECT * FROM students WHERE id=%s", (student_id,))
    student = cur.fetchone()
    cur.close()
    conn.close()

    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for("students"))

    return render_template("student_form.html", student=student)


@app.route("/students/delete/<int:student_id>", methods=["POST"])
@login_required
def delete_student(student_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE id=%s", (student_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Student deleted successfully.", "success")
    return redirect(url_for("students"))


# ---------------------------------------------------------
# Attendance Marking
# ---------------------------------------------------------
@app.route("/attendance/mark", methods=["GET", "POST"])
@login_required
def mark_attendance():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    selected_date = request.values.get("attendance_date", date.today().isoformat())

    if request.method == "POST":
        cur2 = conn.cursor()
        cur.execute("SELECT id FROM students")
        all_ids = [row["id"] for row in cur.fetchall()]

        for sid in all_ids:
            status = request.form.get(f"status_{sid}", "Absent")
            cur2.execute("""
                INSERT INTO attendance (student_id, attendance_date, status)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE status = VALUES(status)
            """, (sid, selected_date, status))
        conn.commit()
        cur2.close()
        cur.close()
        conn.close()
        flash(f"Attendance marked for {selected_date}.", "success")
        return redirect(url_for("mark_attendance", attendance_date=selected_date))

    cur.execute("SELECT * FROM students ORDER BY name")
    all_students = cur.fetchall()

    cur.execute("""
        SELECT student_id, status FROM attendance WHERE attendance_date=%s
    """, (selected_date,))
    existing = {row["student_id"]: row["status"] for row in cur.fetchall()}

    cur.close()
    conn.close()

    return render_template(
        "mark_attendance.html",
        students=all_students,
        existing=existing,
        selected_date=selected_date
    )


# ---------------------------------------------------------
# Attendance Reports (student-wise & date-wise)
# ---------------------------------------------------------
@app.route("/attendance/reports")
@login_required
def attendance_reports():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM students ORDER BY name")
    all_students = cur.fetchall()

    report_data = []
    for s in all_students:
        present, total, pct = get_attendance_percentage(s["id"], conn)
        streak = get_absent_streak(s["id"], conn)
        risk = predict_risk(pct, total if total > 0 else 1, streak)
        report_data.append({
            "id": s["id"],
            "roll_no": s["roll_no"],
            "name": s["name"],
            "course": s["course"],
            "present": present,
            "total": total,
            "percentage": pct,
            "risk": risk
        })

    cur.close()
    conn.close()

    return render_template("reports.html", report_data=report_data)


@app.route("/attendance/date-wise", methods=["GET"])
@login_required
def date_wise_report():
    selected_date = request.args.get("date", date.today().isoformat())

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT s.roll_no, s.name, s.course, a.status
        FROM students s
        LEFT JOIN attendance a
            ON s.id = a.student_id AND a.attendance_date = %s
        ORDER BY s.name
    """, (selected_date,))
    records = cur.fetchall()
    cur.close()
    conn.close()

    for r in records:
        if r["status"] is None:
            r["status"] = "Not Marked"

    return render_template("date_wise.html", records=records, selected_date=selected_date)


@app.route("/attendance/student/<int:student_id>")
@login_required
def student_wise_report(student_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM students WHERE id=%s", (student_id,))
    student = cur.fetchone()

    cur.execute("""
        SELECT attendance_date, status FROM attendance
        WHERE student_id=%s ORDER BY attendance_date DESC
    """, (student_id,))
    records = cur.fetchall()

    present, total, pct = get_attendance_percentage(student_id, conn)
    streak = get_absent_streak(student_id, conn)
    risk = predict_risk(pct, total if total > 0 else 1, streak)

    cur.close()
    conn.close()

    return render_template(
        "student_report.html",
        student=student,
        records=records,
        present=present,
        total=total,
        percentage=pct,
        risk=risk
    )


# ---------------------------------------------------------
# AI Analysis Page
# ---------------------------------------------------------
@app.route("/ai/analysis")
@login_required
def ai_analysis():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM students ORDER BY name")
    all_students = cur.fetchall()

    results = []
    for s in all_students:
        present, total, pct = get_attendance_percentage(s["id"], conn)
        streak = get_absent_streak(s["id"], conn)
        risk = predict_risk(pct, total if total > 0 else 1, streak)
        results.append({
            "roll_no": s["roll_no"],
            "name": s["name"],
            "percentage": pct,
            "absent_streak": streak,
            "risk": risk
        })

    cur.close()
    conn.close()

    return render_template("ai_analysis.html", results=results)


@app.route("/ai/retrain", methods=["POST"])
@login_required
def ai_retrain():
    train_model()
    flash("AI model retrained successfully.", "success")
    return redirect(url_for("ai_analysis"))


# ---------------------------------------------------------
# Run
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)

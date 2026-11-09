"""Teacher / admin portal (blueprint)."""

import csv
import io

from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash, Response
)

from helpers import get_db, teacher_required, now_str, award_badges
from model import predict_performance
from quiz_data import QUIZZES

teacher = Blueprint("teacher", __name__, url_prefix="/teacher")

AT_RISK_ATTENDANCE = 75


def _number(value, low, high, default=None):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default

    return number if low <= number <= high else default


# ----------------------------------------------------------------------
# Dashboard
# ----------------------------------------------------------------------

@teacher.route("/")
@teacher_required
def dashboard():
    connection = get_db()

    students = connection.execute(
        "SELECT * FROM students WHERE role = 'student' ORDER BY name"
    ).fetchall()

    counts = {"Good": 0, "Average": 0, "Needs Improvement": 0, "Not Predicted": 0}
    for s in students:
        counts[s["prediction"] if s["prediction"] in counts else "Not Predicted"] += 1

    at_risk = [
        s for s in students
        if s["prediction"] == "Needs Improvement"
        or (0 < (s["attendance"] or 0) < AT_RISK_ATTENDANCE)
    ]

    topic_stats = connection.execute(
        """
        SELECT topic, COUNT(*) AS attempts, AVG(percentage) AS avg
        FROM quiz_results GROUP BY topic ORDER BY avg ASC
        """
    ).fetchall()

    recent = connection.execute(
        """
        SELECT q.topic, q.score, q.total, q.percentage, q.created_at, s.name, s.id AS student_id
        FROM quiz_results q JOIN students s ON s.id = q.student_id
        ORDER BY q.id DESC LIMIT 8
        """
    ).fetchall()

    pending = connection.execute(
        "SELECT COUNT(*) FROM submissions WHERE marks IS NULL"
    ).fetchone()[0]

    n = len(students)

    summary = {
        "students": n,
        "avg_attendance": round(sum(s["attendance"] or 0 for s in students) / n, 1) if n else 0,
        "avg_quiz": round(sum(s["quiz_marks"] or 0 for s in students) / n, 1) if n else 0,
        "at_risk": len(at_risk),
        "pending": pending,
    }

    connection.close()

    return render_template(
        "teacher/dashboard.html",
        summary=summary,
        counts=counts,
        at_risk=at_risk,
        topic_stats=[dict(t) for t in topic_stats],
        recent=recent
    )


# ----------------------------------------------------------------------
# Students
# ----------------------------------------------------------------------

@teacher.route("/students")
@teacher_required
def students():
    search = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()

    query = "SELECT * FROM students WHERE role = 'student'"
    params = []

    if search:
        query += " AND (name LIKE ? OR email LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]

    if status:
        query += " AND prediction = ?"
        params.append(status)

    query += " ORDER BY name"

    connection = get_db()
    rows = connection.execute(query, params).fetchall()
    connection.close()

    return render_template("teacher/students.html", students=rows, search=search, status=status)


@teacher.route("/students/<int:student_id>", methods=["GET", "POST"])
@teacher_required
def student_detail(student_id):
    connection = get_db()

    student = connection.execute(
        "SELECT * FROM students WHERE id = ? AND role = 'student'", (student_id,)
    ).fetchone()

    if student is None:
        connection.close()
        flash("Student not found.")
        return redirect(url_for("teacher.students"))

    if request.method == "POST":
        previous = _number(request.form.get("previous_marks"), 0, 100)
        attendance = _number(request.form.get("attendance"), 0, 100)

        if previous is None or attendance is None:
            flash("Marks and attendance must be numbers between 0 and 100.")
        else:
            prediction = predict_performance(
                previous, student["assignment_marks"], student["quiz_marks"], attendance
            )
            connection.execute(
                """
                UPDATE students SET previous_marks = ?, attendance = ?, prediction = ?
                WHERE id = ?
                """,
                (previous, attendance, prediction, student_id)
            )
            connection.commit()
            flash(f"Updated. New predicted performance: {prediction}.", "success")

        connection.close()
        award_badges(student_id)
        return redirect(url_for("teacher.student_detail", student_id=student_id))

    quizzes = connection.execute(
        "SELECT * FROM quiz_results WHERE student_id = ? ORDER BY id DESC LIMIT 20",
        (student_id,)
    ).fetchall()

    topic_avgs = connection.execute(
        """
        SELECT topic, AVG(percentage) AS avg, COUNT(*) AS attempts
        FROM quiz_results WHERE student_id = ? GROUP BY topic ORDER BY avg
        """,
        (student_id,)
    ).fetchall()

    subs = connection.execute(
        """
        SELECT s.*, a.title, a.max_marks FROM submissions s
        JOIN assignments a ON a.id = s.assignment_id
        WHERE s.student_id = ? ORDER BY s.id DESC
        """,
        (student_id,)
    ).fetchall()

    connection.close()

    return render_template(
        "teacher/student_detail.html",
        student=student,
        quizzes=quizzes,
        topic_avgs=topic_avgs,
        submissions=subs
    )


@teacher.route("/students/export.csv")
@teacher_required
def export_students():
    connection = get_db()
    rows = connection.execute(
        "SELECT name, email, previous_marks, assignment_marks, quiz_marks, attendance, "
        "prediction, streak FROM students WHERE role = 'student' ORDER BY name"
    ).fetchall()
    connection.close()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Name", "Email", "Previous marks", "Assignment marks", "Quiz marks",
        "Attendance", "Predicted performance", "Streak (days)"
    ])

    for r in rows:
        # Prefix risky first characters so spreadsheets don't run them as formulas
        writer.writerow([
            ("'" + str(v)) if isinstance(v, str) and v and v[0] in "=+-@" else v
            for v in tuple(r)
        ])

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=students.csv"}
    )


# ----------------------------------------------------------------------
# Announcements
# ----------------------------------------------------------------------

@teacher.route("/announcements", methods=["GET", "POST"])
@teacher_required
def announcements():
    connection = get_db()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        message = request.form.get("message", "").strip()

        if not title or not message:
            flash("Title and message are required.")
        else:
            connection.execute(
                "INSERT INTO announcements (title, message, author_id, created_at) "
                "VALUES (?, ?, ?, ?)",
                (title[:120], message[:2000], session["user_id"], now_str())
            )
            connection.commit()
            flash("Announcement posted.", "success")

        connection.close()
        return redirect(url_for("teacher.announcements"))

    items = connection.execute("SELECT * FROM announcements ORDER BY id DESC").fetchall()
    connection.close()

    return render_template("teacher/announcements.html", announcements=items)


@teacher.route("/announcements/<int:item_id>/delete", methods=["POST"])
@teacher_required
def delete_announcement(item_id):
    connection = get_db()
    connection.execute("DELETE FROM announcements WHERE id = ?", (item_id,))
    connection.commit()
    connection.close()
    flash("Announcement deleted.", "success")
    return redirect(url_for("teacher.announcements"))


# ----------------------------------------------------------------------
# Learning materials
# ----------------------------------------------------------------------

MATERIAL_KINDS = ["Article", "Video", "Course", "Interactive", "PDF", "Other"]


@teacher.route("/materials", methods=["GET", "POST"])
@teacher_required
def materials():
    connection = get_db()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        topic = request.form.get("topic", "").strip()
        kind = request.form.get("kind", "Article")
        url = request.form.get("url", "").strip()
        description = request.form.get("description", "").strip()

        if not title or not topic or not url:
            flash("Title, topic and link are required.")
        elif not url.lower().startswith(("http://", "https://")):
            # blocks javascript: and other unsafe link types
            flash("The link must start with http:// or https://")
        else:
            connection.execute(
                "INSERT INTO materials (title, topic, kind, url, description, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (title[:150], topic[:60], kind if kind in MATERIAL_KINDS else "Other",
                 url[:500], description[:500], now_str())
            )
            connection.commit()
            flash("Material added.", "success")

        connection.close()
        return redirect(url_for("teacher.materials"))

    items = connection.execute("SELECT * FROM materials ORDER BY topic, id DESC").fetchall()
    connection.close()

    return render_template(
        "teacher/materials.html",
        materials=items,
        kinds=MATERIAL_KINDS,
        topics=sorted(QUIZZES.keys())
    )


@teacher.route("/materials/<int:item_id>/delete", methods=["POST"])
@teacher_required
def delete_material(item_id):
    connection = get_db()
    connection.execute("DELETE FROM materials WHERE id = ?", (item_id,))
    connection.commit()
    connection.close()
    flash("Material deleted.", "success")
    return redirect(url_for("teacher.materials"))


# ----------------------------------------------------------------------
# Assignments and grading
# ----------------------------------------------------------------------

@teacher.route("/assignments", methods=["GET", "POST"])
@teacher_required
def assignments():
    connection = get_db()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        topic = request.form.get("topic", "").strip()
        due_date = request.form.get("due_date", "").strip()
        max_marks = _number(request.form.get("max_marks"), 1, 1000, 100)

        if not title:
            flash("Title is required.")
        else:
            connection.execute(
                "INSERT INTO assignments (title, description, topic, due_date, max_marks, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (title[:150], description[:3000], topic[:60], due_date or None,
                 max_marks, now_str())
            )
            connection.commit()
            flash("Assignment created.", "success")

        connection.close()
        return redirect(url_for("teacher.assignments"))

    items = connection.execute(
        """
        SELECT a.*,
               COUNT(s.id) AS submitted,
               SUM(CASE WHEN s.marks IS NULL AND s.id IS NOT NULL THEN 1 ELSE 0 END) AS ungraded
        FROM assignments a LEFT JOIN submissions s ON s.assignment_id = a.id
        GROUP BY a.id ORDER BY a.id DESC
        """
    ).fetchall()
    connection.close()

    return render_template("teacher/assignments.html", assignments=items, topics=sorted(QUIZZES))


def _recalculate_assignment_marks(connection, student_id):
    """students.assignment_marks = average % over this student's graded work."""
    rows = connection.execute(
        """
        SELECT s.marks, a.max_marks FROM submissions s
        JOIN assignments a ON a.id = s.assignment_id
        WHERE s.student_id = ? AND s.marks IS NOT NULL
        """,
        (student_id,)
    ).fetchall()

    if not rows:
        return

    average = sum(r["marks"] / r["max_marks"] * 100 for r in rows) / len(rows)

    student = connection.execute(
        "SELECT previous_marks, quiz_marks, attendance FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()

    prediction = predict_performance(
        student["previous_marks"], average, student["quiz_marks"], student["attendance"]
    )

    connection.execute(
        "UPDATE students SET assignment_marks = ?, prediction = ? WHERE id = ?",
        (round(average, 2), prediction, student_id)
    )


@teacher.route("/assignments/<int:assignment_id>", methods=["GET", "POST"])
@teacher_required
def assignment_detail(assignment_id):
    connection = get_db()

    assignment = connection.execute(
        "SELECT * FROM assignments WHERE id = ?", (assignment_id,)
    ).fetchone()

    if assignment is None:
        connection.close()
        flash("Assignment not found.")
        return redirect(url_for("teacher.assignments"))

    if request.method == "POST":
        submission_id = request.form.get("submission_id", type=int)
        marks = _number(request.form.get("marks"), 0, assignment["max_marks"])
        feedback = request.form.get("feedback", "").strip()[:1000]

        submission = connection.execute(
            "SELECT * FROM submissions WHERE id = ? AND assignment_id = ?",
            (submission_id, assignment_id)
        ).fetchone()

        if submission is None:
            flash("Submission not found.")
        elif marks is None:
            flash(f"Marks must be a number between 0 and {assignment['max_marks']:g}.")
        else:
            connection.execute(
                "UPDATE submissions SET marks = ?, feedback = ? WHERE id = ?",
                (marks, feedback, submission_id)
            )
            _recalculate_assignment_marks(connection, submission["student_id"])
            connection.commit()
            award_badges(submission["student_id"])
            flash("Grade saved. The student's performance prediction was refreshed.", "success")

        connection.close()
        return redirect(url_for("teacher.assignment_detail", assignment_id=assignment_id))

    submissions = connection.execute(
        """
        SELECT s.*, st.name, st.email FROM submissions s
        JOIN students st ON st.id = s.student_id
        WHERE s.assignment_id = ? ORDER BY (s.marks IS NOT NULL), s.submitted_at
        """,
        (assignment_id,)
    ).fetchall()

    not_submitted = connection.execute(
        """
        SELECT name FROM students
        WHERE role = 'student'
          AND id NOT IN (SELECT student_id FROM submissions WHERE assignment_id = ?)
        ORDER BY name
        """,
        (assignment_id,)
    ).fetchall()

    connection.close()

    return render_template(
        "teacher/assignment_detail.html",
        assignment=assignment,
        submissions=submissions,
        not_submitted=not_submitted
    )


@teacher.route("/assignments/<int:assignment_id>/delete", methods=["POST"])
@teacher_required
def delete_assignment(assignment_id):
    connection = get_db()
    connection.execute("DELETE FROM submissions WHERE assignment_id = ?", (assignment_id,))
    connection.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
    connection.commit()
    connection.close()
    flash("Assignment deleted.", "success")
    return redirect(url_for("teacher.assignments"))

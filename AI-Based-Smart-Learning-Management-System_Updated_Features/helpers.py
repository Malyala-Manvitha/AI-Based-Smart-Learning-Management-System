"""Shared helpers: DB access, auth decorators, CSRF, gamification."""

import secrets
from datetime import datetime, timedelta
from functools import wraps

from flask import session, redirect, url_for, flash, request, abort

from database import get_connection

get_db = get_connection


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ----------------------------------------------------------------------
# Authentication
# ----------------------------------------------------------------------

def login_required(view):
    """Student pages. Teachers are sent to their own portal."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))

        if session.get("role") == "teacher":
            return redirect(url_for("teacher.dashboard"))

        return view(*args, **kwargs)

    return wrapper


def teacher_required(view):

    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))

        if session.get("role") != "teacher":
            flash("That page is only for teachers.")
            return redirect(url_for("dashboard"))

        return view(*args, **kwargs)

    return wrapper


# ----------------------------------------------------------------------
# CSRF protection (token stored in the session, checked on every POST)
# ----------------------------------------------------------------------

def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)

    return session["_csrf"]


def check_csrf():
    if request.method == "POST":
        sent = request.form.get("csrf_token", "")
        expected = session.get("_csrf", "")

        if not expected or not secrets.compare_digest(sent, expected):
            abort(400, "Invalid or missing CSRF token. Reload the page and try again.")


# ----------------------------------------------------------------------
# Gamification: streaks, XP, levels and badges
# ----------------------------------------------------------------------

BADGES = {
    "first_quiz": ("🚀", "First Steps", "Complete your first quiz."),
    "quiz_5": ("📚", "Quiz Warrior", "Complete 5 quizzes."),
    "quiz_20": ("🏆", "Quiz Master", "Complete 20 quizzes."),
    "perfect": ("💯", "Perfect Score", "Score 100% on a quiz."),
    "all_rounder": ("🌈", "All-Rounder", "Take quizzes in 3 different topics."),
    "streak_3": ("🔥", "On Fire", "Learn 3 days in a row."),
    "streak_7": ("⚡", "Unstoppable", "Learn 7 days in a row."),
    "attendance": ("📅", "Always Present", "Reach 90% attendance."),
    "first_submission": ("📝", "Submitted!", "Submit your first assignment."),
    "top_grade": ("⭐", "Top Grade", "Get 90%+ on a graded assignment."),
    "good_performer": ("🎯", "High Achiever", "Reach a 'Good' predicted performance."),
}


def touch_streak(student_id):
    """Call whenever the student does something meaningful (login / quiz)."""
    connection = get_db()
    row = connection.execute(
        "SELECT streak, last_active FROM students WHERE id = ?", (student_id,)
    ).fetchone()

    if row is None:
        connection.close()
        return

    today = datetime.now().date()
    last = None

    if row["last_active"]:
        try:
            last = datetime.strptime(row["last_active"], "%Y-%m-%d").date()
        except ValueError:
            last = None

    streak = row["streak"] or 0

    if last == today:
        connection.close()
        return

    streak = streak + 1 if last == today - timedelta(days=1) else 1

    connection.execute(
        "UPDATE students SET streak = ?, last_active = ? WHERE id = ?",
        (streak, today.strftime("%Y-%m-%d"), student_id)
    )
    connection.commit()
    connection.close()


def award_badges(student_id):
    """Evaluate every badge rule. Returns the list of newly earned badge keys."""
    connection = get_db()

    student = connection.execute(
        "SELECT * FROM students WHERE id = ?", (student_id,)
    ).fetchone()

    quizzes = connection.execute(
        "SELECT topic, percentage FROM quiz_results WHERE student_id = ?",
        (student_id,)
    ).fetchall()

    submissions = connection.execute(
        """
        SELECT s.marks, a.max_marks FROM submissions s
        JOIN assignments a ON a.id = s.assignment_id
        WHERE s.student_id = ?
        """,
        (student_id,)
    ).fetchall()

    earned = {
        r["badge_key"] for r in connection.execute(
            "SELECT badge_key FROM student_badges WHERE student_id = ?",
            (student_id,)
        )
    }

    topics = {q["topic"] for q in quizzes}
    streak = student["streak"] or 0

    checks = {
        "first_quiz": len(quizzes) >= 1,
        "quiz_5": len(quizzes) >= 5,
        "quiz_20": len(quizzes) >= 20,
        "perfect": any(q["percentage"] >= 100 for q in quizzes),
        "all_rounder": len(topics) >= 3,
        "streak_3": streak >= 3,
        "streak_7": streak >= 7,
        "attendance": (student["attendance"] or 0) >= 90,
        "first_submission": len(submissions) >= 1,
        "top_grade": any(
            s["marks"] is not None and s["max_marks"] and
            s["marks"] / s["max_marks"] >= 0.9
            for s in submissions
        ),
        "good_performer": student["prediction"] == "Good",
    }

    new = []

    for key, ok in checks.items():
        if ok and key not in earned:
            connection.execute(
                "INSERT OR IGNORE INTO student_badges (student_id, badge_key, earned_at) "
                "VALUES (?, ?, ?)",
                (student_id, key, now_str())
            )
            new.append(key)

    connection.commit()
    connection.close()

    return new


def xp_for(connection, student_id):
    """XP = 10 per correct quiz answer + 20 per submission + 50 per badge."""
    correct = connection.execute(
        "SELECT COALESCE(SUM(score), 0) FROM quiz_results WHERE student_id = ?",
        (student_id,)
    ).fetchone()[0]

    subs = connection.execute(
        "SELECT COUNT(*) FROM submissions WHERE student_id = ?", (student_id,)
    ).fetchone()[0]

    badges = connection.execute(
        "SELECT COUNT(*) FROM student_badges WHERE student_id = ?", (student_id,)
    ).fetchone()[0]

    return correct * 10 + subs * 20 + badges * 50


def level_for(xp):
    return xp // 100 + 1

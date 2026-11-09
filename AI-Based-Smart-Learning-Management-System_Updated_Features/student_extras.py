"""Additional student-facing features (blueprint)."""

from datetime import datetime

from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_weak_topics
from helpers import (
    get_db, login_required, now_str, touch_streak, award_badges,
    xp_for, level_for, BADGES
)
from quiz_data import QUIZZES

extras = Blueprint("extras", __name__)


# ----------------------------------------------------------------------
# Announcements
# ----------------------------------------------------------------------

@extras.route("/announcements")
@login_required
def announcements():
    connection = get_db()
    items = connection.execute(
        "SELECT * FROM announcements ORDER BY id DESC LIMIT 50"
    ).fetchall()
    connection.close()

    return render_template("announcements.html", announcements=items)


# ----------------------------------------------------------------------
# Learning materials
# ----------------------------------------------------------------------

@extras.route("/materials")
@login_required
def materials():
    topic = request.args.get("topic", "").strip()

    connection = get_db()

    if topic:
        items = connection.execute(
            "SELECT * FROM materials WHERE topic = ? ORDER BY id DESC", (topic,)
        ).fetchall()
    else:
        items = connection.execute(
            "SELECT * FROM materials ORDER BY topic, id DESC"
        ).fetchall()

    topics = [
        r["topic"] for r in connection.execute(
            "SELECT DISTINCT topic FROM materials ORDER BY topic"
        )
    ]
    connection.close()

    weak = {w["topic"] for w in get_weak_topics(session["user_id"])}

    return render_template(
        "materials.html",
        materials=items,
        topics=topics,
        selected=topic,
        weak_topics=weak
    )


# ----------------------------------------------------------------------
# Assignments
# ----------------------------------------------------------------------

def _is_overdue(due_date):
    if not due_date:
        return False

    try:
        return datetime.strptime(due_date, "%Y-%m-%d").date() < datetime.now().date()
    except ValueError:
        return False


@extras.route("/assignments")
@login_required
def assignments():
    connection = get_db()

    rows = connection.execute(
        """
        SELECT a.*, s.id AS submission_id, s.marks, s.submitted_at
        FROM assignments a
        LEFT JOIN submissions s
               ON s.assignment_id = a.id AND s.student_id = ?
        ORDER BY a.id DESC
        """,
        (session["user_id"],)
    ).fetchall()
    connection.close()

    items = [dict(r, overdue=_is_overdue(r["due_date"])) for r in rows]

    return render_template("assignments.html", assignments=items)


@extras.route("/assignments/<int:assignment_id>", methods=["GET", "POST"])
@login_required
def assignment_detail(assignment_id):
    connection = get_db()

    assignment = connection.execute(
        "SELECT * FROM assignments WHERE id = ?", (assignment_id,)
    ).fetchone()

    if assignment is None:
        connection.close()
        flash("Assignment not found.")
        return redirect(url_for("extras.assignments"))

    submission = connection.execute(
        "SELECT * FROM submissions WHERE assignment_id = ? AND student_id = ?",
        (assignment_id, session["user_id"])
    ).fetchone()

    if request.method == "POST":
        content = request.form.get("content", "").strip()

        if not content:
            flash("Please write your answer or paste a link to your work.")
        elif submission is not None and submission["marks"] is not None:
            flash("This submission has already been graded and can't be changed.")
        elif len(content) > 10000:
            flash("Submission is too long (max 10,000 characters).")
        else:
            connection.execute(
                """
                INSERT INTO submissions (assignment_id, student_id, content, submitted_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(assignment_id, student_id)
                DO UPDATE SET content = excluded.content,
                              submitted_at = excluded.submitted_at
                """,
                (assignment_id, session["user_id"], content, now_str())
            )
            connection.commit()
            connection.close()

            touch_streak(session["user_id"])
            new = award_badges(session["user_id"])

            flash("Assignment submitted successfully.", "success")
            for key in new:
                flash(f"New badge unlocked: {BADGES[key][0]} {BADGES[key][1]}", "success")

            return redirect(url_for("extras.assignment_detail", assignment_id=assignment_id))

    connection.close()

    return render_template(
        "assignment_detail.html",
        assignment=assignment,
        submission=submission,
        overdue=_is_overdue(assignment["due_date"])
    )


# ----------------------------------------------------------------------
# Achievements: XP, level, streak, badges, leaderboard
# ----------------------------------------------------------------------

@extras.route("/achievements")
@login_required
def achievements():
    connection = get_db()

    student = connection.execute(
        "SELECT * FROM students WHERE id = ?", (session["user_id"],)
    ).fetchone()

    earned_rows = connection.execute(
        "SELECT badge_key, earned_at FROM student_badges WHERE student_id = ?",
        (session["user_id"],)
    ).fetchall()
    earned = {r["badge_key"]: r["earned_at"] for r in earned_rows}

    students = connection.execute(
        "SELECT id, name FROM students WHERE role = 'student'"
    ).fetchall()

    board = []
    for s in students:
        xp = xp_for(connection, s["id"])
        board.append({"id": s["id"], "name": s["name"], "xp": xp, "level": level_for(xp)})

    connection.close()

    board.sort(key=lambda r: (-r["xp"], r["name"].lower()))

    for position, row in enumerate(board, start=1):
        row["rank"] = position

    mine = next((r for r in board if r["id"] == session["user_id"]), None)
    my_xp = mine["xp"] if mine else 0

    badges = [
        {"key": k, "icon": v[0], "name": v[1], "description": v[2],
         "earned_at": earned.get(k)}
        for k, v in BADGES.items()
    ]

    return render_template(
        "achievements.html",
        student=student,
        xp=my_xp,
        level=level_for(my_xp),
        xp_into_level=my_xp % 100,
        badges=badges,
        earned_count=len(earned),
        leaderboard=board[:10],
        my_rank=mine["rank"] if mine else None,
        total_students=len(board)
    )


# ----------------------------------------------------------------------
# Analytics
# ----------------------------------------------------------------------

@extras.route("/analytics")
@login_required
def analytics():
    connection = get_db()

    student = connection.execute(
        "SELECT * FROM students WHERE id = ?", (session["user_id"],)
    ).fetchone()

    results = connection.execute(
        """
        SELECT topic, score, total, percentage, created_at
        FROM quiz_results WHERE student_id = ? ORDER BY id ASC
        """,
        (session["user_id"],)
    ).fetchall()

    class_avg = connection.execute(
        """
        SELECT topic, AVG(percentage) AS avg
        FROM quiz_results GROUP BY topic
        """
    ).fetchall()
    connection.close()

    topic_scores = {}
    for r in results:
        topic_scores.setdefault(r["topic"], []).append(r["percentage"])

    topics = sorted(topic_scores)
    my_avg = [round(sum(topic_scores[t]) / len(topic_scores[t]), 1) for t in topics]
    class_lookup = {r["topic"]: round(r["avg"], 1) for r in class_avg}

    data = {
        "trend_labels": [r["created_at"][5:16] for r in results],
        "trend_values": [round(r["percentage"], 1) for r in results],
        "trend_topics": [r["topic"] for r in results],
        "topics": topics,
        "my_avg": my_avg,
        "class_avg": [class_lookup.get(t, 0) for t in topics],
        "components_labels": ["Previous marks", "Assignments", "Quizzes", "Attendance"],
        "components": [
            student["previous_marks"], student["assignment_marks"],
            student["quiz_marks"], student["attendance"]
        ],
    }

    best = max(zip(topics, my_avg), key=lambda x: x[1]) if topics else None
    worst = min(zip(topics, my_avg), key=lambda x: x[1]) if topics else None

    # Improvement: average of last 3 quizzes vs the 3 before
    values = data["trend_values"]
    change = None
    if len(values) >= 4:
        recent = values[-3:]
        earlier = values[-6:-3] or values[:-3]
        change = round(sum(recent) / len(recent) - sum(earlier) / len(earlier), 1)

    return render_template(
        "analytics.html",
        data=data,
        quiz_count=len(results),
        best=best,
        worst=worst,
        change=change
    )


# ----------------------------------------------------------------------
# Smart 7-day study plan
# ----------------------------------------------------------------------

def build_study_plan(student_id):
    connection = get_db()

    averages = {
        r["topic"]: r["avg"] for r in connection.execute(
            """
            SELECT topic, AVG(percentage) AS avg
            FROM quiz_results WHERE student_id = ? GROUP BY topic
            """,
            (student_id,)
        )
    }

    student = connection.execute(
        "SELECT attendance FROM students WHERE id = ?", (student_id,)
    ).fetchone()

    materials = {}
    for m in connection.execute("SELECT * FROM materials ORDER BY id"):
        materials.setdefault(m["topic"], []).append(m)

    connection.close()

    # Priority: weak -> untried -> medium -> strong
    def priority(topic):
        avg = averages.get(topic)
        if avg is None:
            return (1, 0)
        if avg < 60:
            return (0, avg)
        if avg < 80:
            return (2, avg)
        return (3, avg)

    ordered = sorted(QUIZZES.keys(), key=priority)

    def status(topic):
        avg = averages.get(topic)
        if avg is None:
            return "Not attempted yet"
        return f"Current average {avg:.0f}%"

    plan = []
    days = ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]

    for index in range(6):
        topic = ordered[index % len(ordered)]
        tasks = []

        library = materials.get(topic)
        if library:
            item = library[index // len(ordered) % len(library)]
            tasks.append({"icon": "📖", "text": f"Study: {item['title']}", "url": item["url"]})
        else:
            tasks.append({"icon": "📖", "text": f"Revise your notes on {topic}", "url": None})

        tasks.append({
            "icon": "🤖",
            "text": f"Ask the AI Tutor 2 questions about {topic}",
            "url": url_for("tutor")
        })
        tasks.append({
            "icon": "📝",
            "text": f"Take the {topic} quiz and aim for 80%+",
            "url": url_for("quiz", topic=topic)
        })

        plan.append({"day": days[index], "topic": topic, "status": status(topic), "tasks": tasks})

    review = [{
        "icon": "🔁",
        "text": "Retake the quiz for your weakest topic and compare your score",
        "url": url_for("quiz", topic=ordered[0])
    }]

    if (student["attendance"] or 0) < 75:
        review.append({
            "icon": "📅",
            "text": "Your attendance is below 75% - plan to attend every class next week",
            "url": url_for("attendance")
        })

    plan.append({"day": days[6], "topic": "Review & rest", "status": "Consolidate the week",
                 "tasks": review})

    return plan


@extras.route("/study-plan")
@login_required
def study_plan():
    return render_template("study_plan.html", plan=build_study_plan(session["user_id"]))


# ----------------------------------------------------------------------
# Profile
# ----------------------------------------------------------------------

@extras.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()
    user = connection.execute(
        "SELECT * FROM students WHERE id = ?", (session["user_id"],)
    ).fetchone()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "name":
            name = request.form.get("name", "").strip()

            if not name or len(name) > 60:
                flash("Please enter a name (max 60 characters).")
            else:
                connection.execute(
                    "UPDATE students SET name = ? WHERE id = ?",
                    (name, session["user_id"])
                )
                connection.commit()
                session["user_name"] = name
                flash("Name updated.", "success")

        elif action == "password":
            current = request.form.get("current_password", "")
            new = request.form.get("new_password", "")
            confirm = request.form.get("confirm_password", "")

            if not check_password_hash(user["password"], current):
                flash("Current password is incorrect.")
            elif len(new) < 6:
                flash("New password must be at least 6 characters.")
            elif new != confirm:
                flash("New passwords do not match.")
            else:
                connection.execute(
                    "UPDATE students SET password = ? WHERE id = ?",
                    (generate_password_hash(new), session["user_id"])
                )
                connection.commit()
                flash("Password changed.", "success")

        connection.close()
        return redirect(url_for("extras.profile"))

    connection.close()

    return render_template("profile.html", user=user)

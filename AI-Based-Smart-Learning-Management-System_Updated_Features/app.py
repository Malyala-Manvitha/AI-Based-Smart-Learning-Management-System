import os
import sqlite3
import random
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from model import (
    predict_performance,
    predict_with_details,
    train_model,
    MODEL_FOLDER,
    MODEL_PATH
)

from quiz_data import QUIZZES

from database import (
    init_database,
    get_connection,
    DATABASE_FOLDER,
    DATABASE_NAME as DATABASE_PATH
)

from helpers import (
    csrf_token,
    check_csrf,
    login_required,
    touch_streak,
    award_badges,
    xp_for,
    level_for,
    BADGES
)

from tutor import get_tutor_answer

from student_extras import extras
from teacher import teacher


# ==========================================================
# FLASK APPLICATION
# ==========================================================

app = Flask(__name__)

def _load_secret_key():
    """Use LMS_SECRET_KEY if set, otherwise create and reuse a random key file."""
    env_key = os.environ.get("LMS_SECRET_KEY")

    if env_key:
        return env_key

    os.makedirs("database", exist_ok=True)
    key_path = os.path.join("database", "secret.key")

    if not os.path.exists(key_path):
        with open(key_path, "w") as key_file:
            key_file.write(os.urandom(32).hex())

    with open(key_path) as key_file:
        return key_file.read().strip()


app.secret_key = _load_secret_key()

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=60 * 60 * 8
)

app.register_blueprint(extras)
app.register_blueprint(teacher)


STUDENT_ONLY = {
    "dashboard", "predict", "quiz", "submit_quiz", "attendance",
    "recommendations", "progress", "tutor"
}


@app.before_request
def _csrf_protect():
    check_csrf()

    if session.get("role") == "teacher" and request.endpoint in STUDENT_ONLY:
        return redirect(url_for("teacher.dashboard"))


@app.context_processor
def _template_globals():
    return {"csrf_token": csrf_token, "quiz_topics": list(QUIZZES.keys())}


# ==========================================================
# DATABASE (see database.py - tables are created / migrated on start)
# ==========================================================

def get_db():
    return get_connection()


# ==========================================================
# HOME PAGE
# ==========================================================

@app.route("/")
def home():

    if "user_id" in session:

        return redirect(
            url_for("dashboard")
        )

    return redirect(
        url_for("login")
    )


# ==========================================================
# REGISTER
# ==========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )


        # Check empty fields
        if not name or not email or not password:

            flash(
                "Please fill all fields."
            )

            return redirect(
                url_for("register")
            )


        if len(password) < 6:

            flash(
                "Password must be at least 6 characters."
            )

            return redirect(
                url_for("register")
            )


        connection = get_db()

        cursor = connection.cursor()


        # Check whether email already exists
        cursor.execute("""
            SELECT id
            FROM students
            WHERE lower(email) = ?
        """, (
            email,
        ))

        existing_user = cursor.fetchone()


        if existing_user:

            connection.close()

            flash(
                "Email already registered. Please login."
            )

            return redirect(
                url_for("login")
            )


        # Hash password
        hashed_password = generate_password_hash(
            password
        )


        # Insert student
        cursor.execute("""
            INSERT INTO students
            (
                name,
                email,
                password,
                created_at
            )

            VALUES (?, ?, ?, ?)
        """, (
            name,
            email,
            hashed_password,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))


        connection.commit()

        connection.close()


        flash(
            "Registration successful. Please login."
        )

        return redirect(
            url_for("login")
        )


    return render_template(
        "register.html"
    )


# ==========================================================
# LOGIN
# ==========================================================

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


        connection = get_db()

        cursor = connection.cursor()


        cursor.execute("""
            SELECT *
            FROM students
            WHERE lower(email) = ?
        """, (
            email,
        ))


        student = cursor.fetchone()

        connection.close()


        # Check login
        if student and check_password_hash(
            student["password"],
            password
        ):

            session.clear()

            session["user_id"] = student["id"]

            session["user_name"] = student["name"]

            session["role"] = student["role"] or "student"

            flash(
                "Login successful."
            )

            if session["role"] == "teacher":

                return redirect(
                    url_for("teacher.dashboard")
                )

            touch_streak(student["id"])

            award_badges(student["id"])

            return redirect(
                url_for("dashboard")
            )


        flash(
            "Invalid email or password."
        )


    return render_template(
        "login.html"
    )


# ==========================================================
# LOGOUT
# ==========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out."
    )

    return redirect(
        url_for("login")
    )


# ==========================================================
# DASHBOARD
# ==========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    connection = get_db()

    student = connection.execute(
        "SELECT * FROM students WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    recent_results = connection.execute("""
        SELECT * FROM quiz_results
        WHERE student_id = ?
        ORDER BY id DESC
        LIMIT 5
    """, (session["user_id"],)).fetchall()

    average_row = connection.execute(
        "SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?",
        (session["user_id"],)
    ).fetchone()

    average_quiz = round(average_row[0], 1) if average_row[0] is not None else 0

    latest_announcements = connection.execute(
        "SELECT * FROM announcements ORDER BY id DESC LIMIT 3"
    ).fetchall()

    open_assignments = connection.execute("""
        SELECT a.id, a.title, a.due_date
        FROM assignments a
        WHERE a.id NOT IN (
            SELECT assignment_id FROM submissions WHERE student_id = ?
        )
        ORDER BY (a.due_date IS NULL), a.due_date
        LIMIT 4
    """, (session["user_id"],)).fetchall()

    xp = xp_for(connection, session["user_id"])

    badge_count = connection.execute(
        "SELECT COUNT(*) FROM student_badges WHERE student_id = ?",
        (session["user_id"],)
    ).fetchone()[0]

    connection.close()

    weak_topics = get_weak_topics(
        session["user_id"]
    )

    recommendations = get_recommendations(
        student,
        weak_topics
    )

    return render_template(
        "dashboard.html",
        student=student,
        recent_results=recent_results,
        weak_topics=weak_topics,
        recommendations=recommendations,
        average_quiz=average_quiz,
        announcements=latest_announcements,
        open_assignments=open_assignments,
        xp=xp,
        level=level_for(xp),
        badge_count=badge_count
    )


# ==========================================================
# PERFORMANCE PREDICTION
# ==========================================================

@app.route(
    "/predict",
    methods=["GET", "POST"]
)
def predict():

    # Check login
    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    # ======================================================
    # POST - PREDICT PERFORMANCE
    # ======================================================

    if request.method == "POST":

        try:

            previous_marks = float(
                request.form.get(
                    "previous_marks",
                    0
                )
            )

            assignment_marks = float(
                request.form.get(
                    "assignment_marks",
                    0
                )
            )

            quiz_marks = float(
                request.form.get(
                    "quiz_marks",
                    0
                )
            )

            attendance = float(
                request.form.get(
                    "attendance",
                    0
                )
            )

        except ValueError:

            flash(
                "Please enter valid numbers."
            )

            return redirect(
                url_for("predict")
            )


        # Check range
        values = [
            previous_marks,
            assignment_marks,
            quiz_marks,
            attendance
        ]


        if any(
            value < 0 or value > 100
            for value in values
        ):

            flash(
                "All values must be between 0 and 100."
            )

            return redirect(
                url_for("predict")
            )


        # ==================================================
        # MACHINE LEARNING PREDICTION
        # ==================================================

        details = predict_with_details(previous_marks, assignment_marks, quiz_marks, attendance)

        prediction = details["label"]


        # ==================================================
        # SAVE DATA
        # ==================================================

        connection = get_db()

        cursor = connection.cursor()


        cursor.execute("""
            UPDATE students

            SET
                previous_marks = ?,

                assignment_marks = ?,

                quiz_marks = ?,

                attendance = ?,

                prediction = ?

            WHERE id = ?
        """, (

            previous_marks,

            assignment_marks,

            quiz_marks,

            attendance,

            prediction,

            session["user_id"]

        ))


        connection.commit()


        # ==================================================
        # GET UPDATED STUDENT
        # ==================================================

        cursor.execute("""
            SELECT *
            FROM students
            WHERE id = ?
        """, (
            session["user_id"],
        ))


        student = cursor.fetchone()


        connection.close()


        award_badges(session["user_id"])


        # ==================================================
        # DISPLAY RESULT
        # ==================================================

        return render_template(

            "predict.html",

            student=student,

            prediction=prediction,
            details=details,
            previous_marks=previous_marks,

            assignment_marks=assignment_marks,

            quiz_marks=quiz_marks,

            attendance=attendance

        )


    # ======================================================
    # GET - OPEN PREDICTION PAGE
    # ======================================================

    connection = get_db()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *
        FROM students
        WHERE id = ?
    """, (
        session["user_id"],
    ))


    student = cursor.fetchone()

    connection.close()


    return render_template(

        "predict.html",

        student=student

    )


# ==========================================================
# QUIZ PAGE
# ==========================================================

@app.route(
    "/quiz",
    methods=["GET"]
)
def quiz():

    # Check login
    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    topic = request.args.get(
        "topic"
    )


    # ======================================================
    # NO TOPIC SELECTED
    # ======================================================

    if not topic:

        return render_template(

            "quiz.html",

            questions=None,

            topic=None

        )


    # ======================================================
    # CHECK TOPIC
    # ======================================================

    if topic not in QUIZZES:

        flash(
            "Selected quiz topic is not available."
        )

        return redirect(
            url_for("quiz")
        )


    # ======================================================
    # GET QUESTIONS
    # ======================================================

    available_questions = QUIZZES[
        topic
    ]


    number_of_questions = min(
        5,
        len(available_questions)
    )


    questions = random.sample(

        available_questions,

        number_of_questions

    )


    # ======================================================
    # STORE QUESTIONS IN SESSION
    # ======================================================

    session["quiz_questions"] = questions

    session["quiz_topic"] = topic


    return render_template(

        "quiz.html",

        questions=questions,

        topic=topic

    )


# ==========================================================
# SUBMIT QUIZ
# ==========================================================

@app.route(
    "/quiz/submit",
    methods=["POST"]
)
@login_required
def submit_quiz():

    questions = session.get("quiz_questions", [])

    topic = session.get("quiz_topic", "")

    if not questions:

        flash("Please start the quiz first.")

        return redirect(url_for("quiz"))

    # ======================================================
    # CALCULATE SCORE AND BUILD ANSWER REVIEW
    # ======================================================

    score = 0

    review = []

    for index, question in enumerate(questions):

        selected = request.form.get(f"question_{index}")

        correct = question.get("answer")

        is_correct = selected == correct

        if is_correct:

            score += 1

        review.append({
            "question": question["question"],
            "selected": selected,
            "correct": correct,
            "is_correct": is_correct,
            "explanation": question.get("explanation", "")
        })

    total = len(questions)

    percentage = (score / total) * 100

    # ======================================================
    # SAVE RESULT AND UPDATE AVERAGE QUIZ MARK
    # ======================================================

    connection = get_db()

    connection.execute("""
        INSERT INTO quiz_results
        (student_id, topic, score, total, percentage, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        topic,
        score,
        total,
        percentage,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    average_quiz = connection.execute(
        "SELECT AVG(percentage) FROM quiz_results WHERE student_id = ?",
        (session["user_id"],)
    ).fetchone()[0]

    if average_quiz is None:

        average_quiz = percentage

    connection.execute(
        "UPDATE students SET quiz_marks = ? WHERE id = ?",
        (average_quiz, session["user_id"])
    )

    connection.commit()

    connection.close()

    session.pop("quiz_questions", None)

    session.pop("quiz_topic", None)

    # ======================================================
    # STREAK, BADGES
    # ======================================================

    touch_streak(session["user_id"])

    new_badges = [
        {"icon": BADGES[key][0], "name": BADGES[key][1]}
        for key in award_badges(session["user_id"])
    ]

    return render_template(
        "quiz_result.html",
        topic=topic,
        score=score,
        total=total,
        percentage=percentage,
        review=review,
        new_badges=new_badges,
        xp_gained=score * 10
    )


# ==========================================================
# ATTENDANCE
# ==========================================================

@app.route(
    "/attendance",
    methods=["GET", "POST"]
)
def attendance():

    # Check login
    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    # ======================================================
    # UPDATE ATTENDANCE
    # ======================================================

    if request.method == "POST":

        try:

            attendance_value = float(

                request.form.get(

                    "attendance",

                    0

                )

            )

        except ValueError:

            flash(
                "Please enter a valid attendance percentage."
            )

            return redirect(
                url_for("attendance")
            )


        if (
            attendance_value < 0
            or attendance_value > 100
        ):

            flash(
                "Attendance must be between 0 and 100."
            )

            return redirect(
                url_for("attendance")
            )


        connection = get_db()

        cursor = connection.cursor()


        cursor.execute("""
            UPDATE students

            SET attendance = ?

            WHERE id = ?
        """, (

            attendance_value,

            session["user_id"]

        ))


        connection.commit()

        connection.close()


        flash(
            "Attendance updated successfully."
        )


        return redirect(
            url_for("attendance")
        )


    # ======================================================
    # GET ATTENDANCE
    # ======================================================

    connection = get_db()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT attendance

        FROM students

        WHERE id = ?
    """, (
        session["user_id"],
    ))


    student = cursor.fetchone()

    connection.close()


    return render_template(

        "attendance.html",

        student=student

    )


# ==========================================================
# WEAK TOPIC DETECTION
# ==========================================================

def get_weak_topics(
    student_id
):

    connection = get_db()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT

            topic,

            AVG(percentage) AS average_score

        FROM quiz_results

        WHERE student_id = ?

        GROUP BY topic
    """, (
        student_id,
    ))


    results = cursor.fetchall()

    connection.close()


    weak_topics = []


    for result in results:

        if result["average_score"] < 60:

            weak_topics.append({

                "topic": result["topic"],

                "score": round(

                    result["average_score"],

                    2

                )

            })


    return weak_topics


# ==========================================================
# PERSONALIZED RECOMMENDATIONS
# ==========================================================

def get_recommendations(

    student,

    weak_topics

):

    recommendations = []


    if not student:

        return recommendations


    # ======================================================
    # ATTENDANCE RECOMMENDATION
    # ======================================================

    if student["attendance"] < 75:

        recommendations.append(

            "Improve your attendance. Try to maintain at least 75% attendance."

        )


    # ======================================================
    # PERFORMANCE RECOMMENDATION
    # ======================================================

    if student["prediction"] == "Needs Improvement":

        recommendations.append(

            "Your predicted performance needs improvement. Focus on weak topics and practice regularly."

        )


    elif student["prediction"] == "Average":

        recommendations.append(

            "Your performance is average. Revise important concepts and take more practice quizzes."

        )


    elif student["prediction"] == "Good":

        recommendations.append(

            "Your performance is good. Continue practicing and try advanced topics."

        )


    # ======================================================
    # WEAK TOPIC RECOMMENDATION
    # ======================================================

    for topic in weak_topics:

        recommendations.append(

            f"Focus more on {topic['topic']}. "
            f"Your average quiz score is {topic['score']}%."

        )


    # ======================================================
    # DEFAULT
    # ======================================================

    if not recommendations:

        recommendations.append(

            "Complete quizzes and update your academic information to receive personalized recommendations."

        )


    return recommendations


# ==========================================================
# RECOMMENDATIONS PAGE
# ==========================================================

@app.route(
    "/recommendations"
)
def recommendations():

    # Check login
    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    connection = get_db()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *

        FROM students

        WHERE id = ?
    """, (
        session["user_id"],
    ))


    student = cursor.fetchone()

    connection.close()


    weak_topics = get_weak_topics(

        session["user_id"]

    )


    recommendation_list = get_recommendations(

        student,

        weak_topics

    )


    return render_template(

        "recommendations.html",

        student=student,

        weak_topics=weak_topics,

        recommendations=recommendation_list

    )


# ==========================================================
# PROGRESS PAGE
# ==========================================================

@app.route(
    "/progress"
)
def progress():

    # Check login
    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    connection = get_db()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT

            topic,

            score,

            total,

            percentage,

            created_at

        FROM quiz_results

        WHERE student_id = ?

        ORDER BY id ASC
    """, (
        session["user_id"],
    ))


    results = cursor.fetchall()

    student = connection.execute(
        "SELECT * FROM students WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    connection.close()



    return render_template(

        "progress.html",

        student=student,

        results=results

    )


# ==========================================================
# AI TUTOR
# ==========================================================

@app.route(
    "/tutor",
    methods=["GET", "POST"]
)
@login_required
def tutor():

    result = None

    question = None

    connection = get_db()

    if request.method == "POST":

        question = request.form.get("question", "").strip()[:500]

        result = get_tutor_answer(question)

        if question:

            connection.execute("""
                INSERT INTO tutor_history
                (student_id, question, answer, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                session["user_id"],
                question,
                result["answer"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            connection.commit()

    history = connection.execute("""
        SELECT question, answer, created_at
        FROM tutor_history
        WHERE student_id = ?
        ORDER BY id DESC
        LIMIT 8
    """, (session["user_id"],)).fetchall()

    connection.close()

    return render_template(
        "tutor.html",
        result=result,
        question=question,
        history=history
    )


# ==========================================================
# ERROR PAGES
# ==========================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "error.html",
        code=404,
        message="The page you are looking for does not exist."
    ), 404


@app.errorhandler(400)
def bad_request(error):

    return render_template(
        "error.html",
        code=400,
        message=getattr(error, "description", "Bad request.")
    ), 400


@app.errorhandler(500)
def server_error(error):

    return render_template(
        "error.html",
        code=500,
        message="Something went wrong on our side. Please try again."
    ), 500


# ==========================================================
# START-UP (also runs when the app is imported, e.g. by tests)
# ==========================================================

def prepare_app():

    init_database()

    os.makedirs(MODEL_FOLDER, exist_ok=True)

    if not os.path.exists(MODEL_PATH):

        train_model()


prepare_app()


if __name__ == "__main__":

    print()
    print("==============================================")
    print(" AI-Based Smart Learning Management System")
    print("==============================================")
    print()
    print("Open: http://127.0.0.1:5000")
    print("Teacher login: teacher@lms.com / teacher123  (change it in Profile)")
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )

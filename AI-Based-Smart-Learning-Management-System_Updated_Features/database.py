"""
Database layer for the AI Smart LMS.

`init_database()` is safe to run on every start-up. It creates any missing
table and adds any missing column to an existing database, so students who
registered before the upgrade keep their data.
"""

import os
import sqlite3
from datetime import datetime

from werkzeug.security import generate_password_hash

DATABASE_FOLDER = "database"
DATABASE_NAME = os.path.join(DATABASE_FOLDER, "learning_system.db")

# Default teacher account (created once if no teacher exists).
# Change the password after the first login (Profile page) or override with
# the LMS_TEACHER_EMAIL / LMS_TEACHER_PASSWORD environment variables.
DEFAULT_TEACHER_EMAIL = os.environ.get("LMS_TEACHER_EMAIL", "teacher@lms.com")
DEFAULT_TEACHER_PASSWORD = os.environ.get("LMS_TEACHER_PASSWORD", "teacher123")


def get_connection():
    os.makedirs(DATABASE_FOLDER, exist_ok=True)

    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def _add_column_if_missing(cursor, table, column, definition):
    existing = [row[1] for row in cursor.execute(f"PRAGMA table_info({table})")]

    if column not in existing:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_database():
    connection = get_connection()
    cursor = connection.cursor()

    # ------------------------------------------------------------------
    # Core tables (same as the original project)
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            previous_marks REAL DEFAULT 0,
            assignment_marks REAL DEFAULT 0,
            quiz_marks REAL DEFAULT 0,
            attendance REAL DEFAULT 0,
            prediction TEXT DEFAULT 'Not Predicted'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            percentage REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    # ------------------------------------------------------------------
    # New columns on students (migration for existing databases)
    # ------------------------------------------------------------------
    _add_column_if_missing(cursor, "students", "role", "TEXT DEFAULT 'student'")
    _add_column_if_missing(cursor, "students", "created_at", "TEXT")
    _add_column_if_missing(cursor, "students", "streak", "INTEGER DEFAULT 0")
    _add_column_if_missing(cursor, "students", "last_active", "TEXT")

    cursor.execute("UPDATE students SET role = 'student' WHERE role IS NULL")

    # ------------------------------------------------------------------
    # New tables
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            author_id INTEGER,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            topic TEXT NOT NULL,
            kind TEXT NOT NULL DEFAULT 'Article',
            url TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            topic TEXT DEFAULT '',
            due_date TEXT,
            max_marks REAL NOT NULL DEFAULT 100,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            submitted_at TEXT NOT NULL,
            marks REAL,
            feedback TEXT DEFAULT '',
            UNIQUE(assignment_id, student_id),
            FOREIGN KEY(assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            badge_key TEXT NOT NULL,
            earned_at TEXT NOT NULL,
            UNIQUE(student_id, badge_key),
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tutor_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    _seed_teacher(cursor)
    _seed_materials(cursor)

    connection.commit()
    connection.close()


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _seed_teacher(cursor):
    has_teacher = cursor.execute(
        "SELECT 1 FROM students WHERE role = 'teacher' LIMIT 1"
    ).fetchone()

    if has_teacher:
        return

    existing = cursor.execute(
        "SELECT id FROM students WHERE email = ?",
        (DEFAULT_TEACHER_EMAIL,)
    ).fetchone()

    if existing:
        cursor.execute(
            "UPDATE students SET role = 'teacher' WHERE id = ?",
            (existing["id"],)
        )
        return

    cursor.execute(
        """
        INSERT INTO students (name, email, password, role, created_at)
        VALUES (?, ?, ?, 'teacher', ?)
        """,
        (
            "Teacher",
            DEFAULT_TEACHER_EMAIL,
            generate_password_hash(DEFAULT_TEACHER_PASSWORD),
            _now()
        )
    )


STARTER_MATERIALS = [
    ("Python Official Tutorial", "Python", "Article",
     "https://docs.python.org/3/tutorial/",
     "Step-by-step introduction to Python from the official docs."),
    ("Python for Everybody (freeCodeCamp)", "Python", "Video",
     "https://www.youtube.com/results?search_query=python+for+everybody+freecodecamp",
     "Full beginner course on YouTube."),
    ("Machine Learning Crash Course", "Machine Learning", "Course",
     "https://developers.google.com/machine-learning/crash-course",
     "Google's free, practical introduction to machine learning."),
    ("scikit-learn User Guide", "Machine Learning", "Article",
     "https://scikit-learn.org/stable/user_guide.html",
     "Reference for the algorithms used in this project."),
    ("SQLBolt Interactive Lessons", "SQL", "Interactive",
     "https://sqlbolt.com/",
     "Learn SQL with short interactive exercises."),
    ("W3Schools SQL Tutorial", "SQL", "Article",
     "https://www.w3schools.com/sql/",
     "Quick SQL reference with an in-browser editor."),
    ("MDN HTML Basics", "HTML", "Article",
     "https://developer.mozilla.org/en-US/docs/Learn/Getting_started_with_the_web/HTML_basics",
     "Mozilla's beginner guide to HTML."),
    ("MDN CSS First Steps", "CSS", "Article",
     "https://developer.mozilla.org/en-US/docs/Learn/CSS/First_steps",
     "Learn how CSS styles a web page."),
    ("MDN JavaScript Guide", "JavaScript", "Article",
     "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
     "The complete JavaScript guide from MDN."),
    ("Visualgo - Data Structures", "Data Structures", "Interactive",
     "https://visualgo.net/en",
     "Animated visualisations of common data structures and algorithms."),
]


def _seed_materials(cursor):
    count = cursor.execute("SELECT COUNT(*) FROM materials").fetchone()[0]

    if count:
        return

    for title, topic, kind, url, description in STARTER_MATERIALS:
        cursor.execute(
            """
            INSERT INTO materials (title, topic, kind, url, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, topic, kind, url, description, _now())
        )


# ----------------------------------------------------------------------
# Small query helpers kept from the original module
# ----------------------------------------------------------------------

def get_student(student_id):
    connection = get_connection()

    student = connection.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()

    connection.close()

    return student


def get_quiz_results(student_id):
    connection = get_connection()

    results = connection.execute(
        """
        SELECT *
        FROM quiz_results
        WHERE student_id = ?
        ORDER BY created_at DESC
        """,
        (student_id,)
    ).fetchall()

    connection.close()

    return results


def get_weak_topics(student_id, threshold=60):
    connection = get_connection()

    topics = connection.execute(
        """
        SELECT topic, AVG(percentage) AS average_score
        FROM quiz_results
        WHERE student_id = ?
        GROUP BY topic
        """,
        (student_id,)
    ).fetchall()

    connection.close()

    return [
        {"topic": t["topic"], "score": round(t["average_score"], 2)}
        for t in topics
        if t["average_score"] < threshold
    ]

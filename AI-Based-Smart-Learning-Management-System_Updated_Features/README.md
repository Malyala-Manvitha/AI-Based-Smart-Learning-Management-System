# AI-Based Smart Learning Management System

## Project Description

The AI-Based Smart Learning Management System is a web-based application designed to help students improve their academic performance using Artificial Intelligence and Machine Learning.

## Main Features

### Student
1. Registration, login, profile (change name / password)
2. Dashboard with XP, level, streak, announcements and open assignments
3. Performance prediction (Decision Tree) with confidence, weighted score and "what to improve first"
4. Topic quizzes (Python, Machine Learning, SQL, HTML, JavaScript, CSS, Data Structures) with a countdown timer and a full answer review with explanations
5. AI Tutor (TF-IDF + cosine similarity, 45 Q&A entries) with related questions, quiz / material shortcuts and chat history
6. Weak topic detection and personalised recommendations
7. Smart 7-day study plan built from your weak / untried topics
8. Learning materials library (weak topics highlighted)
9. Assignments: submit work, see grade and teacher feedback
10. Analytics charts: score trend, topic average vs class, academic profile
11. Achievements: XP, levels, learning streaks, 11 badges, class leaderboard
12. Attendance and progress tracking

### Teacher (new)
- Class overview: averages, performance distribution chart, topic difficulty chart, at-risk students
- Student list with search / filter, per-student detail, edit marks and attendance (prediction refreshes)
- Create assignments, grade submissions with feedback (updates the student's assignment marks and prediction)
- Post announcements, add / remove learning materials
- Export all students to CSV

### Security and quality
- CSRF protection on every form, hashed passwords, session cookie hardening
- Random secret key generated on first run (or set `LMS_SECRET_KEY`)
- Role-based access (students cannot open teacher pages)
- Database migrates automatically: existing students and quiz results are kept
- Fixed: Progress page crash, dashboard quiz average, hidden navigation bar

## Technologies Used

### Frontend
- HTML
- CSS
- JavaScript

### Backend
- Python
- Flask

### Database
- SQLite

### Machine Learning
- Scikit-learn
- Decision Tree

### NLP
- TF-IDF
- Cosine Similarity

## How to Run

Install dependencies:

    pip install -r requirements.txt

Run the application:

    python app.py

Open the browser:

    http://127.0.0.1:5000

### Teacher login

A teacher account is created automatically the first time the app starts:

    Email:    teacher@lms.com
    Password: teacher123

Change the password on the Profile page right after your first login (or set the
`LMS_TEACHER_EMAIL` and `LMS_TEACHER_PASSWORD` environment variables before the first run).
Students register themselves on the Register page.

## Project Structure

    app.py              Flask app, student core routes (auth, quiz, predict, tutor...)
    student_extras.py   Materials, assignments, achievements, analytics, study plan, profile
    teacher.py          Teacher portal
    helpers.py          Login / CSRF helpers, XP, streaks and badge rules
    database.py         Schema + automatic migration + starter data
    model.py            Decision Tree training and prediction details
    tutor.py            AI tutor knowledge base and TF-IDF matching
    quiz_data.py        Quiz questions (add topics here)
    templates/          HTML pages (templates/teacher for the teacher portal)
    static/             CSS and JavaScript (charts.js is a small offline chart library)

## Future Enhancements

- Email notifications for announcements and grades
- Automatic AI quiz generation
- Connect the tutor to a large language model
- File uploads for assignments
- Mobile application

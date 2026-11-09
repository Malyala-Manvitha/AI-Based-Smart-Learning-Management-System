🎓 AI-Based Smart Learning Management System
# 🎓 AI-Based Smart Learning Management System

An AI-powered web platform that helps students understand where they are weak, predicts their performance, and answers their doubts in simple words, while giving teachers a clear view of the whole class.

Department of Computer Science and Engineering · Chaitanya Deemed to be University, Hyderabad

📌 Overview

Most learning platforms store marks but do not tell students why they are struggling. This project combines a Learning Management System with Machine Learning and Natural Language Processing so that the platform:

predicts a student’s performance (Good / Average / Needs Improvement),
finds weak topics from quiz results and builds a 7-day study plan,
answers doubts through an offline AI Tutor and an Ask AI assistant,
keeps students motivated with XP, levels, streaks and badges,
gives teachers at-risk student detection, grading and class analytics.
✨ Features
👩‍🎓 Student portal
Feature	Description
Registration & login	Hashed passwords, session-based login, profile page
Dashboard	Marks, attendance, prediction, weak topics, XP, level, streak
Quizzes	7 topics (Python, Machine Learning, SQL, HTML, JavaScript, CSS, Data Structures) with instant score and answer review
Performance prediction	Decision Tree with confidence, weighted score and “what to improve first”
Weak topics & recommendations	Topics with average score below 60% are flagged with advice
7-day study plan	Weakest topics first, with study links and quiz goals
AI Tutor	TF-IDF + cosine similarity over 46 Q&A entries (works offline)
Ask AI	ChatGPT-style assistant using a free Gemini / Groq key, with automatic offline fallback
Analytics	Score trend, topic average vs class average, academic profile charts
Achievements	XP, levels, streaks, 11 badges, top-10 leaderboard
Assignments & materials	Submit work, receive marks and feedback, browse learning links
Attendance	Tracking with a warning below 75%
👨‍🏫 Teacher portal
Class overview: averages, performance distribution and topic difficulty charts
At-risk students (predicted Needs Improvement or attendance below 75%)
Student search / filter, detail pages, edit marks and attendance
Create assignments and grade submissions (updates marks and prediction automatically)
Post announcements and add learning materials
Export students to CSV
🏗️ System Architecture
 Browser (HTML · CSS · JavaScript, offline SVG charts)
                 │
                 ▼
 Flask backend ── authentication · sessions · CSRF · role checks
   │        │          │            │             │
   ▼        ▼          ▼            ▼             ▼
 Quiz &   ML model   AI Tutor    Ask AI       Teacher portal
 weak     (Decision  (TF-IDF)    (Gemini /    (grading, at-risk,
 topics    Tree)                  Groq / offline) CSV export)
   └────────┴──────────┴────────────┴─────────────┘
                 │
                 ▼
          SQLite database
🧠 How the AI works

1. Performance prediction (model.py)

Inputs: previous marks (30%), assignment marks (25%), quiz marks (25%), attendance (20%).
Algorithm: DecisionTreeClassifier (max_depth=5, min_samples_leaf=8) trained on 800 synthetic student records.
Output: label, confidence, weighted score and the area to improve first.
⚠️ The model is trained on synthetic data that follows a weighted rule. It demonstrates the approach; accuracy on real students can only be measured once real records are available.

2. Weak topic detection: quiz results are averaged per topic; an average below 60% marks the topic as weak.

3. AI Tutor (tutor.py): questions and answers are vectorised with TF-IDF (unigrams + bigrams) and the best match is chosen by cosine similarity.

4. Ask AI (ai_chat.py): sends the question to Google Gemini, Groq or Anthropic when a key is present, with retry, fallback models and a rate limit (30 questions per student per hour). Without a key it answers from the offline tutor, so it never just fails.

🛠️ Tech Stack
Layer	Technology
Frontend	HTML, CSS, JavaScript (custom offline chart library)
Backend	Python, Flask
Database	SQLite
Machine Learning	scikit-learn (Decision Tree), NumPy
NLP	TF-IDF, cosine similarity
Generative AI (optional)	Google Gemini, Groq or Anthropic API
🚀 Getting Started
Prerequisites
Python 3.9 or newer
pip
Installation
bash
# 1. Clone the repository
git clone https://github.com/Malyala-Manvitha/AI-Based-Smart-Learning-Management-System.git
cd AI-Based-Smart-Learning-Management-System

# 2. (Optional) create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py

Open http://127.0.0.1:5000 in your browser. On Windows you can also double-click run.bat.

The database and ML model are created automatically on first run.

Teacher login

A teacher account is created on first start:

Email:    teacher@lms.com
Password: teacher123

Change this password from the Profile page after your first login, or set LMS_TEACHER_EMAIL and LMS_TEACHER_PASSWORD before the first run. Students register themselves on the Register page.

🔑 Enable Ask AI with a free key (optional)

Without a key, Ask AI runs in offline mode. To answer any question:

Get a free key from Google AI Studio (Gemini) or Groq Console.
Copy .env.example to a new file named .env.
Paste the key after the matching name, with no spaces or quotes (e.g. GEMINI_API_KEY=your_key_here).
Restart python app.py. The Ask AI page shows “Online AI is on”.

🔒 Never commit your .env file. It is already listed in .gitignore.

🔐 Security
Passwords stored as hashes (Werkzeug)
CSRF token required on every POST form
Role-based access (students cannot open teacher pages)
Parameterised SQL queries
Random secret key generated on first run (or set LMS_SECRET_KEY)
Per-student hourly rate limit on Ask AI
Database migrates automatically, so existing data is kept

📁 Project Structure
├── app.py               Core routes: auth, dashboard, quiz, predict, tutor
├── ai_chat.py           Ask AI (Gemini / Groq / Anthropic + offline fallback)
├── student_extras.py    Materials, assignments, achievements, analytics, study plan, profile
├── teacher.py           Teacher portal
├── helpers.py           Login / CSRF helpers, XP, streaks, badge rules
├── database.py          Schema, auto-migration, starter data
├── model.py             Decision Tree training and prediction
├── tutor.py             TF-IDF AI Tutor
├── quiz_data.py         Quiz questions (add new topics here)
├── ml_models/           Saved model (performance_model.pkl)
├── templates/           HTML pages (templates/teacher for the teacher portal)
├── static/              CSS and JavaScript
├── requirements.txt
├── .env.example         Template for the free API key
└── run.bat              One-click start on Windows
🔭 Future Scope
Train the prediction model on real historical records and report evaluation metrics
Teacher-created quizzes and question-bank upload
Answers from uploaded course notes (retrieval-augmented generation)
Email / app notifications for deadlines and low attendance
File uploads for assignments
Mobile application and production deployment (PostgreSQL / MySQL)


⭐ If you found this project useful, consider giving it a star.

"""AI tutor: TF-IDF + cosine similarity over a question/answer knowledge base."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# (question, answer, topic used to suggest learning materials / quizzes)
KNOWLEDGE = [
    ("What is Python?", "Python is a high-level programming language known for its simple syntax and wide use in web development, data science, AI and automation.", "Python"),
    ("What is a variable in Python?", "A variable is a name that refers to a value stored in memory, e.g. age = 20. Python figures out the type automatically (dynamic typing).", "Python"),
    ("What is a list in Python?", "A list is an ordered, changeable collection written with square brackets, e.g. [1, 2, 3]. You can add, remove and change items.", "Python"),
    ("What is the difference between a list and a tuple?", "Lists are mutable (can be changed) and use [ ]. Tuples are immutable (cannot be changed after creation) and use ( ). Tuples are slightly faster and can be used as dictionary keys.", "Python"),
    ("What is a dictionary in Python?", "A dictionary stores key-value pairs, e.g. {'name': 'Asha', 'age': 20}. Values are looked up quickly by their key.", "Python"),
    ("What is a function?", "A function is a reusable block of code that runs when called. In Python it is defined with the def keyword and can take parameters and return a value.", "Python"),
    ("What is object oriented programming OOP?", "OOP organises code into classes and objects. Its four pillars are encapsulation, inheritance, polymorphism and abstraction.", "Python"),
    ("What is a class and an object?", "A class is a blueprint that defines attributes and methods. An object is an instance created from that class.", "Python"),
    ("What is a loop?", "A loop repeats code. Python has for loops (iterate over a sequence) and while loops (repeat while a condition is true).", "Python"),
    ("What is recursion?", "Recursion is when a function calls itself to solve a smaller version of the same problem. It needs a base case to stop.", "Data Structures"),
    ("What is Machine Learning?", "Machine Learning is a branch of AI where computers learn patterns from data and use them to make predictions or decisions without being explicitly programmed.", "Machine Learning"),
    ("What is supervised learning?", "Supervised learning trains a model on labelled data (inputs with known answers). Examples: classification and regression.", "Machine Learning"),
    ("What is unsupervised learning?", "Unsupervised learning finds hidden patterns or groups in unlabelled data. Clustering (e.g. k-means) is a common example.", "Machine Learning"),
    ("What is a decision tree?", "A decision tree is a supervised algorithm that predicts by asking a series of yes/no questions about the features, splitting the data at each node. This project uses one to predict student performance.", "Machine Learning"),
    ("What is overfitting?", "Overfitting happens when a model memorises the training data, noise included, so it performs well on training data but badly on new data. Fix it with more data, simpler models or regularisation.", "Machine Learning"),
    ("What is a neural network?", "A neural network is a model made of layers of connected nodes (neurons) that learn weights from data. Deep learning uses networks with many layers.", "Machine Learning"),
    ("What is classification and regression?", "Classification predicts a category (e.g. Good / Average). Regression predicts a number (e.g. a house price).", "Machine Learning"),
    ("What is TF-IDF?", "TF-IDF scores how important a word is to a document: frequent in that document but rare across all documents. This tutor uses it with cosine similarity to match your question to answers.", "Machine Learning"),
    ("What is Artificial Intelligence?", "Artificial Intelligence is the field of computer science focused on building systems that perform tasks normally requiring human intelligence, such as understanding language or recognising images.", "Machine Learning"),
    ("What is data science?", "Data Science combines statistics, programming and domain knowledge to extract insight from data.", "Machine Learning"),
    ("What is SQL?", "SQL (Structured Query Language) is used to create, read, update and delete data in relational databases.", "SQL"),
    ("What is a primary key?", "A primary key uniquely identifies each row in a table. It cannot be NULL or duplicated.", "SQL"),
    ("What is a foreign key?", "A foreign key is a column that references the primary key of another table, linking the two tables together.", "SQL"),
    ("What is a JOIN in SQL?", "A JOIN combines rows from two tables using a related column. Types: INNER, LEFT, RIGHT and FULL JOIN.", "SQL"),
    ("What is the difference between WHERE and HAVING?", "WHERE filters rows before grouping; HAVING filters groups after GROUP BY (usually on aggregates like COUNT or AVG).", "SQL"),
    ("What is a database?", "A database is an organised collection of data that can be stored, managed and retrieved efficiently.", "SQL"),
    ("What is normalization?", "Normalization organises a database to reduce redundancy and improve integrity by splitting data into related tables (1NF, 2NF, 3NF).", "SQL"),
    ("What is HTML?", "HTML (HyperText Markup Language) defines the structure of web pages using elements such as headings, paragraphs, links and forms.", "HTML"),
    ("What is the difference between div and span?", "div is a block-level container that starts on a new line; span is an inline container used for small pieces of text inside a line.", "HTML"),
    ("What is CSS?", "CSS (Cascading Style Sheets) styles HTML: colours, fonts, spacing and layout.", "CSS"),
    ("What is the CSS box model?", "Every element is a box made of content, padding, border and margin, from the inside out.", "CSS"),
    ("What is flexbox?", "Flexbox is a CSS layout system for arranging items in a row or column with easy alignment, spacing and wrapping (display: flex).", "CSS"),
    ("What is JavaScript?", "JavaScript is the programming language of the web. It makes pages interactive by responding to clicks, updating content and talking to servers.", "JavaScript"),
    ("What is the difference between let, const and var?", "var is function-scoped and old. let is block-scoped and reassignable. const is block-scoped and cannot be reassigned. Prefer const, then let.", "JavaScript"),
    ("What is a promise and async await?", "A Promise represents a value that will arrive later. async/await lets you write asynchronous code that reads like normal sequential code.", "JavaScript"),
    ("What is the DOM?", "The DOM (Document Object Model) is a tree representation of a web page that JavaScript can read and change.", "JavaScript"),
    ("What is Flask?", "Flask is a lightweight Python web framework for building web apps and APIs. This LMS is built with it.", "Python"),
    ("What is an API and REST?", "An API lets programs talk to each other. A REST API uses HTTP methods (GET, POST, PUT, DELETE) on URLs to work with resources, usually returning JSON.", "Python"),
    ("What is Git and GitHub?", "Git is a version-control system that tracks changes to code. GitHub is a website that hosts Git repositories for collaboration.", "Python"),
    ("What is an algorithm?", "An algorithm is a step-by-step procedure for solving a problem.", "Data Structures"),
    ("What is a stack and a queue?", "A stack is Last-In-First-Out (LIFO), like a pile of plates. A queue is First-In-First-Out (FIFO), like a line at a ticket counter.", "Data Structures"),
    ("What is a linked list?", "A linked list is a chain of nodes where each node stores a value and a pointer to the next node. Insertion is fast but random access is slow.", "Data Structures"),
    ("What is Big O notation time complexity?", "Big O describes how an algorithm's running time grows with input size n. Examples: O(1) constant, O(log n) binary search, O(n) loop, O(n^2) nested loops.", "Data Structures"),
    ("What is binary search?", "Binary search finds an item in a sorted list by repeatedly halving the search range. It runs in O(log n) time.", "Data Structures"),
    ("What is a hash table?", "A hash table maps keys to values using a hash function for O(1) average lookups. Python dictionaries are hash tables.", "Data Structures"),
    ("What is a tree and a binary tree?", "A tree is a hierarchical structure of nodes. In a binary tree each node has at most two children (left and right).", "Data Structures"),
]

import re

_questions = [k[0] for k in KNOWLEDGE]

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

_STOP = set(ENGLISH_STOP_WORDS) | {"explain", "tell", "me", "about", "how", "does", "work", "works", "difference", "between"}


def _tokenize(text):
    """Lower-case words with a very light plural stemmer (joins -> join)."""
    words = re.findall(r"[a-z0-9+#]+", text.lower())
    return [
        w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w
        for w in words
        if w not in _STOP
    ]


# Question counts triple so it dominates; answer text adds recall for loose wording
_documents = [(q + " ") * 3 + a for q, a, _ in KNOWLEDGE]

_vectorizer = TfidfVectorizer(
    tokenizer=_tokenize, token_pattern=None, lowercase=False,
    stop_words=None, ngram_range=(1, 2), sublinear_tf=True
)
_matrix = _vectorizer.fit_transform(_documents)

MIN_SCORE = 0.12

TOPIC_HINT = (
    "Try asking about Python, OOP, Machine Learning, overfitting, SQL joins, "
    "HTML, CSS, JavaScript, Flask, Git, stacks/queues or Big O."
)


def get_tutor_answer(user_question):
    """Return a dict: answer, confidence (0-100), topic, related (list of questions)."""
    user_question = (user_question or "").strip()

    if not user_question:
        return {"answer": "Please enter a question.", "confidence": 0, "topic": None, "related": []}

    scores = cosine_similarity(_vectorizer.transform([user_question]), _matrix)[0]
    order = scores.argsort()[::-1]
    best = int(order[0])

    if scores[best] < MIN_SCORE:
        return {
            "answer": "Sorry, I don't have a good answer for that yet. " + TOPIC_HINT,
            "confidence": 0,
            "topic": None,
            "related": [],
        }

    related = [
        _questions[int(i)] for i in order[1:4] if scores[int(i)] >= 0.05
    ]

    return {
        "answer": KNOWLEDGE[best][1],
        "confidence": min(99, round(float(scores[best]) * 100)),
        "topic": KNOWLEDGE[best][2],
        "matched_question": KNOWLEDGE[best][0],
        "related": related,
    }

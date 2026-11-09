import os
import pickle

import numpy as np
from sklearn.tree import DecisionTreeClassifier

MODEL_FOLDER = "ml_models"
MODEL_PATH = os.path.join(MODEL_FOLDER, "performance_model.pkl")

FEATURES = ["previous marks", "assignment marks", "quiz marks", "attendance"]
WEIGHTS = np.array([0.30, 0.25, 0.25, 0.20])

GOOD_CUTOFF = 72
AVERAGE_CUTOFF = 52


def _label(score):
    if score >= GOOD_CUTOFF:
        return "Good"
    if score >= AVERAGE_CUTOFF:
        return "Average"
    return "Needs Improvement"


def train_model():
    """Train a Decision Tree on 800 synthetic students.

    The labels follow a weighted-score rule that reproduces the 12 hand-made
    samples from the original project, with random variation added so the tree
    learns smooth boundaries rather than 12 points.
    """
    os.makedirs(MODEL_FOLDER, exist_ok=True)

    rng = np.random.default_rng(42)

    X = rng.uniform(20, 100, size=(800, 4))

    # Students' scores are correlated: a strong student is usually strong everywhere
    base = rng.uniform(25, 95, size=(800, 1))
    X = np.clip(0.7 * base + 0.3 * X, 0, 100)

    scores = X @ WEIGHTS + rng.normal(0, 2.5, size=800)
    y = np.array([_label(s) for s in scores])

    model = DecisionTreeClassifier(max_depth=5, min_samples_leaf=8, random_state=42)
    model.fit(X, y)

    with open(MODEL_PATH, "wb") as file:
        pickle.dump(model, file)

    print("ML model trained and saved to", os.path.abspath(MODEL_PATH))

    return model


def load_model():
    if not os.path.exists(MODEL_PATH):
        return train_model()

    try:
        with open(MODEL_PATH, "rb") as file:
            return pickle.load(file)
    except Exception:
        # Corrupt or saved by an incompatible scikit-learn version
        return train_model()


def predict_performance(previous_marks, assignment_marks, quiz_marks, attendance):
    model = load_model()
    data = np.array([[previous_marks, assignment_marks, quiz_marks, attendance]])
    return str(model.predict(data)[0])


def predict_with_details(previous_marks, assignment_marks, quiz_marks, attendance):
    """Prediction plus confidence, weighted score and the area to work on first."""
    model = load_model()
    values = np.array([previous_marks, assignment_marks, quiz_marks, attendance], dtype=float)

    label = str(model.predict([values])[0])
    probabilities = model.predict_proba([values])[0]
    confidence = float(probabilities.max()) * 100

    weighted = float(values @ WEIGHTS)

    # Largest weighted gap to a perfect score = most worthwhile thing to improve
    # (previous marks are history, so only the 3 changeable areas are considered)
    gaps = (100 - values[1:]) * WEIGHTS[1:]
    focus = FEATURES[1 + int(gaps.argmax())]

    return {
        "label": label,
        "confidence": round(confidence, 1),
        "weighted_score": round(weighted, 1),
        "focus_area": focus,
        "points_to_good": max(0, round(GOOD_CUTOFF - weighted, 1)),
    }


if __name__ == "__main__":
    train_model()

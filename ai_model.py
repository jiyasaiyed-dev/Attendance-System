"""
AI Module - Attendance Risk Prediction
----------------------------------------
Uses a simple Decision Tree Classifier (scikit-learn) to classify students
into: 'Good', 'Average', or 'Shortage Risk' based on their attendance
percentage and related simple features.

No face recognition / webcam / camera involved anywhere.
The model is trained on synthetic-but-realistic rule-based data that
mirrors institutional attendance policy, then used to predict live data
pulled from MySQL.
"""

import os
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
import joblib

MODEL_PATH = os.path.join(os.path.dirname(__file__), "attendance_model.pkl")


def _generate_training_data(n=500, seed=42):
    """
    Generates synthetic training data.
    Features:
        - attendance_percentage (0-100)
        - total_classes (number of classes held so far)
        - absent_streak (longest consecutive absent streak)
    Label:
        - Good           : percentage >= 85
        - Average         : 75 <= percentage < 85
        - Shortage Risk   : percentage < 75
    (This mirrors a common academic attendance policy: 75% minimum requirement.)
    """
    rng = np.random.default_rng(seed)
    attendance_percentage = rng.uniform(0, 100, n)
    total_classes = rng.integers(20, 120, n)
    absent_streak = rng.integers(0, 15, n)

    # Absent streak slightly pulls percentage down for realism
    attendance_percentage = np.clip(
        attendance_percentage - (absent_streak * rng.uniform(0, 0.5, n)), 0, 100
    )

    labels = []
    for p in attendance_percentage:
        if p >= 85:
            labels.append("Good")
        elif p >= 75:
            labels.append("Average")
        else:
            labels.append("Shortage Risk")

    df = pd.DataFrame({
        "attendance_percentage": attendance_percentage,
        "total_classes": total_classes,
        "absent_streak": absent_streak,
        "label": labels
    })
    return df


def train_model():
    """Trains the Decision Tree model and saves it to disk."""
    df = _generate_training_data()
    X = df[["attendance_percentage", "total_classes", "absent_streak"]]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = DecisionTreeClassifier(
        criterion="gini",
        max_depth=5,
        min_samples_split=4,
        random_state=42
    )
    clf.fit(X_train, y_train)

    accuracy = clf.score(X_test, y_test)
    print(f"[AI MODEL] Decision Tree trained. Test accuracy: {accuracy:.2%}")

    joblib.dump(clf, MODEL_PATH)
    return clf


def load_model():
    """Loads the trained model from disk, training it first if it doesn't exist."""
    if not os.path.exists(MODEL_PATH):
        return train_model()
    return joblib.load(MODEL_PATH)


def predict_risk(attendance_percentage, total_classes=60, absent_streak=0):
    """
    Predicts risk category for a single student.
    Returns one of: 'Good', 'Average', 'Shortage Risk'
    """
    clf = load_model()
    features = pd.DataFrame([{
        "attendance_percentage": attendance_percentage,
        "total_classes": total_classes,
        "absent_streak": absent_streak
    }])
    prediction = clf.predict(features)[0]
    return prediction


def predict_bulk(students_data):
    """
    students_data: list of dicts with keys
        'attendance_percentage', 'total_classes', 'absent_streak'
    Returns list of predicted labels in the same order.
    """
    clf = load_model()
    df = pd.DataFrame(students_data)
    if df.empty:
        return []
    predictions = clf.predict(df[["attendance_percentage", "total_classes", "absent_streak"]])
    return list(predictions)


if __name__ == "__main__":
    # Run this file directly to (re)train the model: python model/ai_model.py
    train_model()

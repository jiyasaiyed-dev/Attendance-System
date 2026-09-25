# AI-Based Attendance System
**FAI Mini Project**

A simple, professional web-based attendance management system with an AI (Decision Tree)
module that predicts each student's attendance risk category: **Good**, **Average**, or
**Shortage Risk**.

> ⚠️ No face recognition, no webcam, no camera. Attendance is marked manually by the admin
> through the web UI, and MySQL stores all data.

---

## 🧰 Tech Stack

| Layer      | Technology                     |
|------------|---------------------------------|
| Frontend   | HTML, CSS, JavaScript (Jinja2 templates) |
| Backend    | Python 3 + Flask                |
| Database   | MySQL (via WAMP Server)         |
| AI/ML      | scikit-learn (Decision Tree Classifier) |

---

## 📁 Folder Structure

```
attendance_system/
│
├── app.py                     # Main Flask application (routes/controllers)
├── db_config.py                # MySQL connection configuration
├── database.sql                # SQL file to create DB, tables & sample data
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── model/
│   ├── ai_model.py             # Decision Tree training + prediction logic
│   └── attendance_model.pkl    # (auto-generated after first run)
│
├── templates/                  # HTML (Jinja2) templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── students.html
│   ├── student_form.html
│   ├── mark_attendance.html
│   ├── reports.html
│   ├── date_wise.html
│   ├── student_report.html
│   └── ai_analysis.html
│
└── static/
    ├── css/style.css           # All styling
    └── js/main.js               # Small client-side helper
```

---

## 🖥️ Windows Setup Instructions (using WAMP)

### 1. Install & Start WAMP
1. Download and install **WAMP Server** (64-bit) from https://www.wampserver.com/
2. Launch WAMP. Wait until the tray icon turns **green** (Apache is not strictly required
   for this project — only the **MySQL** service needs to be running).
3. Left-click the WAMP icon → **MySQL** → ensure the service is started.

### 2. Create the Database
**Option A — phpMyAdmin (recommended):**
1. Click the WAMP tray icon → `phpMyAdmin` (opens in browser, usually `http://localhost/phpmyadmin`).
2. Login (default user: `root`, password: empty).
3. Click **Import** tab → choose file → select `database.sql` from this project.
4. Click **Go**. This creates the `attendance_system` database with all tables and sample data.

**Option B — MySQL command line:**
```bash
"C:\wamp64\bin\mysql\mysqlX.X.X\bin\mysql.exe" -u root -p < database.sql
```
(Replace the path with your actual WAMP MySQL bin path; press Enter when asked for password if it's empty.)

### 3. Verify Database Config
Open `db_config.py` and confirm these match your WAMP MySQL setup:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",       # change if you set a password in WAMP
    "database": "attendance_system",
    "port": 3306
}
```

### 4. Install Python & Dependencies
1. Install **Python 3.10+** from https://www.python.org/downloads/ (check "Add Python to PATH" during install).
2. Open Command Prompt in the project folder:
   ```bash
   cd path\to\attendance_system
   ```
3. (Recommended) Create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 5. Run the Application
```bash
python app.py
```
You should see:
```
* Running on http://127.0.0.1:5000
```

### 6. Open in Browser
Go to: **http://127.0.0.1:5000**

**Default Admin Login:**
- Username: `admin`
- Password: `admin123`

> The first time any AI page is loaded, the Decision Tree model auto-trains and saves
> to `model/attendance_model.pkl`. You can also click "Retrain Model" anytime on the
> AI Analysis page.

---

## ✅ Features

- **Admin Login** — secure session-based login (SHA-256 hashed password).
- **Student Management** — Add / Edit / Delete students with search & filter.
- **Mark Attendance** — daily Present/Absent marking per student, editable per date.
- **Attendance Percentage** — auto-calculated per student.
- **Reports**:
  - Student-wise attendance history & percentage.
  - Date-wise attendance for the whole class.
  - Overall report table with AI risk tags.
- **Dashboard** — total students, today's present/absent counts, AI risk distribution.
- **AI Analysis (Decision Tree)** — classifies every student as:
  - 🟢 **Good** (≥ 85% attendance)
  - 🟠 **Average** (75%–84% attendance)
  - 🔴 **Shortage Risk** (< 75% attendance)
  
  based on attendance percentage, total classes held, and current absent streak.
- **Search & Filter** — quickly find students by name / roll no / course.

---

## 🔐 Changing the Admin Password

Generate a new SHA-256 hash and update the `admin` table:
```python
import hashlib
print(hashlib.sha256("your_new_password".encode()).hexdigest())
```
```sql
UPDATE admin SET password = '<generated_hash>' WHERE username = 'admin';
```

---

## 🧠 About the AI Model

`model/ai_model.py` trains a **Decision Tree Classifier** on features:
- `attendance_percentage`
- `total_classes`
- `absent_streak` (consecutive recent absences)

Training data is generated programmatically following the standard 75% attendance
policy rule, so the tree learns realistic decision boundaries. It is retrained
automatically if no saved model is found, and can be manually retrained from the
**AI Analysis** page.

---

## 📌 Notes
- Runs in Flask debug mode by default for development (`app.run(debug=True)`).
  Turn this off for production use.
- No camera, webcam, or face recognition is used anywhere in this project.

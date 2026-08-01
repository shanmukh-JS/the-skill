# Skill Exchange Platform (Flask)

A production-grade, secure, full-stack Flask web application where users teach each other skills 1-on-1, send and manage learning requests, engage in real-time chat, and build reputation via verified peer reviews.

---

## 🚀 Setup & Local Execution Instructions

### Prerequisites
- **Python 3.11+**
- **pip** and **virtualenv**

### 1. Clone & Set Up Environment
```bash
git clone <repository-url>
cd "skill exchange"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure your `.env` contains:
```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secure-secret-key
DATABASE_URL=sqlite:///app.db
```

### 3. Database Migrations
Initialize and run database migrations using Flask-Migrate (Alembic):
```bash
# Initialize migration repository (first-time setup)
flask db init

# Generate migration script
flask db migrate -m "Initial schema setup"

# Apply migrations to database
flask db upgrade
```

### 4. Run the Application
Start the development server:
```bash
python run.py
# or
flask run
```
Open your browser at `http://127.0.0.1:5000`.

---

## 🧪 Running Automated Tests

Run the full `pytest` suite (covering Auth, Models, Requests, Ratings, Search):
```bash
pytest -v
```

---

## 🛡️ Key Architectural & Design Decisions Log

1. **Skill Deletion Policy (Soft Delete):**
   - Implemented via `Skill.is_active = db.Column(db.Boolean, default=True)`.
   - If a skill has active (`pending` or `accepted`) requests attached, deletion is **blocked** with an informative flash message.
   - If a skill is referenced by historical (`completed`, `rejected`, `cancelled`) requests, it is **soft-deleted** (`is_active = False`). This hides the skill from active searches and new request forms while keeping database referential integrity (`NOT NULL` FK constraints) intact across requests, chats, ratings, and learning history.

2. **Production-Grade Login Rate Limiting (Multi-Worker Safe):**
   - Implemented using a database model `FailedLogin` (`id`, `ip_address`, `username`, `attempted_at`).
   - Tracks failed login attempts across all Gunicorn WSGI worker processes (max 5 failed attempts per 15-minute window), persisting across restarts and horizontal process scaling.

3. **Average Rating Calculation:**
   - Computed dynamically at **query-time** via `sqlalchemy.func.avg(Rating.score)` filtered by `Rating.rated_user_id == user.id`. This avoids denormalization sync bugs and guarantees 100% data consistency.

4. **Request Completion Trigger & Dual History Logging:**
   - Either participant on an `accepted` request can trigger "Mark Complete".
   - Transitioning to `completed` automatically writes **two** `LearningHistory` records: one for the teacher (`role='teacher'`) and one for the learner (`role='learner'`).

5. **Rating Edit Window:**
   - Rating updates and deletions are time-boxed to **24 hours** from creation (`Rating.created_at`). After 24 hours, ratings are locked to prevent retroactive manipulation.

6. **AJAX + CSRF Protection:**
   - Global CSRF token is embedded in `<meta name="csrf-token">`.
   - Sent via `X-CSRFToken` HTTP header in `static/js/chat.js` for all fetch calls (polling, sending messages, marking notifications as read).

---

## ☁️ Production Deployment Guide (Render / Railway)

### Deploying to Render
1. Push your repository to GitHub/GitLab.
2. Log into [Render Dashboard](https://dashboard.render.com/) and click **New + > Web Service**.
3. Select your repository.
4. Set Build Command:
   ```bash
   pip install -r requirements.txt && flask db upgrade
   ```
5. Set Start Command:
   ```bash
   gunicorn run:app
   ```
6. Add Environment Variables:
   - `FLASK_CONFIG`: `production`
   - `SECRET_KEY`: `<generate-a-strong-random-key>`
   - `DATABASE_URL`: `<render-postgresql-internal-database-url>`
7. Click **Create Web Service**. Render handles SSL termination automatically.

---

## 📁 Repository Structure Overview

```
skill-exchange-platform/
├── app/
│   ├── __init__.py              # App factory, extension init, blueprint registration
│   ├── config.py                # Config, DevelopmentConfig, TestingConfig, ProductionConfig
│   ├── extensions.py            # db, migrate, login_manager, csrf instances
│   ├── models/                  # SQLAlchemy ORM Models
│   │   ├── __init__.py
│   │   ├── user.py              # User, FailedLogin
│   │   ├── skill.py             # Skill (soft delete), LearningInterest
│   │   ├── request.py           # Request (status enum)
│   │   ├── chat.py              # Chat, Message
│   │   ├── rating.py            # Rating (24h edit window, unique constraint)
│   │   ├── history.py           # LearningHistory
│   │   └── notification.py      # Notification
│   ├── routes/                  # 10 Blueprints
│   │   ├── __init__.py
│   │   ├── main.py              # Public homepage & about
│   │   ├── auth.py              # Auth lifecycle & rate limiting
│   │   ├── profile.py           # User profile & avatar upload
│   │   ├── skills.py            # Skill & interest CRUD
│   │   ├── search.py            # Search & teacher discovery
│   │   ├── requests.py          # Request lifecycle state machine
│   │   ├── chat.py              # Chat room & polling endpoint
│   │   ├── ratings.py           # Rating & review CRUD
│   │   ├── dashboard.py         # Dashboard stats & history
│   │   └── admin.py             # Admin portal, moderation & analytics
│   ├── forms/                   # Flask-WTF Forms with validation
│   │   ├── auth_forms.py
│   │   ├── profile_forms.py
│   │   ├── skill_forms.py
│   │   └── request_forms.py
│   ├── templates/               # Jinja2 Templates
│   │   ├── base.html            # Base layout with CSRF meta & header dropdown
│   │   ├── main/
│   │   ├── auth/
│   │   ├── profile/
│   │   ├── skills/
│   │   ├── search/
│   │   ├── requests/
│   │   ├── chat/
│   │   ├── ratings/
│   │   ├── dashboard/
│   │   ├── admin/
│   │   └── partials/            # Header dropdown partial
│   ├── static/
│   │   ├── css/style.css
│   │   ├── js/chat.js           # Polling & CSRF fetch headers
│   │   └── uploads/profile_pics/ # Profile pictures (.gitkeep tracked)
│   └── utils/                   # Centralized Utilities
│       ├── decorators.py        # admin_required
│       ├── validators.py        # Password complexity & file checkers
│       ├── notifications.py     # Notification dispatcher
│       └── rate_limiter.py      # Database-backed rate limiter
├── migrations/                  # Generated by Flask-Migrate
├── tests/                       # Pytest Test Suite
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_models.py
│   ├── test_requests.py
│   ├── test_ratings.py
│   └── test_search.py
├── .env.example
├── .gitignore
├── COMPLETION.md                # 100% Audit Completion Checklist
├── requirements.txt             # Pinned exact versions
├── run.py                       # WSGI entrypoint
└── README.md
```

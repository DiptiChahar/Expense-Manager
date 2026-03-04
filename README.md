# SpendSmart

SpendSmart is a personal finance management application that helps users track income, expenses, bills, and financial goals in a secure and structured way.
It uses a FastAPI backend with PostgreSQL and a lightweight multi-page frontend built with HTML, CSS, and JavaScript.

The project focuses on clean backend architecture, modular code structure, and scalable financial analytics.

---

# Features

* Track income and expenses with categorized transactions.
* Manage bills, budgets, and financial goals.
* Dashboard insights for income, expenses, and financial summaries.
* Secure JWT authentication with strict user data isolation.
* Transaction filtering and export capabilities.

**Upcoming Enhancements**

* Machine learning–based expense forecasting (Random Forest, LSTM).
* AI assistant powered by OpenAI for personalized budgeting insights and spending recommendations.

---

# Tech Stack

**Frontend**

* HTML
* CSS
* JavaScript (multi-page)

**Backend**

* FastAPI

**Database**

* PostgreSQL

**AI / ML (planned)**

* Random Forest
* LSTM
* OpenAI API

---

# Environment Configuration

Create the file:

```bash
backend/.env
```

Add the following configuration:

```bash
DATABASE_URL=postgresql://<user>:<password>@localhost:5432/<database_name>

ENV=development

CORS_ALLOW_ORIGINS=http://localhost:5500,http://127.0.0.1:5500

JWT_SECRET_KEY=<your-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

OPENAI_API_KEY=<your-openai-key>

DB_STATEMENT_TIMEOUT_MS=5000
DB_LOCK_TIMEOUT_MS=2000

AUTO_APPLY_MIGRATIONS=true
```

---

# Backend Setup

### 1. Install Dependencies

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Run Migrations

```bash
python -m app.db.migrate
```

### 3. Start Backend Server

```bash
uvicorn app.main:app --reload
```

Backend runs at:

```
http://127.0.0.1:8000
```

API Base URL:

```
http://127.0.0.1:8000/api/v1
```

API documentation:

```
http://127.0.0.1:8000/docs
```

---

# Frontend Setup

Run a simple server:

```bash
cd frontend
python3 -m http.server 5500
```

Open:

```
http://127.0.0.1:5500
```

---

# Authentication

Auth endpoints:

```
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

Successful authentication returns:

```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

Use token in requests:

```
Authorization: Bearer <token>
```

---

# Security Notes

* All financial APIs require authentication.
* User data is isolated using `user_id` derived from JWT.
* Sensitive information such as passwords and tokens is never logged.

---

# License

This project is intended for educational and portfolio purposes.

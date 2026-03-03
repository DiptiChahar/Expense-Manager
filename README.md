# SpendSmart

SpendSmart is an AI-powered personal expense management and forecasting app.

## Tech Stack
- Frontend: HTML + CSS + JavaScript (multi-page architecture)
- Backend: Python FastAPI
- Database: PostgreSQL (raw SQL, no ORM)
- No Node.js runtime required

## Project Hierarchy

```text
project/
├── frontend/
│   ├── index.html                    # redirects to dashboard page
│   ├── html/                         # separate HTML page per feature
│   │   ├── dashboard.html
│   │   ├── transactions.html
│   │   ├── bills.html
│   │   ├── income.html
│   │   ├── expenses.html
│   │   └── goals.html
│   ├── components/                   # reusable markup fragments
│   │   ├── sidebar.html
│   │   └── topbar.html
│   ├── css/
│   │   ├── base.css
│   │   ├── components/
│   │   │   ├── sidebar.css
│   │   │   ├── topbar.css
│   │   │   ├── buttons.css
│   │   │   ├── panel.css
│   │   │   ├── table.css
│   │   │   └── modal.css
│   │   └── pages/
│   │       ├── dashboard.css
│   │       ├── transactions.css
│   │       ├── bills.css
│   │       ├── income.css
│   │       ├── expenses.css
│   │       └── goals.css
│   └── js/
│       ├── core/
│       │   ├── api.js
│       │   ├── charts.js
│       │   ├── format.js
│       │   ├── layout.js
│       │   ├── modal.js
│       └── pages/
│           ├── dashboard.js
│           ├── transactions.js
│           ├── bills.js
│           ├── income.js
│           ├── expenses.js
│           └── goals.js
└── backend/
    ├── requirements.txt
    ├── .env.example
    ├── main.py                        # compatibility entrypoint (imports app.main)
    └── app/
        ├── main.py                    # FastAPI app setup
        ├── core/
        │   ├── config.py
        │   └── database.py
        ├── models/
        │   ├── sql_models.py
        │   └── schema.sql
        ├── schemas/
        │   ├── transactions.py
        │   ├── budgets.py
        │   ├── goals.py
        │   ├── bills.py
        │   └── notifications.py
        ├── routers/
        │   ├── __init__.py
        │   ├── health.py
        │   ├── transactions.py
        │   ├── income.py
        │   ├── expenses.py
        │   ├── budgets.py
        │   ├── goals.py
        │   ├── bills.py
        │   ├── dashboard.py
        │   ├── statistics.py
        │   └── notifications.py
        └── utils/
            ├── db.py
            ├── serialization.py
            ├── schema_init.py
            └── transactions.py
```

## Backend Setup (FastAPI + PostgreSQL)

1. Create PostgreSQL database named `spendsmart`.
2. Create env file:
   - `cp backend/.env.example backend/.env`
3. Install dependencies:
   - `cd backend`
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt`
4. Run API:
   - `uvicorn app.main:app --reload`

API default URL: `http://localhost:8000`

## Frontend Setup

1. Serve static frontend:
   - `cd frontend`
   - `python3 -m http.server 5500`
2. Open:
   - `http://localhost:5500`

The frontend is pre-wired to `http://localhost:8000`.

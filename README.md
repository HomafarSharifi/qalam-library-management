# 📚 قلم (Qalam) - Library Management System
**سیستم جامع و مدرن مدیریت کتابخانه قلم**

Qalam is a full-stack library management system featuring a high-performance **FastAPI** backend with **MySQL**, and a responsive **React 18 + Vite** frontend tailored with Persian/Dari RTL typography and Afghan Solar Hijri (هجری خورشیدی) calendar integration.

---

## 🌟 Key Features

- **📖 Books & Inventory Management**: Full cataloging with title, ISBN, description, multi-author associations, and real-time total/available copies tracking.
- **✍️ Authors & Categories**: Dynamic grouping and categorization with safe deletion constraints preventing accidental data loss.
- **👥 Member Management**: Member registration with contact validation, duplicate email protection, and active loan tracking.
- **🔄 Circulation & Loans Lifecycle**:
  - Atomic copy reservations (checks copy availability and decrements available inventory upon issue).
  - Return workflow with automatic overdue calculation and daily fine computation.
  - Safe cancellation with automatic inventory restoration.
- **📊 Reports & Dashboard**: Real-time stats, most borrowed books, overdue tracking, and monthly activity trends.
- **📅 Afghan Jalali Calendar Support**: Full conversion and display of official Solar Hijri dates alongside standard Gregorian dates.
- **🛡️ Secure & Resilient**:
  - Parameterized queries protecting against SQL injection.
  - Atomic database transactions with automatic rollback on errors.
  - Connection pooling with reconnection fallback.
  - Offline-first resilience: frontend gracefully operates with local persistence when backend server is restarting.

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python 3.12+, FastAPI, Uvicorn, Pydantic v2, MySQL Connector Python, Python-Dotenv |
| **Frontend** | React 18, Vite 6, React Router DOM v6, Lucide React, Yekan Bakh Persian Font |
| **Database** | MySQL 8.0+ / MariaDB with strict relational constraints and indexing |
| **Testing** | Built-in Python unittest framework with in-memory database simulator (80 tests) |

---

## 📁 Project Structure

```text
Qalam/
├── backend/
│   ├── routers/             # Modular API route controllers
│   │   ├── authors.py       # Author endpoints (/api/authors)
│   │   ├── books.py         # Book & Copy endpoints (/api/books)
│   │   ├── categories.py    # Category endpoints (/api/categories)
│   │   ├── loans.py         # Loan issue & return (/api/loans)
│   │   ├── members.py       # Member endpoints (/api/members)
│   │   └── reports.py       # Dashboard stats & analytics (/api/reports)
│   ├── schemas/             # Pydantic validation schemas
│   ├── tests/               # 80 automated unit & integration tests
│   │   ├── mock_db.py       # In-memory relational database test engine
│   │   ├── run_all_tests.py # Master test runner
│   │   └── test_*.py        # Test modules for all services
│   ├── database.py          # Connection pool, transactions & error mapping
│   ├── main.py              # FastAPI application entrypoint & middleware
│   ├── requirements.txt     # Python backend dependencies
│   ├── .env.example         # Template for environment configuration
│   └── .env                 # Local environment variables (ignored by git)
├── frontend/
│   ├── public/              # Static public assets and icons
│   ├── src/
│   │   ├── components/      # Reusable UI components & Afghan DatePicker
│   │   ├── data/
│   │   │   ├── api.js / libraryService.js # API client & state persistence
│   │   ├── utils/           # Afghan Jalali date conversion utilities
│   │   ├── App.jsx          # Main application & routing logic
│   │   └── App.css          # Design system, RTL styles & dark/light palettes
│   ├── package.json         # Node.js dependencies
│   └── vite.config.js       # Vite configuration with automatic /api proxy
├── sql/
│   ├── schema.sql           # Database DDL with tables, keys & check constraints
│   └── sample_data.sql      # Initial seed dataset matching demo books & members
├── .gitignore               # Comprehensive GitHub ignore protecting sensitive files
└── README.md                # Project documentation
```

---

## 🚀 Getting Started

### 1. Database Setup
Make sure you have a running **MySQL** server (e.g. via MySQL Server, XAMPP, or Docker).

Import the schema and initial seed data:
```bash
# Log into MySQL and run the schema and seed scripts
mysql -u root -p < sql/schema.sql
mysql -u root -p < sql/sample_data.sql
```

---

### 2. Backend Setup

1. Open a terminal and navigate to the `backend/` directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to match your local MySQL configuration:
   ```env
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=Qalam
   DB_POOL_NAME=qalam_pool
   DB_POOL_SIZE=5
   FINE_PER_DAY=5.0
   ```

5. Start the backend server:
   ```bash
   uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```
   The backend API will start at `http://127.0.0.1:8000`.
   - **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
   - **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

### 3. Frontend Setup

1. Open a new terminal and navigate to `frontend/`:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   Open your browser at `http://localhost:5173`.
   - The Vite development server automatically proxies all `/api/*` requests to the FastAPI backend running at `http://127.0.0.1:8000`.
   - A live connection badge in the top bar indicates connection status (`متصل به سرور` / `حالت آفلاین`).

---

## 🧪 Running the Backend Test Suite

The backend includes a comprehensive, automated test suite with **80 unit and integration tests** testing all endpoints, edge cases, constraint violations, and transactions:

```bash
# Run all tests
backend\.venv\Scripts\python backend\tests\run_all_tests.py
```

Expected output:
```text
======================================================================
           QALAM LIBRARY MANAGEMENT SYSTEM - TEST SUITE
======================================================================
...
Ran 80 tests in 0.06s
OK
Tests run: 80 | Failures: 0 | Errors: 0 | Success: True
======================================================================
```

---

## 🔒 Security & Sensitive Data Guidelines for GitHub

To protect sensitive credentials when pushing to GitHub:

- **Never commit `.env` files**: All environment variable files (`.env`, `.env.*`, `*.env`) are strictly excluded by [.gitignore](file:///.gitignore).
- **Template Only**: Commit only [.env.example](file:///backend/.env.example) containing placeholder values.
- **Ignored Artifacts**: Private keys (`*.pem`, `*.key`), database files (`*.sqlite`, `*.db`), virtual environments (`.venv/`), and build output (`dist/`, `node_modules/`) are protected by git rules.
- **SQL Sanitization**: All database interaction in the backend uses parameterized SQL bindings (`%s`) to prevent SQL injection vulnerabilities.

---

## 📡 API Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Server & database connection status |
| `GET` | `/api/books` | List books (search by title/ISBN/author, category filter, pagination) |
| `POST` | `/api/books` | Create book, author associations, and copy inventory |
| `PUT` | `/api/books/{id}` | Update book information and authors |
| `PUT` | `/api/books/{id}/copies` | Update total and available book copies |
| `DELETE` | `/api/books/{id}` | Delete book (safe check: rejects if copies are on active loan) |
| `GET` | `/api/authors` | List authors with book counts |
| `POST` | `/api/authors` | Register author |
| `DELETE` | `/api/authors/{id}` | Delete author (rejects if linked to books) |
| `GET` | `/api/categories` | List categories with book counts |
| `POST` | `/api/categories` | Create category (unique name check) |
| `DELETE` | `/api/categories/{id}` | Delete category (rejects if books belong to it) |
| `GET` | `/api/members` | List members with active loan counts |
| `POST` | `/api/members` | Register member (unique email check) |
| `DELETE` | `/api/members/{id}` | Delete member (rejects if member has active loans) |
| `GET` | `/api/loans` | List loans with status filters (`active`, `returned`, `overdue`) |
| `POST` | `/api/loans` | Issue a loan (atomically decrements copy availability) |
| `POST` | `/api/loans/{id}/return` | Return a loan (atomically increments copy availability & computes fines) |
| `DELETE` | `/api/loans/{id}` | Cancel/delete loan (restores copy inventory if active) |
| `GET` | `/api/reports/stats` | Dashboard statistics overview |
| `GET` | `/api/reports/top-books` | Top most borrowed books |
| `GET` | `/api/reports/overdue` | List overdue loans with calculated fines |
| `GET` | `/api/reports/activity` | Monthly circulation activity for charts |

---

## 📄 License
This project is licensed under the MIT License. See [LICENSE](file:///LICENSE) for details.

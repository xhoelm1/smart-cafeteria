# Smart Cafeteria — Queue Management System

A full-stack web application that lets university students pre-order food, reserve a
pickup time slot, and skip the break-hour queue. Staff manage incoming orders on a
live Kanban dashboard; admins manage the menu, users, and daily reports.

> _Screenshots placeholder — drop PNGs into `docs/` and reference them here._

---

## Team

| Member             | Role                         |
|--------------------|------------------------------|
| Xhesilda Kullolli  | Team Lead                    |
| Erisilda Zhaboli   | Research                     |
| Megi Bicaku        | Solution & Scope             |
| Xhoel Merkuli      | App Description & Features   |

---

## Tech Stack

| Layer        | Technology                                    |
|--------------|-----------------------------------------------|
| Language     | Python 3.10+ (tested on 3.12)                 |
| Framework    | Flask 3                                       |
| Templating   | Jinja2                                        |
| ORM          | SQLAlchemy 2 via Flask-SQLAlchemy             |
| Auth         | Flask-Login + Werkzeug password hashing       |
| Forms / CSRF | Flask-WTF                                     |
| Migrations   | Flask-Migrate (Alembic)                       |
| Database     | SQLite by default (MySQL-compatible schema)   |
| Frontend     | Server-rendered Jinja + vanilla CSS + vanilla JS |
| Real-time UI | `fetch()` polling every 5 s                   |
| Tests        | pytest + pytest-flask                         |

---

## Quick Start

```bash
# 1. clone & cd
cd smart-cafeteria

# 2. virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 3. install
pip install -r requirements.txt

# 4. run (database + demo data are seeded automatically on first run)
python run.py
```

Open <http://127.0.0.1:5000>.

---

## Demo Credentials (password for all: `Demo1234!`)

| Role    | Email                       |
|---------|-----------------------------|
| Admin   | `admin@cafeteria.edu`       |
| Staff   | `staff@cafeteria.edu`       |
| Student | `student1@cafeteria.edu`    |
| Student | `student2@cafeteria.edu`    |
| Student | `student3@cafeteria.edu`    |

---

## Features

- [x] Student registration & login (CSRF-protected forms, hashed passwords)
- [x] Menu browsing with search, stock badges, sold-out handling
- [x] Session-based shopping cart with quantity controls
- [x] Time-slot pickup picker with capacity enforcement
- [x] Atomic checkout that decrements stock and reserves the slot
- [x] Order detail page with auto-polling live status
- [x] Cancel order before preparation (stock auto-returned)
- [x] In-app notifications (bell + unread count) when an order is ready
- [x] Staff Kanban dashboard (Pending → Preparing → Ready) with auto-refresh
- [x] Staff one-click availability toggle on menu items
- [x] Admin menu CRUD (create / edit / delete)
- [x] Admin user management (create staff/admin, enable/disable accounts)
- [x] Admin daily report (orders, revenue, top 5 items, status breakdown) with date picker
- [x] Role-based access control via `@role_required(...)`
- [x] Responsive layout (works at 375 px width)

---

## Project Structure

```
smart-cafeteria/
├── README.md
├── requirements.txt
├── config.py
├── run.py
├── .env.example
├── .gitignore
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── extensions.py        # db, login_manager, csrf, migrate
│   ├── models.py            # SQLAlchemy models
│   ├── seed.py              # Idempotent demo data seeder
│   ├── blueprints/
│   │   ├── auth.py
│   │   ├── student.py
│   │   ├── staff.py
│   │   ├── admin.py
│   │   └── api.py           # JSON endpoints for polling
│   ├── templates/
│   │   ├── base.html
│   │   ├── partials/        # navbar, flash
│   │   ├── auth/            # login, register
│   │   ├── student/         # menu, cart, checkout, my_orders, ...
│   │   ├── staff/           # dashboard, menu, order_card
│   │   └── admin/           # menu, menu_form, users, reports
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/app.js
│   └── utils/
│       ├── decorators.py    # @role_required
│       └── notifications.py # notify() helper
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_student_flow.py
│   ├── test_staff_flow.py
│   ├── test_admin_flow.py
│   └── test_smoke_routes.py
└── instance/                # SQLite file lives here (gitignored)
```

---

## Switching from SQLite to MySQL

Change one environment variable — no code changes needed:

```bash
export DATABASE_URL="mysql+pymysql://USER:PASSWORD@HOST/DBNAME"
pip install pymysql
python run.py
```

The schema is portable; SQLAlchemy emits MySQL-compatible DDL.

---

## Running the Tests

```bash
.venv\Scripts\activate     # or source .venv/bin/activate
pytest -q
```

22 tests cover authentication, student order flow, time-slot capacity, cancellation
rules, staff status transitions, notification creation, admin CRUD, role-based access
control, and a smoke check that hits every page in every role with no 500.

---

## Future Improvements

- Real-time push via WebSockets instead of HTTP polling
- Payment gateway integration (Stripe / Paddle)
- QR-code pickup confirmation
- Push / email notifications
- Per-day analytics charts (Chart.js)
- Multi-language support (sq / en)

---

## License

MIT — see `LICENSE` (add one before publishing publicly).

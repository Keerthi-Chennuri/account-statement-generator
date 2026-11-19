# Account Statement Generator

A fintech-style account statement workspace built as a college mini-project.
Manage multiple accounts, record credits and debits, see balances update
instantly, and export a professional PDF statement for any date range.

> **Educational prototype.** No real bank connection, no real money transfer,
> no banking credentials. All accounts, names and amounts are demo data.
> Account numbers are stored masked (`XXXX1234`) — never in full.

---

## Features

| Area | What works |
| --- | --- |
| Authentication | Secure login/logout, PBKDF2 password hashing, HttpOnly session cookie, "remember me", show/hide password, validation, read-only analyst role |
| Dashboard | Account count, total credits, total debits, combined balance, 6-month cash-flow chart, credit vs debit donut, recent transactions, quick actions |
| Accounts | Create, read, update, delete (with confirmation), search by holder/number, filter by account type, computed current balance |
| Transactions | Create, edit, delete, search, filter by account/type/date range, green credit and red debit indicators, status labels, empty states |
| Statement generator | Account + date range, quick ranges, preview, print, PDF download, opening/closing balance, running balance per row |
| Transaction details | Full entry with previous balance and updated balance |
| Settings | Profile name, password change, statement defaults, chart preference, logout |
| UX | Responsive sidebar/drawer, skeleton loaders, toasts, modals, accessible contrast, print stylesheet |

### Demo accounts

| Role | Username | Password | Access |
| --- | --- | --- | --- |
| Admin | `rahul` | `demo1234` | Create, edit, delete |
| Analyst | `priya` | `demo1234` | Read-only |

`rahul` starts with three accounts (Savings `XXXX1234` opening ₹10,000,
Current `XXXX7788`, Salary `XXXX2190`) and several months of transactions.
The brief's sample is included in the Savings account:
**₹10,000 opening + ₹5,000 credit − ₹2,000 debit = ₹13,000 closing.**

---

## Tech stack

- **Frontend:** React 18, Vite, Tailwind CSS 3, Lucide React icons, Recharts, React Router
- **Backend:** Python Flask REST API, Decimal arithmetic
- **Database:** SQLite (MySQL-compatible schema), automatically created and seeded
- **PDF:** ReportLab
- **Auth:** Flask signed session cookie + `werkzeug.security` password hashing

---

## Project structure

```
account statement generator/
├── backend/
│   ├── app.py                    # Flask app factory + error handlers + CLI
│   ├── config.py                 # Environment-driven configuration
│   ├── requirements.txt
│   ├── authentication/
│   │   └── auth.py               # Session login, login_required, roles_required
│   ├── database/
│   │   ├── db.py                 # Per-request SQLite connection
│   │   ├── schema.sql            # users / accounts / transactions
│   │   └── seed.py               # Demo users, accounts, transactions
│   ├── models/                   # user.py, account.py, transaction.py (SQL)
│   ├── services/                 # auth, account, transaction, statement, dashboard
│   ├── routes/                   # REST blueprints (thin controllers)
│   ├── pdf/statement_pdf.py      # ReportLab statement builder
│   └── utils/                    # money.py, validators.py, errors.py
└── frontend/
    ├── index.html
    ├── src/
    │   ├── pages/                # Login, Dashboard, Accounts, Transactions,
    │   │                         # TransactionDetails, Statements, Settings, NotFound
    │   ├── layouts/AppLayout.jsx # Sidebar + top bar + mobile drawer
    │   ├── components/           # Form modals, transaction table, UI kit
    │   ├── hooks/                # useAuth, useToast, useDebounce
    │   ├── services/api.js       # Single fetch wrapper for every endpoint
    │   ├── utils/format.js       # ₹ (en-IN) and date formatting
    │   └── assets/               # (add your own logos/illustrations here)
    └── package.json
```

---

## Run it locally

### Requirements

- Python 3.10+
- Node.js 18+ (LTS)

### 1. Backend (Flask API) — port 5000

```bash
cd backend

# Create and activate a virtual environment (Windows)
python -m venv .venv
.venv\Scripts\activate
# macOS / Linux: python3 -m venv .venv && source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

On first start the database file `backend/database/statement.db` is created,
the schema is applied and demo data is inserted. Visit
<http://127.0.0.1:5000/api/health> to confirm the API is up.

To reset the demo data, delete `backend/database/statement.db` and restart.
To re-seed only an empty database manually: `flask --app app seed-demo`.

### 2. Frontend (React) — port 5173

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173> and sign in with `rahul / demo1234`.

Vite proxies `/api` to `http://127.0.0.1:5000`, so the session cookie is
first-party in development. If you host the API elsewhere, set
`VITE_API_URL` and add that origin to `FRONTEND_ORIGIN` / CORS in
`backend/config.py`.

### 3. Production build (optional)

```bash
cd frontend
npm run build      # outputs frontend/dist
npm run preview
```

---

## API summary

All endpoints are under `/api` and require a signed-in session except login.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/auth/login` | Sign in (`username`, `password`, `remember`) |
| POST | `/auth/logout` | Sign out |
| GET | `/auth/me` | Current user + preferences |
| PUT | `/auth/profile` | Update display name |
| PUT | `/auth/password` | Change password |
| PUT | `/auth/preferences` | Statement default + chart preference |
| GET | `/dashboard/summary` | Totals, recent transactions, monthly series |
| GET/POST | `/accounts` | List (with `q`, `type`) / create |
| GET/PUT/DELETE | `/accounts/<id>` | Read / update / delete (cascades transactions) |
| GET/POST | `/transactions` | List (filters) / create |
| GET/PUT/DELETE | `/transactions/<id>` | Details with balances / update / delete |
| GET | `/statements/preview?account_id&start_date&end_date` | Statement JSON |
| GET | `/statements/pdf?...` | Downloadable PDF |

Errors return `{ "error": "message", "fields": { ... } }`, which the UI maps
onto inline field errors and toasts.

---

## Balance logic

Money is handled with Python `Decimal` (two decimal places) and stored as
`DECIMAL(14,2)`. Nothing is calculated with floats.

```
closing balance = opening balance + total credits − total debits
credit: new balance = previous balance + amount
debit:  new balance = previous balance − amount
```

For a statement period:

1. Start from the account's opening balance.
2. Apply **every transaction dated before the start date** → period opening balance.
3. Apply transactions **inside the period in chronological order**, recording a
   running balance on each row.
4. Closing balance = period opening + period credits − period debits.

The same ordering rule (`transaction_date`, `created_at`, `transaction_id`) is
used for the transaction details page, so previous/updated balances always
match the statement.

---

## Database notes (SQLite → MySQL)

The schema in `backend/database/schema.sql` uses the same tables, columns,
keys and constraints you would use in MySQL. To move to MySQL:

- Replace `INTEGER PRIMARY KEY AUTOINCREMENT` with `INT AUTO_INCREMENT PRIMARY KEY`
- Replace `TEXT` with `VARCHAR(...)` / `DATETIME`
- Keep `DECIMAL(14,2)` for all money columns
- Swap `backend/database/db.py` for a MySQL connector (e.g. `mysql-connector-python`)
- Set `DATABASE_PATH`/connection settings through environment variables

Every query is parameterised, and every account/transaction lookup is scoped
by the signed-in `user_id`, so one user can never read another user's records.

---

## Security notes

- Passwords hashed with PBKDF2 (`werkzeug.security.generate_password_hash`)
- Sessions signed with `SECRET_KEY`; set a real secret in production
- Cookies are `HttpOnly` and `SameSite=Lax`
- Role checks on the server (`admin` writes, `analyst` read-only)
- No card numbers, CVV, bank passwords or real credentials are stored

---

## Testing checklist used

- Login with valid and invalid credentials; logout clears the session
- Accounts: create, edit, search, filter, delete with cascade
- Transactions: add credit and debit, edit, delete, filter by account/type/date
- Balance maths: ₹10,000 + ₹5,000 − ₹2,000 = ₹13,000 for the sample period
- Statement: opening/closing balances and running balance per row
- PDF: generated with the correct filename and all required fields
- Role restrictions: analyst receives HTTP 403 on write endpoints
- Unauthenticated requests to protected endpoints return HTTP 401
- Frontend production build passes

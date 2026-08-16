# 🥛 DoodhSync

**DoodhSync** is a production-ready Telegram-based milk tracking application designed to make daily milk record keeping simple, reliable, and accessible.

Users can record their daily milk quantity directly through Telegram and retrieve daily, historical, monthly, and custom date-range reports without needing a separate mobile or web application.

The project was built incrementally with a focus on **clean architecture, multi-user support, database persistence, automated testing, timezone-aware date handling, and production deployment**.

> **Current Version:** `v1.0.0`

---

## 🚀 Live Project

### Telegram Bot

**DoodhSync Bot:** [@DoodhSync_Bot](https://t.me/DoodhSync_Bot)

The production bot is deployed and uses a Telegram webhook to communicate with the backend.

### Production API

**Health Check:** https://doodhsync.onrender.com/health

### Production Health Check

The application exposes a health endpoint:

```text
GET /health
```

Expected response:

```json
{
  "status": "ok"
}
```

---

# ✨ Features

### 🥛 Milk Tracking

* Record daily milk quantity directly through Telegram.
* Accept quantities such as `3`, `2.5`, or `3.25` liters.
* Prevent duplicate milk records for the same user and date.
* Validate invalid, zero, and negative quantities.

### 📊 Reports

* Today's milk consumption
* Recent milk history
* Monthly milk reports
* Custom date-range reports
* Total milk quantity
* Daily averages and other report-level statistics

### 👥 Multi-User Support

* Each Telegram user has their own account and milk records.

* Users cannot access another user's milk data.

### 🤖 Telegram Bot

Supported commands include:

```text
/start
/help
/today
/history
/month
/range YYYY-MM-DD YYYY-MM-DD
```

Milk quantities can also be recorded simply by sending a number:

```text
3.25
```

### 🌐 Production Webhook

* The production bot uses a Telegram webhook instead of polling.

* Telegram sends updates to the deployed FastAPI application:

```text
Telegram
    │
    │ HTTPS POST
    ▼
FastAPI Webhook
    │
    ▼
Telegram Handlers
    │
    ▼
Application Services
    │
    ▼
SQLAlchemy
    │
    ▼
PostgreSQL
```

### 🗄️ Persistent Database

* Production data is stored in **PostgreSQL hosted on Neon**.

* Local development can use SQLite as a lightweight fallback.

### 🧪 Automated Testing

The project includes automated tests for:

* Services
* Repositories
* Telegram handlers
* Input validation
* Date-range validation
* Timezone configuration
* Database-related behavior

Current V1 test suite:

```text
42 passed
```

---

# 🏗️ Architecture

DoodhSync follows a layered backend architecture.

```text
                    ┌─────────────────┐
                    │     Telegram    │
                    │      User       │
                    └────────┬────────┘
                             │
                             │ Webhook
                             ▼
                    ┌─────────────────┐
                    │     FastAPI     │
                    │  Webhook Layer  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Telegram        │
                    │ Handlers        │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    Services     │
                    │ Business Logic  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Repositories   │
                    │  Data Access    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   SQLAlchemy    │
                    │       ORM       │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Neon PostgreSQL │
                    │   Production DB │
                    └─────────────────┘
```

This separation keeps Telegram-specific code, business logic, and database operations independent from each other.

---

# 🛠️ Technology Stack

## Backend

| Technology              | Purpose                                  |
| ----------------------- | ---------------------------------------- |
| **Python 3.11**         | Primary programming language             |
| **FastAPI**             | Web framework and webhook API            |
| **Uvicorn**             | ASGI server                              |
| **python-telegram-bot** | Telegram Bot API integration             |
| **SQLAlchemy**          | ORM and database interaction             |
| **Alembic**             | Database schema migrations               |
| **Pydantic Settings**   | Configuration and environment management |

## Database

| Technology     | Purpose                             |
| -------------- | ----------------------------------- |
| **PostgreSQL** | Production relational database      |
| **Neon**       | Serverless/cloud PostgreSQL hosting |
| **SQLite**     | Local development fallback          |
| **psycopg**    | PostgreSQL driver                   |

## Testing

| Technology         | Purpose                                |
| ------------------ | -------------------------------------- |
| **Pytest**         | Test framework                         |
| **pytest-asyncio** | Testing asynchronous Telegram handlers |

## Development & Deployment

| Technology            | Purpose                                      |
| --------------------- | -------------------------------------------- |
| **uv**                | Python dependency and environment management |
| **Git**               | Version control                              |
| **GitHub**            | Source code hosting                          |
| **Render**            | Production deployment                        |
| **Telegram Webhooks** | Production bot communication                 |

---

# 📁 Project Structure

```text
DoodhSync/
│
├── app/
│   │
│   ├── database/
│   │   ├── base.py
│   │   └── session.py
│   │
│   ├── models/
│   │   └── ...
│   │
│   ├── repositories/
│   │   └── ...
│   │
│   ├── services/
│   │   └── ...
│   │
│   ├── telegram/
│   │   ├── bot.py
│   │   └── handlers.py
│   │
│   ├── config.py
│   └── web.py
│
├── migrations/
│   ├── versions/
│   └── env.py
│
├── tests/
│   ├── test_milk_service.py
│   ├── test_repositories.py
│   ├── test_telegram_handlers.py
│   └── ...
│
├── .env.example
├── pyproject.toml
├── uv.lock
├── alembic.ini
└── README.md
```

---

# 🔄 Application Flow

When a user records milk:

```text
User sends:
    3.25
       │
       ▼
Telegram
       │
       ▼
Telegram Webhook
       │
       ▼
FastAPI
       │
       ▼
milk_quantity_handler()
       │
       ▼
Milk Service
       │
       ├── Validate quantity
       ├── Identify Telegram user
       ├── Check today's record
       └── Create record
       │
       ▼
Repository
       │
       ▼
SQLAlchemy
       │
       ▼
PostgreSQL
       │
       ▼
Response sent back to Telegram
```

---

# 🗃️ Database Design

The application uses a relational database with separate user and milk-record entities.

### Users

Stores Telegram users registered with the application.

Conceptually:

```text
users
├── id
├── telegram_user_id
├── ...
```

### Milk Records

Stores daily milk quantities.

```text
milk_records
├── id
├── user_id
├── date
├── quantity_liters
├── created_at
└── updated_at
```

The relationship is:

```text
User
  │
  │ 1
  │
  └───────────< Milk Records
                    *
```

This design allows the application to support multiple users while keeping their records isolated.

---

# 🌍 Timezone Handling

DoodhSync uses:

```text
Asia/Kolkata
```

as the default application timezone.

This is important because milk records are associated with calendar dates.

For example, a message received around midnight should be interpreted according to the application's configured timezone rather than blindly using the server's timezone.

The timezone is configurable through environment variables.

---

# 🔐 Configuration

DoodhSync uses environment variables for configuration.

Example `.env`:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=sqlite:///./doodhsync.db
TIMEZONE=Asia/Kolkata
```

Production uses PostgreSQL:

```env
DATABASE_URL=your_postgresql_connection_string
```

### Important

Secrets such as:

* Telegram bot tokens
* Database credentials
* API keys

are **not committed to GitHub**.

The repository only contains `.env.example` with placeholder values.

---

# 🗄️ Database Migrations

Alembic is used to manage database schema changes.

Apply migrations:

```bash
alembic upgrade head
```

Check the current migration:

```bash
alembic current
```

This allows the database schema to evolve safely as the application develops.

---

# 💻 Local Development

## Prerequisites

Install:

* Python 3.11
* Git
* uv
* Telegram account
* Telegram bot token

---

## 1. Clone the repository

```bash
git clone https://github.com/CodesbyHim/DoodhSync.git
cd DoodhSync
```

---

## 2. Install dependencies

```bash
uv sync
```

---

## 3. Configure environment variables

Create a `.env` file:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=sqlite:///./doodhsync.db
TIMEZONE=Asia/Kolkata
```

---

## 4. Run database migrations

```bash
alembic upgrade head
```

---

## 5. Start the application

Run FastAPI with Uvicorn:

```bash
uv run uvicorn app.web:app --host 0.0.0.0 --port 8000
```

The health endpoint will be available at:

```text
http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

---

# 🧪 Running Tests

Run the complete test suite:

```bash
python -m pytest -q
```

Current V1 status:

```text
42 passed
```

Tests can be expanded as new features are introduced.

---

# 🚀 Production Deployment

The V1 application is deployed using **Render**.

Production architecture:

```text
                    Internet
                       │
                       ▼
                 Telegram API
                       │
                       │ Webhook
                       ▼
              ┌─────────────────┐
              │     Render      │
              │                 │
              │    FastAPI      │
              │    Uvicorn      │
              └────────┬────────┘
                       │
                       ▼
                DoodhSync App
                       │
                       ▼
              ┌─────────────────┐
              │      Neon       │
              │   PostgreSQL    │
              └─────────────────┘
```

The production service requires:

```text
TELEGRAM_BOT_TOKEN
DATABASE_URL
TIMEZONE
```

---

# 🔗 Telegram Webhook

Production uses webhooks instead of Telegram polling.

The webhook endpoint is:

```text
https://doodhsync.onrender.com/telegram/webhook
```

Telegram is configured to send incoming bot updates to this endpoint.

Webhook status can be checked using Telegram's Bot API:

```text
getWebhookInfo
```

This architecture allows the bot to operate as part of the deployed web application without requiring a continuously running local polling process.

---

# 🧠 Engineering Decisions

## Why FastAPI?

FastAPI provides a lightweight and modern HTTP layer for the application and works well with asynchronous Python code.

It also gives DoodhSync a proper web layer, allowing future APIs and integrations to be added without redesigning the application.

## Why SQLAlchemy?

SQLAlchemy provides an abstraction between application code and the database.

This allows the application to work with SQLite during local development and PostgreSQL in production without rewriting the application's business logic.

## Why PostgreSQL?

SQLite is excellent for simple local development, but PostgreSQL is better suited for a deployed multi-user application.

Production DoodhSync therefore uses PostgreSQL through Neon.

## Why Alembic?

Database schemas change as applications evolve.

Alembic provides version-controlled database migrations so schema changes can be applied consistently across development and production environments.

## Why Telegram?

Telegram provides a simple interface that allows the application to be used without building and maintaining a separate mobile application.

This makes the first version extremely lightweight for end users.

## Why Webhooks?

The production application uses webhooks because the backend is already exposed through HTTPS.

Telegram can send updates directly to the deployed FastAPI endpoint, allowing the application to process messages without continuously polling Telegram.

---

# 🛡️ Error Handling

DoodhSync includes centralized Telegram error handling.

Unexpected exceptions during Telegram update processing are logged by the application rather than being silently ignored.

Input validation is also performed before creating database records.

Examples of invalid input include:

```text
abc
0
-2
```

These inputs are rejected instead of creating invalid milk records.

---

# 👥 Multi-User Design

DoodhSync was designed as a multi-user application from V1.

Each Telegram user is identified independently and their milk records are associated with their user account.

This prevents one user from retrieving another user's records.

The architecture therefore supports expanding the application beyond a single-family/single-user use case in future versions.

---

# 📈 Versioning Strategy

DoodhSync is developed incrementally.

The initial production release is:

```text
v1.0.0
```

Future versions will extend the existing system rather than replacing it.

Planned direction:

```text
V1
│
├── Telegram milk tracking
├── Reports
├── Multi-user support
├── PostgreSQL
└── Production deployment
        │
        ▼
V2
│
├── Backend improvements
├── Better reporting
├── Additional features
└── Operational improvements
        │
        ▼
V3
│
├── React dashboard
├── Visual analytics
├── Charts
└── Web-based management
```

---

# 🗺️ Roadmap

### V1 — Completed ✅

* [x] Telegram bot
* [x] Daily milk recording
* [x] Duplicate record prevention
* [x] Daily reports
* [x] History
* [x] Monthly reports
* [x] Custom date-range reports
* [x] Input validation
* [x] Multi-user support
* [x] Timezone handling
* [x] SQLAlchemy database layer
* [x] Alembic migrations
* [x] PostgreSQL integration
* [x] Neon production database
* [x] FastAPI webhook
* [x] Centralized error handling
* [x] Automated test suite
* [x] Production deployment

### V2 — Planned

* [ ] Improved reporting
* [ ] More flexible record management
* [ ] Better operational monitoring
* [ ] Additional Telegram features
* [ ] Improved analytics

### V3 — Planned

* [ ] React web dashboard
* [ ] Visual analytics
* [ ] Charts and graphs
* [ ] Monthly/yearly dashboards
* [ ] Web-based record management

---

# 📊 Current V1 Status

| Area                | Status       |
| ------------------- | ------------ |
| Telegram Bot        | ✅ Production |
| Milk Tracking       | ✅ Complete   |
| Reports             | ✅ Complete   |
| Multi-user Support  | ✅ Complete   |
| PostgreSQL          | ✅ Production |
| Neon Database       | ✅ Production |
| FastAPI             | ✅ Production |
| Telegram Webhook    | ✅ Production |
| Database Migrations | ✅ Complete   |
| Automated Tests     | ✅ 42 passing |
| Deployment          | ✅ Complete   |
| Documentation       | ✅ Complete   |

---

# 👨‍💻 Author

**Himanshu Khakre**

B.Tech — Artificial Intelligence & Machine Learning

GitHub: [CodesbyHim](https://github.com/CodesbyHim)

---

# 📄 License

This project currently does not include a separate open-source license.

If the project is later released as an open-source project, an appropriate license such as MIT can be added.

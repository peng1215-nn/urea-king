# UREAKING

UREAKING is a role-based group management platform built with FastAPI, PostgreSQL, SQLAlchemy, and vanilla JavaScript.
The system is designed around group-based ecosystem management, invitation-code registration, and multi-role permission control.

The project supports administrators, organizers, and regular users, and includes features such as account management, invitation systems, avatar uploading, internationalization (i18n), and account status control.

---

# Features

## Authentication System

* User registration and login
* Session-based authentication
* Password hashing with Passlib
* Invitation-code registration mechanism
* Multi-group account support

## Role-Based Permission System

* Admin
* Organizer
* User

Different roles have different permissions and accessible pages.

## User Management

* Search users
* View user details
* Modify user roles
* Reset user passwords
* Disable / enable accounts
* Restrict admin account modification

## Invitation Code System

* Generate invitation codes
* Bind invitation codes to groups and roles
* Prevent unauthorized registration

## Account Security

* Password hashing
* Session authentication
* Account disable/enable control
* Environment variable based secret management

## Avatar Upload System

* Cloudinary image hosting integration
* User avatar upload and update

## Internationalization (i18n)

* Chinese / English language switching
* Dynamic frontend translation system
* Shared language state across pages

## Database Migration

* Alembic migration support
* PostgreSQL schema version management

---

# Tech Stack

## Backend

* FastAPI
* SQLAlchemy
* PostgreSQL
* Alembic
* Passlib

## Frontend

* HTML
* CSS
* Vanilla JavaScript

## Deployment & Services

* Render
* Cloudinary

---

# Project Structure

```text
project/
│
├── root/                 # 主域名首页（urea-king.com）
│   ├── routes/           #   路由（GET /）
│   ├── services/         #   首页所需配置（POKER_URL / ADMIN_CONTACT_EMAIL）
│   ├── templates/        #   index.html
│   └── static/           #   css / js（挂载在 /static/root）
│
├── poker/                # Poker 子系统（poker.urea-king.com）
│   ├── routes/
│   ├── services/
│   ├── templates/
│   └── static/           #   js / css / images（挂载在 /static）
│
├── migrations/
├── utils/
├── database.py
├── main.py
└── requirements.txt
```

---

# Database Design

Main tables:

* users
* groups
* user_group_roles
* invitation_codes
* audit_logs

The system supports many-to-many relationships between users and groups with role isolation.

---

# Security Design

The project uses several security mechanisms:

* Password hashing (PBKDF2-SHA256) with an 8–128 character policy
* Signed session cookies (`HttpOnly`, `SameSite=Lax`, `Secure` in production); the app refuses to start in production without `SESSION_SECRET_KEY`
* Login, registration and invite-code rate limiting
* Per-request session validation: disabled accounts and removed roles lose access within 15 seconds
* CSRF protection via `Origin` / `Referer` checks on state-changing requests
* Security headers: Content-Security-Policy, `X-Frame-Options`, `nosniff`, Referrer-Policy, HSTS in production
* Output escaping for all server data rendered into HTML, plus server-side input validation
* Generic error responses to clients, with full details written to structured logs
* Avatar uploads validated by file signature and size
* Random one-time temporary passwords for admin password resets
* Role-based permission checks, group-level data isolation and an audit log

Sensitive values such as:

* DATABASE_URL
* SESSION_SECRET_KEY
* CLOUDINARY_API_KEY
* CLOUDINARY_API_SECRET

are managed through environment variables and are not stored in the repository. See `.env.example`.

---

# Internationalization

The project includes a custom frontend i18n system:

* `language.js`
* page-specific translation files
* dynamic text translation
* persistent language state using localStorage

Currently supported languages:

* Chinese
* English

---

# Deployment

The project is deployed using:

* Render (web service)
* PostgreSQL
* Cloudinary (avatar storage)

Environment variables are configured through the deployment platform. Health check endpoints: `/healthz` (liveness) and `/readyz` (database readiness).

---

# Development

Local setup, migrations, tests, CI and deployment notes are documented in [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

---

# Future Improvements

Planned future features:

* Organizer dashboard
* System announcement management
* Audit log visualization
* Permission granularity refinement
* WebSocket real-time notifications
* Better frontend component abstraction
* API documentation

---

# Author

Jiawei Peng

Master's Student in Electrical and Computer Engineering
The Ohio State University

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
├── routes/
├── services/
├── templates/
├── static/
│   ├── js/
│   ├── css/
│   └── images/
│
├── migrations/
├── models.py
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

* Password hashing
* Session authentication
* Environment variable isolation
* Role-based permission checks
* Admin operation restrictions
* Account status control (`is_active`)

Sensitive values such as:

* DATABASE_URL
* SESSION_SECRET_KEY
* CLOUDINARY_API_KEY
* CLOUDINARY_API_SECRET

are managed through environment variables and are not stored in the repository.

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

* Render (backend deployment)
* PostgreSQL
* Cloudinary

Environment variables are configured through the deployment platform.

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

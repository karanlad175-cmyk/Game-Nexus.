# GAME NEXUS — Backend

The GAME NEXUS backend is a Python **FastAPI** application connected to **PostgreSQL**. It provides the API and server-side functionality used by the GAME NEXUS website, including user authentication, article/content operations, and administrative features.

The frontend files are maintained in the project root and are served by the FastAPI application in the local development setup.

## Features

- Email/password registration and login.
- Password hashing and authenticated sessions using secure cookies.
- Google OAuth sign-in (requires credentials configured locally).
- Password-reset email workflow.
- PostgreSQL persistence through SQLAlchemy.
- Blog post and article APIs.
- Comment moderation.
- Newsletter subscriptions and contact-message handling.
- Admin-only access to management endpoints.
- Admin operations for creating, editing, publishing, unpublishing, and deleting posts.
- Admin tools for comments, users, newsletter subscribers, and contact messages.
- Dashboard statistics and article-view analytics.

> GAME NEXUS is currently intended as a locally demonstrated portfolio project. It is not presented as a production-hardened public service.

## Technology

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- HTML, CSS, JavaScript, and Bootstrap frontend

## Project structure

```text
Game-Nexus/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   ├── admin.py
│   │   │   ├── auth.py
│   │   │   ├── content.py
│   │   │   └── payments.py
│   │   ├── services/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── email_utils.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── security.py
│   ├── requirements.txt
│   └── .env.example
├── images/
├── index.html
├── blog.html
├── post.html
├── login.html
├── profile.html
├── admin.html
└── ...
```

## Local setup

### 1. Requirements

- Python version supported by the dependencies in `requirements.txt`.
- PostgreSQL installed and running.
- Git (to clone the repository).

### 2. Clone the project

```bash
git clone https://github.com/karanlad175-cmyk/Game-Nexus.git
cd Game-Nexus
```

### 3. Create a virtual environment

Open PowerShell in the project directory:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure environment variables

Copy the example file:

```powershell
Copy-Item .env.example .env
```

Edit `backend/.env` and provide your own local configuration values. In particular, configure:

- `DATABASE_URL` — connection URL for your local PostgreSQL database.
- `JWT_SECRET_KEY` — a strong, randomly generated secret.
- `SESSION_SECRET` — a separate strong, randomly generated secret.
- Google OAuth credentials if you want to enable Google sign-in.
- Email/SMTP settings required by the password-reset workflow.

Use the exact variable names expected by `app/config.py` and the `.env.example` template. Never commit your real `.env` file or share its contents.

### 6. Create the local database

Create a PostgreSQL database named `gamenexus` (or use the database name configured in `DATABASE_URL`). Make sure the PostgreSQL server is running and the configured database user has access.

### 7. Start the application

From the `backend` directory:

```powershell
uvicorn app.main:app --reload
```

Open the local website:

```text
http://127.0.0.1:8000/
```

The FastAPI interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

If you configured a different host or port, use that address instead.

## Authentication and integrations

### Email/password authentication

The backend supports registration, login, logout, and retrieval of the currently authenticated user. Passwords are hashed; authentication is handled server-side.

### Google OAuth

Google sign-in requires an OAuth client created in Google Cloud Console. Configure the client ID, client secret, and redirect URI using the environment-variable names in `.env.example` and `app/config.py`.

For local development, the redirect URI must match the URI configured in Google Cloud Console exactly. Do not commit OAuth credentials.

### Password reset email

The password-reset workflow requires valid email/SMTP configuration in the local environment. Email credentials must remain in `.env` and must never be committed.

## Admin dashboard

The admin dashboard uses backend authorization checks. Admin functionality includes:

- Post creation, editing, publishing, unpublishing, and deletion.
- Comment approval and deletion.
- User search and management views.
- Newsletter subscriber listing.
- Contact-message listing and deletion.
- Dashboard counts, registration statistics, and article-view analytics.

Keep administrator credentials private. Do not rely on hiding a frontend link as a security measure; the backend must enforce admin authorization.

## Database notes

The application uses PostgreSQL through SQLAlchemy. The current development setup creates tables on application startup using SQLAlchemy metadata. For a production deployment or long-term schema evolution, a migration workflow such as Alembic should be introduced and tested.

Use your own local database. Do not commit database dumps, database files, or credentials.

## Payments

Razorpay subscriptions are **not part of the current project scope**. The repository may retain earlier payment-related scaffold files, but the website is not being deployed with an active subscription flow. Do not configure live payment credentials for this portfolio demonstration.

## Security reminders

- Keep `.env` private; only commit `.env.example` with placeholder values.
- Never commit passwords, API keys, OAuth secrets, SMTP credentials, private keys, or database backups.
- Use test credentials for third-party integrations during development.
- Keep admin accounts secure.
- A local development setup is not automatically production-ready. Public hosting requires a separate security, configuration, testing, and deployment review.

## Tests

The backend folder contains Python test files for selected project utilities. Run the tests from the `backend` directory with:

```powershell
python -m pytest
```

## Project

**GAME NEXUS** — a full-stack gaming news and community blog platform.

Frontend: HTML, CSS, JavaScript, Bootstrap  
Backend: Python, FastAPI  
Database: PostgreSQL

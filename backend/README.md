# GAME NEXUS — FastAPI backend starter

This package includes your original frontend under `../frontend_source/karan/` and a starter backend. The API is wired to PostgreSQL, email/password auth, Google OAuth, blog/content endpoints, and Razorpay subscription endpoints. It is a development foundation, not yet a production-ready deployment.

## 1. Requirements
- Python 3.11+
- PostgreSQL installed and running
- Google OAuth credentials only if you want Google login enabled
- Razorpay test credentials and test plan IDs for subscription testing

## 2. Create database
In `psql` or pgAdmin, create a database named `gamenexus`:
```sql
CREATE DATABASE gamenexus;
```
Use the password for your own local PostgreSQL user in `DATABASE_URL`.

## 3. Install and configure
Windows PowerShell:
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```
Edit `.env`. Generate secrets in PowerShell:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```
Run that twice and use the values for `JWT_SECRET_KEY` and `SESSION_SECRET`. Do not commit `.env`.

## 4. Google OAuth setup
In Google Cloud Console, configure an OAuth consent screen and create a Web application OAuth client. Add this authorized redirect URI:
`http://127.0.0.1:8000/api/auth/google/callback`
Put the client ID and secret in `.env`. Google login is disabled until these are configured. Production must use HTTPS and the exact production callback URL.

## 5. Razorpay setup
Use TEST mode first. Create monthly and yearly subscription plans in the Razorpay dashboard and copy their plan IDs to `.env`. Set test API keys and configure a webhook pointing to `/api/payments/webhook`; copy the webhook secret into `.env`. Do not put Razorpay secret keys in frontend JavaScript.

## 6. Run
From the `backend` directory:
```powershell
uvicorn app.main:app --reload
```
Open:
- Website: `http://127.0.0.1:8000/index.html`
- API docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/api/health`

The database tables are created on first run for convenience. Before production, add Alembic migrations and a controlled admin bootstrap.

## Implemented endpoints
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET /api/auth/google/start`
- `GET /api/auth/google/callback`
- `GET /api/posts`
- `GET /api/posts/{slug}` (premium body protected by subscription status)
- `GET/POST /api/posts/{slug}/comments`
- `POST /api/newsletter`
- `POST /api/contact`
- `GET /api/payments/config`
- `POST /api/payments/subscriptions`
- `POST /api/payments/verify`
- `GET /api/payments/me`
- `POST /api/payments/webhook`

## Important notes before production
1. The current frontend pages are preserved as supplied. Login/register form wiring, Google button wiring, pricing UI, admin authoring UI, and article/comment/newsletter/contact JavaScript integration still need to be connected and tested against these endpoints.
2. The `login.html` currently simulates successful login/registration in browser JavaScript. Until frontend integration is completed, it does not call the API.
3. The `is_admin` flag exists but an admin bootstrap and protected admin endpoints have not been added. Do not expose admin functions publicly.
4. Configure HTTPS (`COOKIE_SECURE=true`) in production, secure secrets, backups, rate limiting, logging, email verification/password reset, CSRF review, and monitoring before launch.
5. A verified checkout signature alone does not guarantee the subscription is active. The webhook is used to update subscription lifecycle state; verify your Razorpay event configuration and reconcile statuses before granting premium access in production.
6. The app uses `create_all` only for development. Use Alembic migrations for ongoing schema changes.
7. Pricing amounts are configured in Razorpay plan definitions, not hard-coded in the frontend or backend.

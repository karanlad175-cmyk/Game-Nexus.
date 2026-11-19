# GAME NEXUS

**A full-stack gaming news and community blog platform** built with HTML, CSS, JavaScript, Bootstrap, FastAPI, and PostgreSQL.

GAME NEXUS brings gaming articles, user accounts, and content administration together in one web application. The project includes a responsive frontend, a Python REST API, database-backed features, and an admin dashboard.

> **Project status:** Developed and tested locally. This repository contains the source code; the application is not currently hosted as a public live website.

## Overview

GAME NEXUS is designed as a gaming-focused publication where visitors can explore articles and registered users can interact with the platform. Administrative tools provide a central place to manage content and review community activity.

## Features

### Website and articles
- Responsive website built with HTML, CSS, JavaScript, and Bootstrap.
- Home, blog, article, about, and contact pages.
- Gaming news and editorial article pages.
- Article browsing and individual article views.

### User accounts and authentication
- Email and password registration and login.
- Password hashing and authenticated user sessions.
- Google OAuth sign-in integration.
- Password-reset flow using email links.
- User profile page and logout functionality.
- Admin-only access controls for administrative features.

### Admin dashboard
- Create, edit, publish, unpublish, and delete articles.
- Review, approve, and delete comments.
- Search and manage registered users.
- View newsletter subscribers and contact messages.
- Dashboard statistics and article-view analytics.

### Backend and data
- FastAPI application with organized API routers.
- PostgreSQL database integration using SQLAlchemy.
- Authentication and authorization dependencies.
- API endpoints for content and administrative operations.
- Configuration through environment variables.

## Technology stack

| Area | Technologies |
|---|---|
| Frontend | HTML5, CSS3, JavaScript, Bootstrap |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Authentication | Password hashing, session/cookie-based authentication, Google OAuth |
| Email | Email-based password-reset workflow |
| Version control | Git and GitHub |

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
├── about.html
├── contact.html
└── README.md
```

The repository also contains individual article HTML pages and supporting image assets.

## Run locally

### 1. Clone the repository

```bash
git clone https://github.com/karanlad175-cmyk/Game-Nexus.git
cd Game-Nexus
```

### 2. Create and activate a Python virtual environment

From the project root:

```bash
cd backend
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example configuration:

```powershell
Copy-Item .env.example .env
```

Open `backend/.env` and set the values for your local environment. At minimum, configure:

- `DATABASE_URL` — your PostgreSQL connection string.
- `JWT_SECRET_KEY` — a long, randomly generated secret.
- `SESSION_SECRET` — another long, randomly generated secret.
- Google OAuth credentials and email settings if you want to use those integrations.

Use the variable names and any additional required settings documented in `backend/README.md` and `backend/app/config.py`. Keep `.env` private; never commit real credentials.

### 5. Create the PostgreSQL database

Create a local PostgreSQL database named `gamenexus` (or use the database name in your `DATABASE_URL`). Ensure PostgreSQL is running and that the configured user has permission to connect to the database.

### 6. Start the FastAPI application

From the `backend` directory, run:

```bash
uvicorn app.main:app --reload
```

Open the local application URL configured by the project. The API documentation is normally available at:

```text
http://127.0.0.1:8000/docs
```

If the frontend is served by the FastAPI application, open:

```text
http://127.0.0.1:8000/
```

If your local configuration uses a different port or frontend serving setup, use that configured address.

## Configuration and security

- Do not commit `.env` files, database dumps, passwords, OAuth client secrets, email credentials, or private keys.
- `.env.example` is a template; replace placeholders only in your local `.env`.
- Use test credentials for any third-party integration during development.
- Keep admin credentials private.
- This project is presented as a local development/portfolio project and has not been represented as a production-hardened public service.

## Screenshots

Add screenshots of the running application here to help visitors understand the project.

Suggested screenshots:
- Home page
- Blog/article listing
- Individual article page
- Login and profile pages
- Admin dashboard

For example, create a `screenshots/` folder and add image files, then embed them using:

```markdown
![GAME NEXUS home page](screenshots/home.png)
```

## Future improvements

Potential areas for further development include:
- Automated tests and continuous integration.
- More detailed setup and API documentation.
- Accessibility and performance improvements.
- A hosted demo environment with production security review.

## Author

**Karan Lad**

- GitHub: [@karanlad175-cmyk](https://github.com/karanlad175-cmyk)

---

If you find an issue or have a suggestion, feel free to open an issue in this repository.

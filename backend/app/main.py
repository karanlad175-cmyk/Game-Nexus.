
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import Base, engine
from app import models
from app.routers import auth, content, payments, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Keep automatic table creation for local development.
    # Use database migrations for production deployments.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site="lax",
    https_only=settings.cookie_secure,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Requested-With"],
)


# Register existing API routers.
app.include_router(auth.router)
app.include_router(content.router)
app.include_router(payments.router)
app.include_router(admin.router)


@app.get("/api")
def api_root():
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "health": "/api/health",
    }


class SecureStaticFiles(StaticFiles):
    """Prevent public access to backend and internal project files."""

    BLOCKED_DIRECTORIES = {
        "backend",
        ".vscode",
    }

    BLOCKED_EXTENSIONS = {
        ".py",
        ".pyc",
        ".env",
        ".ini",
        ".toml",
        ".yaml",
        ".yml",
        ".log",
        ".db",
        ".sqlite",
        ".pem",
        ".key",
        ".crt",
        ".conf",
        ".md",
    }

    async def get_response(self, path: str, scope):
        parts = Path(path).parts

        # Block hidden files and internal directories.
        for part in parts:
            if part.startswith("."):
                raise HTTPException(status_code=404)

            if part.lower() in self.BLOCKED_DIRECTORIES:
                raise HTTPException(status_code=404)

        # Block sensitive file extensions.
        suffix = Path(path).suffix.lower()

        if suffix in self.BLOCKED_EXTENSIONS:
            raise HTTPException(status_code=404)

        return await super().get_response(path, scope)


# Keep the existing frontend files in the project root.
FRONTEND_DIR = Path(__file__).resolve().parents[2]

if FRONTEND_DIR.exists():
    app.mount(
        "/",
        SecureStaticFiles(
            directory=str(FRONTEND_DIR),
            html=True,
        ),
        name="frontend",
    )

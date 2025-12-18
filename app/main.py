"""Main FastAPI application - Battle-D Web App."""
import logging
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from app.config import settings
from app.exceptions import ValidationError
from app.routers import auth, admin, dancers, tournaments, registration, battles, dashboard, event
from app.dependencies import set_email_service
from app.services.email.factory import create_email_provider
from app.services.email.service import EmailService
from app.logging_config import setup_logging
from app.utils.flash import add_flash_message

# Initialize logging
setup_logging(level="INFO" if not settings.DEBUG else "DEBUG")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events (startup and shutdown)."""
    # Startup
    logger.info("Starting Battle-D application")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Base URL: {settings.BASE_URL}")

    provider = create_email_provider()
    email_service = EmailService(provider)
    set_email_service(email_service)
    logger.info(f"Email service initialized with {type(provider).__name__}")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Battle-D application")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Add SessionMiddleware for flash messages
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.FLASH_SESSION_COOKIE_NAME,  # Use separate cookie for flash messages
    max_age=settings.SESSION_MAX_AGE_SECONDS,
    same_site="lax",
    https_only=not settings.DEBUG,
)

# Templates
templates = Jinja2Templates(directory="app/templates")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# Global exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 page."""
    return templates.TemplateResponse(
        request=request,
        name="errors/404.html",
        context={"request": request},
        status_code=404,
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    """Custom 500 page with error tracking ID."""
    error_id = str(uuid.uuid4())[:8]
    logger.error(f"500 error [{error_id}]: {exc}", exc_info=True)
    return templates.TemplateResponse(
        request=request,
        name="errors/500.html",
        context={
            "request": request,
            "error_id": error_id,
        },
        status_code=500,
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle uncaught ValidationError (fallback for errors not caught in routers)."""
    # Add first error as flash message
    error_message = exc.errors[0] if exc.errors else "Validation error occurred"
    add_flash_message(request, error_message, "error")

    # Redirect back to the same page
    return RedirectResponse(url=str(request.url.path), status_code=303)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with beautiful error pages for browser requests."""
    # Check if browser request (expects HTML)
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        # Map status codes to templates
        template_map = {
            401: "errors/401.html",
            403: "errors/403.html",
            404: "errors/404.html",
            500: "errors/500.html",
        }

        template = template_map.get(exc.status_code, "errors/500.html")

        return templates.TemplateResponse(
            request=request,
            name=template,
            context={
                "request": request,
                "status_code": exc.status_code,
                "detail": exc.detail,
            },
            status_code=exc.status_code,
        )

    # API/HTMX request - return JSON
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


# Include routers
# Dashboard router handles / and /overview
app.include_router(dashboard.router)
app.include_router(auth.router)
# NOTE: phases.router removed - phase management consolidated into Event Mode
# See: FEATURE_SPEC_2024-12-18_SCREEN-CONSOLIDATION.md
app.include_router(admin.router)
app.include_router(dancers.router)
app.include_router(tournaments.router)
app.include_router(registration.router)
app.include_router(battles.router)
app.include_router(event.router)


# Legacy redirect: /dashboard -> /overview
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_redirect(request: Request):
    """Redirect old /dashboard route to /overview."""
    return RedirectResponse(url="/overview", status_code=301)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": settings.APP_NAME}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

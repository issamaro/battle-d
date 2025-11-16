"""Main FastAPI application - Battle-D Web App."""
from typing import Optional
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config import settings
from app.routers import auth, phases, admin, dancers
from app.dependencies import get_current_user, require_auth, CurrentUser, set_email_service
from app.services.email.factory import create_email_provider
from app.services.email.service import EmailService

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

# Templates
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    provider = create_email_provider()
    email_service = EmailService(provider)
    set_email_service(email_service)
    print(f"Email service initialized with {type(provider).__name__}")


# Include routers
app.include_router(auth.router)
app.include_router(phases.router)
app.include_router(admin.router)
app.include_router(dancers.router)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Redirect to login page."""
    return RedirectResponse(url="/auth/login")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
):
    """Main dashboard - role-specific view."""
    user = require_auth(current_user)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "current_user": user,
        },
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": settings.APP_NAME}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

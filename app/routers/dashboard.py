"""Dashboard routes - redirects to tournaments (dashboard removed)."""
from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["dashboard"])


@router.get("/")
async def root():
    """Root route redirects to tournaments."""
    return RedirectResponse(url="/tournaments", status_code=302)


@router.get("/overview")
async def overview():
    """Redirect to tournaments list (dashboard removed)."""
    return RedirectResponse(url="/tournaments", status_code=302)

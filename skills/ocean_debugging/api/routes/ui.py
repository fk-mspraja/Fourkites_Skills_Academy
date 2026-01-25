"""UI routes for interactive testing"""

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

# Get the static files directory (api/static/)
STATIC_DIR = Path(__file__).parent.parent / "static"


@router.get("/", include_in_schema=False)
async def root():
    """Serve the interactive testing page"""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    # Fall back to investigation.html
    return FileResponse(STATIC_DIR / "investigation.html")


@router.get("/ui", include_in_schema=False)
async def ui():
    """Serve the interactive testing page"""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return FileResponse(STATIC_DIR / "investigation.html")


@router.get("/investigation", include_in_schema=False)
async def investigation():
    """Serve the hypothesis-driven investigation UI"""
    return FileResponse(STATIC_DIR / "investigation.html")

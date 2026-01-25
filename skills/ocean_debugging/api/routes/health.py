"""Health check endpoint"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health")
async def health():
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "auto-rca-api",
            "version": "2.0.0"
        },
        status_code=200
    )

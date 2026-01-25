"""FastAPI main application for Auto-RCA API"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging

from core.utils.logging import setup_logging
from api.routes import health, config, investigate, ui

app = FastAPI(
    title="FourKites Auto-RCA API",
    description="Multi-Mode Root Cause Analysis Platform",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("🚀 Auto-RCA API starting up...")
    logger.info("📊 Framework: Custom asyncio (no LangChain)")
    logger.info("🤖 LLM: Claude Sonnet 4.5 + Azure GPT-4o")


# Health check log suppression middleware
@app.middleware("http")
async def suppress_health_logs(request: Request, call_next):
    """Suppress access logs for health check endpoint"""
    if request.url.path == "/health":
        access_logger = logging.getLogger("uvicorn.access")
        original = access_logger.level
        access_logger.setLevel(logging.WARNING)
        try:
            response = await call_next(request)
            return response
        finally:
            access_logger.setLevel(original)
    return await call_next(request)


# Include routers
app.include_router(ui.router, tags=["ui"])  # Serve UI first (root path)
app.include_router(health.router, tags=["health"])
app.include_router(config.router, prefix="/api/v1/config", tags=["config"])
app.include_router(investigate.router, prefix="/api/v1", tags=["investigate"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )

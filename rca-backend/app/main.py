"""
FastAPI Main Application
Multi-Agent RCA Platform Backend
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import config
from app.api import rca

# Configure logging
logging.basicConfig(
    level=logging.INFO if not config.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    logger.info("Starting RCA Backend...")
    logger.info(f"Environment: {'DEBUG' if config.DEBUG else 'PRODUCTION'}")
    logger.info(f"LLM Provider: {config.LLM_PROVIDER}")
    logger.info(f"Tracking API: {config.TRACKING_API_BASE_URL}")
    logger.info(f"DataHub API: {config.DATAHUB_API_BASE_URL}")

    yield

    # Shutdown
    logger.info("Shutting down RCA Backend...")


# Create FastAPI app
app = FastAPI(
    title="Multi-Agent RCA Platform",
    description="Root Cause Analysis powered by LangGraph multi-agent orchestration",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(rca.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Multi-Agent RCA Platform",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "rca-backend",
        "llm_provider": config.LLM_PROVIDER
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.DEBUG
    )

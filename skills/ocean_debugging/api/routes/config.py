"""Configuration and feature flags endpoint"""

from fastapi import APIRouter
from core.utils.config import config

router = APIRouter()


@router.get("/features")
async def get_features():
    """Get frontend feature flags"""
    return {
        "auto_rca_enabled": config.ENABLE_AUTO_RCA,
        "modes": ["ocean"],  # Will add rail, air, otr, yard in Phase 4
        "llm_provider": config.LLM_PROVIDER,
        "llm_model": config.CLAUDE_MODEL if config.LLM_PROVIDER == "anthropic" else config.AZURE_OPENAI_DEPLOYMENT_NAME
    }

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel, Field
from src.services.research import ResearchService
from src.core.exceptions import ResearchError
from src.api.models.research import ResearchRequest
from src.core.config import get_settings

router = APIRouter()

@router.post("/research")
async def research_topic(request: ResearchRequest, service: ResearchService = Depends()):
    try:
        service = ResearchService()
        return await service.research_topic_from_request(request)
    except ResearchError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/search-config")
async def debug_search_config():
    """Debug endpoint to check search configuration"""
    settings = get_settings()
    return {
        "google_api_configured": bool(settings.GOOGLE_API_KEY and settings.GOOGLE_CSE_ID),
        "google_cse_id_length": len(settings.GOOGLE_CSE_ID) if settings.GOOGLE_CSE_ID else 0,
        "google_api_key_length": len(settings.GOOGLE_API_KEY) if settings.GOOGLE_API_KEY else 0,
        "serpapi_configured": bool(settings.SERPAPI_API_KEY),
        "default_provider": settings.DEFAULT_SEARCH_PROVIDER
    } 
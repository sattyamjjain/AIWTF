from fastapi import APIRouter, Depends, HTTPException
from src.api.models.research import ResearchRequest, ResearchResponse
from src.services.research import ResearchService
from src.core.config import get_settings
import logging
from fastapi import status

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/research",
    response_model=ResearchResponse,
    summary="Conduct research on a topic",
    description="Performs AI-powered research on the given topic"
)
async def research_topic(
    request: ResearchRequest,
    settings = Depends(get_settings),
    research_service: ResearchService = Depends()
) -> ResearchResponse:
    """Research endpoint"""
    try:
        return await research_service.research_topic(request)
    except Exception as e:
        logger.error(f"Research failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 
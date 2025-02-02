from src.innovations.research.agent import ResearchAgent
from src.api.models.research import ResearchRequest, ResearchResponse
from src.core.config import get_settings
from typing import Dict, Any
import logging
import os

logger = logging.getLogger(__name__)

class ResearchService:
    """Service for handling research operations"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Verify environment variables
        if not os.getenv('SERPAPI_API_KEY'):
            logger.error("SERPAPI_API_KEY not found in environment")
            raise ValueError("SERPAPI_API_KEY environment variable not set")
        
        if not os.getenv('OPENAI_API_KEY'):
            logger.error("OPENAI_API_KEY not found in environment")
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.agent = ResearchAgent()
    
    async def research_topic(self, request: ResearchRequest) -> ResearchResponse:
        """Conduct research on a topic"""
        try:
            result = await self.agent.research_topic(
                topic=request.topic,
                depth=request.depth,
                max_sources=request.max_sources
            )
            
            # Validate the response structure
            if not isinstance(result, dict):
                raise ValueError("Invalid response format from research agent")
            
            # Convert to response model
            return ResearchResponse(**result)
            
        except Exception as e:
            logger.error(f"Research failed: {str(e)}", exc_info=True)
            raise  # Re-raise the original exception 
from typing import List, Dict, Optional, Any
from src.innovations.research.agent import ResearchAgent
from src.agents.tools.search_providers import get_search_provider
from src.api.models.research import ResearchRequest, ResearchResponse, ResearchSource, ResearchMetadata
from src.core.config import get_settings
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class ResearchService:
    """Service for handling research operations"""
    
    def __init__(self):
        """Initialize the research service"""
        settings = get_settings()
        if not settings.GOOGLE_API_KEY or not settings.GOOGLE_CSE_ID:
            logger.warning("Google Search credentials not configured. Some features may be limited.")
        
        self.default_provider = settings.DEFAULT_SEARCH_PROVIDER
        self.agent = ResearchAgent(
            search_provider=self.default_provider,
            api_key=settings.GOOGLE_API_KEY,
            cx=settings.GOOGLE_CSE_ID
        )
    
    async def research_topic(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Conduct research on a topic"""
        try:
            return await self.agent.research(query, num_results)
        except Exception as e:
            logger.error(f"Research failed: {str(e)}")
            raise

    async def research_topic_from_request(self, request: ResearchRequest) -> ResearchResponse:
        """Process a research request"""
        try:
            result = await self.agent.research_topic(
                topic=request.topic,
                depth=request.depth,
                max_sources=request.max_sources
            )
            
            # Transform sources to match the model
            sources = [
                ResearchSource(title=s["title"], url=s["url"]) 
                for s in result.get("sources", [])
            ]
            
            # Create metadata
            metadata = ResearchMetadata(
                depth=result["metadata"]["depth"],
                source_count=result["metadata"]["source_count"],
                completion_time=datetime.fromisoformat(result["metadata"]["completion_time"]),
                duration=result["metadata"]["duration"],
                errors=result["metadata"]["errors"]
            )
            
            return ResearchResponse(
                topic=result["topic"],
                summary=result["summary"],
                sources=sources,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Research failed: {str(e)}", exc_info=True)
            raise 
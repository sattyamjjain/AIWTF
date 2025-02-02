import pytest
from unittest.mock import patch, AsyncMock
from src.services.research import ResearchService
from src.api.models.research import ResearchRequest, ResearchResponse

class TestResearchService:
    """Test cases for ResearchService"""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_research_service_success(self, MOCK_RESEARCH_REQUEST, MOCK_RESEARCH_RESPONSE):
        """Test successful research service"""
        request = ResearchRequest(**MOCK_RESEARCH_REQUEST)
        
        with patch('src.services.research.ResearchAgent') as MockAgent:
            mock_instance = AsyncMock()
            mock_instance.research_topic.return_value = MOCK_RESEARCH_RESPONSE
            MockAgent.return_value = mock_instance
            
            service = ResearchService()
            result = await service.research_topic_from_request(request)
            
            assert isinstance(result, ResearchResponse)
            assert result.topic == MOCK_RESEARCH_REQUEST["topic"]
            assert result.summary == MOCK_RESEARCH_RESPONSE["summary"]
            assert len(result.sources) == len(MOCK_RESEARCH_RESPONSE["sources"])
            assert result.metadata.depth == MOCK_RESEARCH_RESPONSE["metadata"]["depth"]
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_research_service_error(self):
        """Test research service error handling"""
        request = ResearchRequest(topic="Test Topic")
        
        with patch('src.services.research.ResearchAgent') as MockAgent:
            mock_instance = AsyncMock()
            mock_instance.research_topic.side_effect = Exception("Test error")
            MockAgent.return_value = mock_instance
            
            service = ResearchService()
            with pytest.raises(Exception):
                await service.research_topic_from_request(request) 
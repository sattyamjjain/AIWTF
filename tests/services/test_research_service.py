import pytest
from src.services.research import ResearchService
from src.api.models.research import ResearchRequest, ResearchResponse
from tests.utils.mock_data import MOCK_RESEARCH_REQUEST, MOCK_RESEARCH_RESPONSE
from unittest.mock import patch, AsyncMock
import copy

class TestResearchService:
    """Test cases for ResearchService"""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_research_service_success(self):
        """Test successful research service"""
        # Setup
        request = ResearchRequest(**MOCK_RESEARCH_REQUEST)
        
        # Create a deep copy of mock response
        response_data = copy.deepcopy(MOCK_RESEARCH_RESPONSE)
        
        # Mock the ResearchAgent class and its instance
        with patch('src.services.research.ResearchAgent') as MockAgent:
            # Create mock instance
            mock_instance = AsyncMock()
            mock_instance.research_topic.return_value = response_data
            MockAgent.return_value = mock_instance
            
            # Create service with mocked dependencies
            service = ResearchService()
            
            # Execute
            result = await service.research_topic(request)
            
            # Assert response structure
            assert isinstance(result, ResearchResponse)
            assert result.topic == request.topic
            assert result.summary == response_data["summary"]
            assert result.key_findings == response_data["key_findings"]
            assert result.statistics == response_data["statistics"]
            assert len(result.sources) == len(response_data["sources"])
            
            # Verify agent called correctly
            mock_instance.research_topic.assert_called_once_with(
                topic=request.topic,
                depth=request.depth,
                max_sources=request.max_sources
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_research_service_error(self):
        """Test error handling in research service"""
        # Setup
        request = ResearchRequest(**MOCK_RESEARCH_REQUEST)
        
        # Mock the ResearchAgent class
        with patch('src.services.research.ResearchAgent') as MockAgent:
            # Create mock instance that raises an error
            mock_instance = AsyncMock()
            mock_instance.research_topic.side_effect = ValueError("Test error")
            MockAgent.return_value = mock_instance
            
            # Create service with mocked dependencies
            service = ResearchService()
            
            # Execute and assert
            with pytest.raises(ValueError) as exc_info:
                await service.research_topic(request)
            
            assert str(exc_info.value) == "Test error"
            mock_instance.research_topic.assert_called_once_with(
                topic=request.topic,
                depth=request.depth,
                max_sources=request.max_sources
            ) 
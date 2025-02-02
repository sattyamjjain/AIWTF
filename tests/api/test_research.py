import pytest
from fastapi import status
from src.api.models.research import ResearchResponse
from tests.utils.mock_data import MOCK_RESEARCH_REQUEST, MOCK_RESEARCH_RESPONSE

@pytest.mark.asyncio
@pytest.mark.integration
async def test_research_endpoint_success(async_client, mock_research_service):
    """Test successful research endpoint"""
    # Setup mock
    mock_research_service.research_topic.return_value = MOCK_RESEARCH_RESPONSE
    
    # Make request
    response = await async_client.post(
        "/api/v1/research",
        json=MOCK_RESEARCH_REQUEST
    )
    
    # Assert response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["topic"] == MOCK_RESEARCH_REQUEST["topic"]
    assert "summary" in data
    assert "key_findings" in data
    assert "statistics" in data
    assert "sources" in data
    assert "metadata" in data

@pytest.mark.asyncio
@pytest.mark.integration
async def test_research_endpoint_validation(async_client):
    """Test input validation"""
    # Test invalid depth
    invalid_request = MOCK_RESEARCH_REQUEST.copy()
    invalid_request["depth"] = 0
    
    response = await async_client.post(
        "/api/v1/research",
        json=invalid_request
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # Test missing topic
    invalid_request = MOCK_RESEARCH_REQUEST.copy()
    del invalid_request["topic"]
    
    response = await async_client.post(
        "/api/v1/research",
        json=invalid_request
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
@pytest.mark.integration
async def test_research_endpoint_error(async_client, mock_research_service):
    """Test error handling"""
    # Setup mock to raise exception
    mock_research_service.research_topic.side_effect = ValueError("Test error")
    
    response = await async_client.post(
        "/api/v1/research",
        json=MOCK_RESEARCH_REQUEST
    )
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    error_response = response.json()
    assert "detail" in error_response
    assert "Test error" in error_response["detail"] 
import pytest
from fastapi import status
from tests.utils.mock_data import MOCK_RESEARCH_REQUEST, MOCK_RESEARCH_RESPONSE


@pytest.mark.asyncio
@pytest.mark.integration
async def test_research_endpoint_success(
    async_client, mock_research_service, mock_research_response
):
    """Test successful research endpoint"""
    mock_research_service.research_topic_from_request.return_value = (
        MOCK_RESEARCH_RESPONSE
    )

    response = await async_client.post("/api/v1/research", json=MOCK_RESEARCH_REQUEST)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["topic"] == MOCK_RESEARCH_REQUEST["topic"]
    assert "summary" in data
    assert "key_findings" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_research_endpoint_validation(async_client):
    """Test input validation"""
    invalid_request = MOCK_RESEARCH_REQUEST.copy()
    del invalid_request["topic"]

    response = await async_client.post("/api/v1/research", json=invalid_request)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
@pytest.mark.integration
async def test_research_endpoint_error(async_client, mock_research_service):
    """Test error handling"""
    mock_research_service.research_topic_from_request.side_effect = Exception(
        "Test error"
    )

    response = await async_client.post("/api/v1/research", json=MOCK_RESEARCH_REQUEST)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    error_response = response.json()
    assert "detail" in error_response
    assert "Test error" in error_response["detail"]

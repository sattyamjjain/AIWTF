import os
import sys
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from httpx import AsyncClient
import asyncio
from typing import AsyncGenerator, Generator, Dict, Any
from src.api.main import app
from src.services.research import ResearchService
from src.core.config import Settings, get_settings
from unittest.mock import AsyncMock, MagicMock

# Add src directory to Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_path)

@pytest.fixture(autouse=True)
def setup_environment():
    """Automatically load environment variables before each test"""
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        pytest.skip("OPENAI_API_KEY not found in environment")
    return api_key 

def get_settings_override():
    """Override settings for testing"""
    return Settings(
        OPENAI_API_KEY="test-openai-key",
        SERPAPI_API_KEY="test-serp-key",
        TESTING=True
    )

@pytest.fixture
def settings():
    """Settings fixture"""
    return get_settings_override()

@pytest.fixture
def app_client() -> Generator:
    """Test client fixture"""
    app.dependency_overrides[get_settings] = get_settings_override
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
async def async_client() -> AsyncGenerator:
    """Async test client fixture"""
    app.dependency_overrides[get_settings] = get_settings_override
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_research_service(monkeypatch):
    """Create a mock research service"""
    service = MagicMock(spec=ResearchService)
    
    def get_mock_service():
        return service
    
    # Mock both the class and instance
    monkeypatch.setattr(
        "src.api.routes.research.ResearchService",
        MagicMock(return_value=service)
    )
    
    # Mock the dependency
    app.dependency_overrides[ResearchService] = get_mock_service
    
    return service

@pytest.fixture
def mock_search_results():
    """Mock search results"""
    return [
        {
            "title": "Test Result",
            "link": "https://example.com",
            "snippet": "Test snippet"
        }
    ]

@pytest.fixture
def mock_research_response(mock_search_results):
    """Mock research response"""
    return {
        "results": mock_search_results,
        "metadata": {
            "query": "test query",
            "num_results": 5
        }
    }

@pytest.fixture(scope="session")
def event_loop_policy():
    """Create event loop policy for async tests"""
    return asyncio.WindowsSelectorEventLoopPolicy() if os.name == 'nt' else asyncio.DefaultEventLoopPolicy() 

@pytest.fixture
def MOCK_RESEARCH_REQUEST():
    return {
        "topic": "Test Research Topic",
        "depth": 1,
        "max_sources": 5
    }

@pytest.fixture
def MOCK_RESEARCH_RESPONSE():
    return {
        "topic": "Test Research Topic",
        "summary": "Test summary of the research",
        "sources": [
            {
                "title": "Test Source",
                "url": "https://example.com"
            }
        ],
        "metadata": {
            "depth": 1,
            "source_count": 1,
            "completion_time": "2025-02-02T16:16:12.830034",
            "duration": "0:00:01.234567",
            "errors": []
        }
    } 
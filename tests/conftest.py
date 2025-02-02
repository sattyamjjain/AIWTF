import os
import sys
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from httpx import AsyncClient
import asyncio
from typing import AsyncGenerator, Generator
from src.api.main import app
from src.services.research import ResearchService
from src.core.config import Settings, get_settings
from unittest.mock import AsyncMock

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
    """Mock research service fixture"""
    service = AsyncMock(spec=ResearchService)
    
    async def get_mock_service():
        return service
    
    # Mock both the class and instance
    monkeypatch.setattr(
        "src.api.routes.research.ResearchService",
        AsyncMock(return_value=service)
    )
    
    # Also mock the dependency
    app.dependency_overrides[ResearchService] = get_mock_service
    
    return service

@pytest.fixture(scope="session")
def event_loop_policy():
    """Create event loop policy for async tests"""
    return asyncio.WindowsSelectorEventLoopPolicy() if os.name == 'nt' else asyncio.DefaultEventLoopPolicy() 
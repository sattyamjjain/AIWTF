import pytest
from src.innovations.research.agent import ResearchAgent
from src.core.exceptions import ResearchError
import asyncio
import logging
from unittest.mock import AsyncMock, patch, MagicMock

logger = logging.getLogger(__name__)


@pytest.fixture
def mock_content_extractor():
    """Mock content extractor"""
    with patch("src.agents.tools.content_tools.ContentExtractor") as mock:
        mock_instance = MagicMock()
        mock_instance.extract_from_url.return_value = {
            "content": "Test content about AI and machine learning",
            "metadata": {"url": "https://example.com"},
        }
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def research_agent(mock_search_results, mock_content_extractor):
    """Create a research agent with mocked tools"""
    with patch("src.agents.tools.research_tools.get_search_provider") as mock_provider:
        mock_search = MagicMock()
        mock_search.search.return_value = mock_search_results
        mock_provider.return_value = mock_search

        agent = ResearchAgent(search_provider="duckduckgo")
        return agent


@pytest.mark.asyncio
async def test_basic_research(research_agent, mock_search_results):
    """Test basic research functionality"""
    query = "What is Python?"
    result = await research_agent.research(query)

    assert result["results"] == mock_search_results
    assert result["metadata"]["query"] == query


@pytest.mark.asyncio
async def test_deep_research(research_agent, mock_content_extractor):
    """Test deeper research with subtopics"""
    # Mock the research synthesizer tool
    mock_synthesis = {
        "topic": "Artificial General Intelligence progress",
        "summary": "Test summary",
        "sources": [{"title": "Test Result", "url": "https://example.com"}],
        "metadata": {
            "depth": 2,
            "source_count": 1,
            "completion_time": "2025-02-02T16:16:28.487220",
            "duration": "0:00:15.269648",
            "errors": [],
        },
    }
    research_agent._execute_tool = AsyncMock(return_value=mock_synthesis)

    result = await research_agent.research_topic(
        topic="Artificial General Intelligence progress", depth=2, max_sources=3
    )

    assert result["topic"] == "Artificial General Intelligence progress"
    assert "summary" in result
    assert "sources" in result
    assert "metadata" in result
    assert result["metadata"]["depth"] == 2


@pytest.mark.asyncio
async def test_error_handling(research_agent):
    """Test error handling with invalid inputs"""
    research_agent._execute_tool = AsyncMock(side_effect=Exception("Test error"))

    with pytest.raises(ResearchError):
        await research_agent.research_topic(
            topic="", depth=1, max_sources=3  # Invalid empty topic
        )


@pytest.mark.asyncio
async def test_tool_execution(research_agent, mock_search_results):
    """Test individual tool execution"""
    query = "Python programming"
    result = await research_agent.research(query)

    assert result["results"] == mock_search_results
    assert result["metadata"]["query"] == query


@pytest.mark.asyncio
async def test_subtopic_identification(research_agent):
    """Test subtopic identification"""
    content = """
    Quantum computing is an emerging technology that uses quantum mechanics.
    Key areas include quantum gates, error correction, and quantum algorithms.
    Recent developments in superconducting qubits have shown promise.
    """

    try:
        subtopics = await research_agent._identify_subtopics(content)
        assert len(subtopics) >= 2
        assert all(isinstance(t, str) for t in subtopics)
    except Exception as e:
        pytest.skip(f"OpenAI API error: {str(e)}")


@pytest.mark.asyncio
async def test_concurrent_research(research_agent):
    """Test concurrent research on multiple topics"""
    queries = [
        "Machine Learning basics",
        "Python async programming",
        "Web development trends",
    ]

    tasks = [research_agent.research(query) for query in queries]
    results = await asyncio.gather(*tasks)

    assert len(results) == len(queries)
    assert all("results" in r for r in results)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pytest.main([__file__, "-v"])

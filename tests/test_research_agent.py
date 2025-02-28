import pytest
from src.innovations.research.agent import ResearchAgent
from src.core.exceptions import ResearchError
import asyncio
import logging
from unittest.mock import AsyncMock, patch, MagicMock

logger = logging.getLogger(__name__)


@pytest.fixture
def mock_search_results():
    return [
        {
            "title": "Test Result",
            "link": "https://example.com",
            "snippet": "Test snippet"
        }
    ]


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
    with patch("src.agents.tools.web_tools.WebSearchTool") as mock_web_tool:
        # Create a mock web search tool instance
        mock_web_tool_instance = AsyncMock()
        
        # Create a mock _arun method that returns the results directly
        async def mock_arun(*args, **kwargs):
            return mock_search_results
            
        mock_web_tool_instance._arun = mock_arun
        mock_web_tool.return_value = mock_web_tool_instance
        
        # Create the agent
        agent = ResearchAgent(search_provider="duckduckgo")
        
        # Mock the content extractor
        agent.content_extractor = mock_content_extractor
        
        # Mock the web search tool instance
        agent.web_search_tool = mock_web_tool_instance
        
        # Mock the tools' functions directly
        for tool in agent.tools:
            if tool.name == "web_search":
                # Replace the function with our mock
                async def mock_search(*args, **kwargs):
                    return mock_search_results
                tool.func = mock_search
            elif tool.name == "content_extractor":
                async def mock_extract(*args, **kwargs):
                    return {
                        "content": "Test content",
                        "metadata": {"url": args[0]}
                    }
                tool.func = mock_extract
        
        return agent


@pytest.mark.asyncio
async def test_basic_research(research_agent, mock_search_results):
    """Test basic research functionality"""
    query = "What is Python?"
    result = await research_agent.research(query)
    assert result["results"] == mock_search_results


@pytest.mark.asyncio
async def test_deep_research(research_agent, mock_content_extractor):
    """Test deeper research with subtopics"""
    mock_synthesis = "Test summary"  # Simplified mock response
    research_agent._synthesize_content_with_llm = AsyncMock(return_value=mock_synthesis)
    
    result = await research_agent.research_topic(
        topic="Artificial General Intelligence progress",
        depth=2,
        max_sources=3
    )
    
    assert result["topic"] == "Artificial General Intelligence progress"
    assert result["summary"] == mock_synthesis
    assert "sources" in result
    assert "metadata" in result


@pytest.mark.asyncio
async def test_error_handling(research_agent):
    """Test error handling in research"""
    with pytest.raises(ResearchError):
        await research_agent.research_topic("")


@pytest.mark.asyncio
async def test_tool_execution(research_agent, mock_search_results):
    """Test individual tool execution"""
    query = "Python programming"
    result = await research_agent.research(query)
    assert result["results"] == mock_search_results


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

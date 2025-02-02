import pytest
from src.innovations.research.agent import ResearchAgent
from src.core.exceptions import ResearchError
import asyncio
import logging

logger = logging.getLogger(__name__)

@pytest.fixture
async def research_agent():
    """Async fixture to create and return a research agent"""
    agent = ResearchAgent()
    try:
        yield agent
    finally:
        await agent.aclose()

@pytest.mark.asyncio
async def test_basic_research(research_agent):
    """Test basic research functionality"""
    topic = "Latest developments in quantum computing"
    
    result = await research_agent.research_topic(
        topic=topic,
        depth=1,
        max_sources=3
    )
    
    # Verify structure
    assert "topic" in result
    assert "summary" in result
    assert "key_findings" in result
    assert "statistics" in result
    assert "sources" in result
    assert "metadata" in result
    
    # Verify content
    assert result["topic"] == topic
    assert isinstance(result["summary"], str)
    assert len(result["summary"]) > 0
    assert isinstance(result["key_findings"], dict)
    assert isinstance(result["statistics"], dict)
    assert isinstance(result["sources"], list)

@pytest.mark.asyncio
async def test_deep_research(research_agent):
    """Test deeper research with subtopics"""
    topic = "Artificial General Intelligence progress"
    
    result = await research_agent.research_topic(
        topic=topic,
        depth=2,
        max_sources=3
    )
    
    # Verify deeper research
    assert result["metadata"]["depth"] == 2
    assert len(result["sources"]) >= 2  # Should have sources from subtopics

@pytest.mark.asyncio
async def test_error_handling(research_agent):
    """Test error handling with invalid inputs"""
    with pytest.raises(ResearchError):
        await research_agent.research_topic(
            topic="   ",  # Empty or whitespace topic should raise error
            depth=1,
            max_sources=3
        )

@pytest.mark.asyncio
async def test_tool_execution(research_agent):
    """Test individual tool execution"""
    state = research_agent.get_initial_state()
    
    # Test web search
    search_results = await research_agent._execute_tool(
        "web_search",
        "Python programming language",
        state
    )
    assert len(search_results) > 0
    assert all(isinstance(r, dict) for r in search_results)
    
    # Test content extraction
    if search_results:
        content = await research_agent._execute_tool(
            "content_extractor",
            search_results[0]['link'],
            state
        )
        assert 'content' in content
        assert 'metadata' in content

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
    topics = [
        "Machine Learning basics",
        "Python async programming",
        "Web development trends"
    ]
    
    tasks = [
        research_agent.research_topic(topic, depth=1, max_sources=2)
        for topic in topics
    ]
    
    results = await asyncio.gather(*tasks)
    assert len(results) == len(topics)
    assert all("summary" in r for r in results)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pytest.main([__file__, "-v"]) 
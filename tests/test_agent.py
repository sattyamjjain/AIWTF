import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from src.agents.base.base_agent import BaseAgent
from src.agents.tools.web_tools import WebSearchTool, WebBrowseTool
from src.agents.tools.research_tools import WebSearchTool
import asyncio
import pytest
import httpx
from openai import OpenAIError

@pytest.mark.slow
@pytest.mark.asyncio
async def test_agent():
    load_dotenv()  # Load environment variables first
    api_key = os.getenv('OPENAI_API_KEY')
    assert api_key is not None, "OPENAI_API_KEY not found in environment"
    
    # Reduce test cases to one
    test_query = "What is Python?"
    
    tools = [WebSearchTool()]  # Reduce tools
    
    async with BaseAgent(
        tools=tools,
        system_prompt="You are a helpful AI assistant."
    ) as agent:
        try:
            response = await agent.run(test_query)
            assert isinstance(response, str)
            assert len(response) > 0
        except (httpx.RemoteProtocolError, OpenAIError) as e:
            pytest.skip(f"OpenAI API connection error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_agent()) 
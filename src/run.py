import asyncio
from src.agents.base.base_innovation import BaseInnovationAgent
from src.agents.tools.web_tools import WebSearchTool, WebBrowseTool
from src.utils import setup_logging

logger = setup_logging()

async def run_agent():
    try:
        # Initialize tools
        tools = [WebSearchTool(), WebBrowseTool()]

        # Create agent
        agent = BaseInnovationAgent(
            tools=tools,
            system_prompt="""You are a helpful AI assistant that can search the web and browse websites.
            Use your tools wisely to find accurate information and help users with their queries.
            Always verify information from multiple sources when possible.""",
        )

        # Example usage
        query = "What are the latest developments in AI agents?"
        logger.info(f"Processing query: {query}")

        result = await agent.run(query)
        logger.info("Query processed successfully")

        print(f"Query: {query}")
        print(f"Response: {result}")

    except Exception as e:
        logger.error(f"Application error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_agent()) 
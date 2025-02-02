import asyncio
import os
from dotenv import load_dotenv
from agents.base.base_innovation import BaseInnovationAgent
from agents.tools.web_tools import WebSearchTool, WebBrowseTool
from utils import setup_logging, Config
from core.exceptions import ConfigurationError

# Initialize logging
logger = setup_logging()


def initialize_environment():
    """Initialize environment and configurations"""
    load_dotenv()

    # Check for required environment variables
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ConfigurationError(
            f"Missing required environment variables: {missing_vars}"
        )

    # Load configuration
    try:
        config = Config.load_config("config/default.yaml")
        return config
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration: {e}")


async def main():
    try:
        # Initialize environment
        config = initialize_environment()
        logger.info("Environment initialized successfully")

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
    asyncio.run(main())

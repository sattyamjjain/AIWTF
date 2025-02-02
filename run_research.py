import asyncio
from src.innovations.research.agent import ResearchAgent
import logging
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

async def main():
    # Verify API key is loaded
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    # Initialize the research agent
    agent = ResearchAgent()
    
    # Define your research topic
    topic = "Latest developments in quantum computing"
    
    try:
        # Run the research
        result = await agent.research_topic(
            topic=topic,
            depth=2,  # How deep to go with subtopics
            max_sources=5  # Maximum sources per topic
        )
        
        # Print the results
        print("\n=== Research Results ===")
        print(f"Topic: {result['topic']}")
        print("\nSummary:")
        for finding in result['summary']:
            print(f"- {finding}")
        
        print("\nKey Points:")
        for point in result['key_points']:
            print(f"- {point}")
        
        print("\nSources:")
        for source in result['sources']:
            print(f"- {source['title']}: {source['url']}")
        
        print("\nMetadata:")
        for key, value in result['metadata'].items():
            print(f"- {key}: {value}")
            
    except Exception as e:
        logging.error(f"Research failed: {str(e)}")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the async main function
    asyncio.run(main()) 
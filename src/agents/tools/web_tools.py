from langchain_core.tools import BaseTool
from bs4 import BeautifulSoup
import requests
from typing import Optional, Any, Dict
from langchain.tools import BaseTool
import logging
import aiohttp

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """Tool for performing web searches"""
    
    name = "web_search"
    description = "Search the web for information"
    return_direct = True

    async def _arun(self, query: str) -> str:
        """Run web search asynchronously"""
        try:
            # Use DuckDuckGo HTML search
            url = f"https://duckduckgo.com/html/?q={query}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    html = await response.text()

            soup = BeautifulSoup(html, "html.parser")
            results = []

            for result in soup.find_all("div", class_="result"):
                title = result.find("h2").text if result.find("h2") else ""
                snippet = (
                    result.find("a", class_="result__snippet").text
                    if result.find("a", class_="result__snippet")
                    else ""
                )
                results.append(f"Title: {title}\nSnippet: {snippet}\n")

                if len(results) >= 3:  # Limit to top 3 results
                    break

            return "\n".join(results) if results else "No results found"
        except Exception as e:
            logger.error(f"Web search failed: {str(e)}")
            return f"Error performing web search: {str(e)}"

    def _run(self, query: str) -> str:
        """Run web search synchronously"""
        raise NotImplementedError("WebSearchTool only supports async operations")


class WebBrowseTool(BaseTool):
    name: str = "web_browse"
    description: str = "Browse a specific webpage and extract its content"

    def _run(self, url: str) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)

        return text[:4000]  # Limit response size

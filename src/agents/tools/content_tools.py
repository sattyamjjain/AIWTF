from typing import Dict, Any, List
import trafilatura
import requests
from bs4 import BeautifulSoup
import httpx
import logging
import backoff
from newspaper import Article
import asyncio
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)


class ContentExtractor:
    """A utility class for extracting content from web pages"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.ua = UserAgent()
        self.headers = {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }

    async def extract_from_url(self, url: str) -> Dict[str, Any]:
        """Extract content from a URL using multiple methods"""
        if not url:
            logger.warning("Empty URL provided")
            return {"content": "", "metadata": {"url": url, "error": "Empty URL"}}

        try:
            logger.info(f"Attempting to extract content from: {url}")

            # Try different extraction methods
            content = await self._try_multiple_methods(url)

            if content.get("content"):
                logger.info(
                    f"Successfully extracted {len(content['content'])} characters from {url}"
                )
                return content
            else:
                logger.warning(f"All extraction methods failed for {url}")
                return {
                    "content": "",
                    "metadata": {
                        "url": url,
                        "error": "Content extraction failed with all methods",
                    },
                }

        except Exception as e:
            logger.error(
                f"Content extraction failed for {url}: {str(e)}", exc_info=True
            )
            return {"content": "", "metadata": {"url": url, "error": str(e)}}

    async def _try_multiple_methods(self, url: str) -> Dict[str, Any]:
        """Try multiple methods to extract content"""
        methods = [
            self._extract_with_trafilatura,
            self._extract_with_newspaper,
            self._extract_with_httpx,
            self._extract_with_selenium,
        ]

        for method in methods:
            try:
                content = await method(url)
                if content.get("content"):
                    return content
            except Exception as e:
                logger.debug(f"Method {method.__name__} failed for {url}: {str(e)}")
                continue

        return {"content": "", "metadata": {"url": url, "error": "All methods failed"}}

    async def _extract_with_trafilatura(self, url: str) -> Dict[str, Any]:
        """Extract content using trafilatura"""
        try:
            downloaded = await asyncio.to_thread(trafilatura.fetch_url, url)
            if downloaded:
                result = await asyncio.to_thread(
                    trafilatura.extract, downloaded, include_metadata=True
                )
                if result:
                    return {
                        "content": result,
                        "metadata": {
                            "url": url,
                            "title": result.get("title", ""),
                            "method": "trafilatura",
                        },
                    }
        except Exception as e:
            logger.debug(f"Trafilatura extraction failed: {str(e)}")
        return {"content": ""}

    async def _extract_with_newspaper(self, url: str) -> Dict[str, Any]:
        """Extract content using newspaper3k"""
        try:
            article = Article(url)
            await asyncio.to_thread(article.download)
            await asyncio.to_thread(article.parse)

            if article.text:
                return {
                    "content": article.text,
                    "metadata": {
                        "url": url,
                        "title": article.title,
                        "method": "newspaper3k",
                    },
                }
        except Exception as e:
            logger.debug(f"Newspaper extraction failed: {str(e)}")
        return {"content": ""}

    async def _extract_with_httpx(self, url: str) -> Dict[str, Any]:
        """Extract content using httpx and BeautifulSoup"""
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers=self.headers,
                follow_redirects=True,
                verify=False,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

                if url.lower().endswith(".pdf"):
                    return {
                        "content": "PDF file - content extraction not supported",
                        "metadata": {"url": url, "type": "pdf"},
                    }

                soup = BeautifulSoup(response.text, "html.parser")

                # Remove unwanted elements
                for element in soup(
                    ["script", "style", "nav", "header", "footer", "aside"]
                ):
                    element.decompose()

                # Get main content
                main_content = (
                    soup.find("main") or soup.find("article") or soup.find("body")
                )

                if main_content:
                    text = main_content.get_text(separator=" ", strip=True)
                    return {
                        "content": text,
                        "metadata": {
                            "url": url,
                            "title": soup.title.string if soup.title else "",
                            "method": "httpx",
                        },
                    }
        except Exception as e:
            logger.debug(f"HTTPX extraction failed: {str(e)}")
        return {"content": ""}

    async def _extract_with_selenium(self, url: str) -> Dict[str, Any]:
        """Extract content using Selenium (as a last resort)"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options

            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument(f"user-agent={self.ua.random}")

            driver = webdriver.Chrome(options=chrome_options)
            await asyncio.to_thread(driver.get, url)
            content = await asyncio.to_thread(
                driver.find_element_by_tag_name, "body"
            ).text
            await asyncio.to_thread(driver.quit)

            if content:
                return {
                    "content": content,
                    "metadata": {"url": url, "method": "selenium"},
                }
        except Exception as e:
            logger.debug(f"Selenium extraction failed: {str(e)}")
        return {"content": ""}

    @staticmethod
    def extract_from_url_old(url: str) -> Dict[str, Any]:
        """
        Extract content from a given URL

        Args:
            url: The URL to extract content from

        Returns:
            Dict containing extracted content with keys:
            - title: page title
            - text: main text content
            - metadata: additional metadata
        """
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded is None:
                return {"error": "Failed to download content"}

            result = trafilatura.extract(downloaded, include_metadata=True)

            if result is None:
                # Fallback to basic extraction
                response = requests.get(url)
                soup = BeautifulSoup(response.text, "html.parser")
                return {
                    "title": soup.title.string if soup.title else "",
                    "text": " ".join([p.text for p in soup.find_all("p")]),
                    "metadata": {},
                }

            return {
                "title": result.get("title", ""),
                "text": result.get("text", ""),
                "metadata": {
                    "author": result.get("author", ""),
                    "date": result.get("date", ""),
                    "description": result.get("description", ""),
                },
            }

        except Exception as e:
            return {"error": str(e)}

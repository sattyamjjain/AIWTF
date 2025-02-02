from langchain_core.tools import BaseTool
from typing import List, Dict, Any, Optional, Type
from pydantic import Field, BaseModel, ConfigDict, PrivateAttr
import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import asyncio
import yaml
import os
import time
import logging
import backoff
from serpapi import GoogleSearch
from src.agents.tools.content_tools import ContentExtractor
from src.agents.tools.search_providers import get_search_provider, SearchProvider
from src.core.config import get_settings

logger = logging.getLogger(__name__)


class WebSearchConfig(BaseModel):
    engine: str = "google"
    max_results: int = 5
    retry_attempts: int = 3
    retry_delay: float = 2.0


class WebSearchInput(BaseModel):
    """Input schema for web search"""

    query: str = Field(..., description="The search query")
    num_results: int = Field(default=5, description="Number of results to return")


class WebSearchTool(BaseTool):
    """Tool for web searching"""

    name: str = "web_search"
    description: str = "Search the web for information on a given topic"
    args_schema: type[BaseModel] = WebSearchInput

    def __init__(
        self,
        provider_type: str = "auto",
        api_key: Optional[str] = None,
        cx: Optional[str] = None,
    ):
        super().__init__()
        # Use object.__setattr__ to bypass Pydantic validation
        object.__setattr__(
            self, "_provider", get_search_provider(provider_type, api_key, cx)
        )

    def _run(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Execute web search"""
        return self._provider.search(query, num_results)

    async def _arun(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Async execution of web search"""
        return self._run(query, num_results)


class ContentExtractorConfig(BaseModel):
    timeout: int = 30
    max_content_length: int = 10000
    fallback_content: str = "Content extraction failed."
    retry_attempts: int = 2
    retry_delay: float = 1.0


class ContentExtractorInput(BaseModel):
    """Input schema for content extraction"""

    url: str = Field(..., description="URL to extract content from")


class ContentExtractorTool(BaseTool):
    """Tool for extracting content from web pages"""

    name: str = "content_extractor"
    description: str = "Extract content from a web page URL"
    args_schema: type[BaseModel] = ContentExtractorInput

    # Use PrivateAttr for non-pydantic fields
    _extractor: ContentExtractor = PrivateAttr()

    def __init__(self):
        super().__init__()
        object.__setattr__(self, "_extractor", ContentExtractor())

    def _run(self, url: str) -> Dict[str, Any]:
        """Extract content from URL synchronously"""
        raise NotImplementedError("Use _arun instead")

    async def _arun(self, url: str) -> Dict[str, Any]:
        """Async content extraction"""
        try:
            result = await self._extractor.extract_from_url(url)
            return result
        except Exception as e:
            logger.error(f"Content extraction failed: {str(e)}")
            return {"content": "", "metadata": {"url": url, "error": str(e)}}


class ResearchSynthesizerConfig(BaseModel):
    max_key_points: int = 5
    min_sentence_length: int = 50


class ResearchSynthesizerTool(BaseTool):
    """Tool for synthesizing research findings"""

    name: str = "research_synthesizer"
    description: str = "Synthesize research findings into a coherent summary"
    config: ResearchSynthesizerConfig = Field(default_factory=ResearchSynthesizerConfig)

    def __init__(self, **data):
        super().__init__(**data)
        self.config = ResearchSynthesizerConfig()

    def _run(self, research_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            valid_data = [
                d for d in research_data if isinstance(d, dict) and "content" in d
            ]

            if not valid_data:
                logger.warning("No valid research data provided for synthesis")
                return self._create_fallback_synthesis()

            # Combine all content
            all_content = "\n".join(d["content"] for d in valid_data)

            # Extract key sections
            synthesis = {
                "summary": self._extract_summary(all_content),
                "key_points": {
                    "tax_changes": [],
                    "economic_measures": [],
                    "social_initiatives": [],
                    "infrastructure": [],
                    "other_highlights": [],
                },
                "statistics": {"fiscal": [], "allocations": [], "targets": []},
                "sources": self._format_sources(valid_data),
            }

            # Process content to extract structured information
            for data in valid_data:
                content = data["content"]

                # Extract key points by category
                synthesis["key_points"]["tax_changes"].extend(
                    self._extract_category_points(content, ["tax", "income", "revenue"])
                )
                synthesis["key_points"]["economic_measures"].extend(
                    self._extract_category_points(
                        content, ["economy", "finance", "market", "industry"]
                    )
                )
                synthesis["key_points"]["social_initiatives"].extend(
                    self._extract_category_points(
                        content, ["welfare", "social", "education", "health"]
                    )
                )
                synthesis["key_points"]["infrastructure"].extend(
                    self._extract_category_points(
                        content, ["infrastructure", "development", "construction"]
                    )
                )

                # Extract statistics
                synthesis["statistics"]["fiscal"].extend(
                    self._extract_statistics(content, ["deficit", "gdp", "growth"])
                )
                synthesis["statistics"]["allocations"].extend(
                    self._extract_statistics(content, ["allocation", "fund", "budget"])
                )

            # Deduplicate and clean
            for category in synthesis["key_points"]:
                synthesis["key_points"][category] = list(
                    set(synthesis["key_points"][category])
                )
                synthesis["key_points"][category] = [
                    p for p in synthesis["key_points"][category] if len(p) > 20
                ]

            for category in synthesis["statistics"]:
                synthesis["statistics"][category] = list(
                    set(synthesis["statistics"][category])
                )

            logger.info(
                f"Synthesized research data into {len(synthesis['key_points'])} categories"
            )
            return synthesis

        except Exception as e:
            logger.error(f"Research synthesis failed: {str(e)}")
            return self._create_fallback_synthesis()

    def _extract_summary(self, content: str) -> str:
        """Extract a concise summary from the content"""
        # Find sentences that look like summaries
        sentences = content.split(".")
        summary_sentences = [
            s
            for s in sentences
            if any(
                w in s.lower()
                for w in ["highlight", "announce", "present", "introduce", "budget"]
            )
        ]

        if summary_sentences:
            return ". ".join(summary_sentences[:3]).strip() + "."
        return "No summary available."

    def _extract_category_points(self, content: str, keywords: List[str]) -> List[str]:
        """Extract points related to specific categories"""
        sentences = content.split(".")
        category_points = []

        for sentence in sentences:
            if any(k in sentence.lower() for k in keywords):
                clean_sentence = sentence.strip()
                if clean_sentence and len(clean_sentence) > 20:
                    category_points.append(clean_sentence)

        return category_points

    def _extract_statistics(self, content: str, keywords: List[str]) -> List[str]:
        """Extract statistical information"""
        sentences = content.split(".")
        stats = []

        for sentence in sentences:
            if any(k in sentence.lower() for k in keywords) and any(
                c.isdigit() for c in sentence
            ):
                clean_sentence = sentence.strip()
                if clean_sentence:
                    stats.append(clean_sentence)

        return stats

    def _format_sources(self, data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format source information"""
        sources = []
        seen_urls = set()

        for d in data:
            if "metadata" in d and "url" in d["metadata"]:
                url = d["metadata"]["url"]
                if url not in seen_urls and url != "https://example.com/error":
                    sources.append(
                        {
                            "title": d["metadata"].get("title", "Unknown Source"),
                            "url": url,
                        }
                    )
                    seen_urls.add(url)

        return sources

    def _create_fallback_synthesis(self) -> Dict[str, Any]:
        return {
            "summary": "Unable to synthesize meaningful findings.",
            "key_points": {
                "tax_changes": [],
                "economic_measures": [],
                "social_initiatives": [],
                "infrastructure": [],
                "other_highlights": [],
            },
            "statistics": {"fiscal": [], "allocations": [], "targets": []},
            "sources": [],
        }

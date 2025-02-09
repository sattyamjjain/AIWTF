from typing import List, Dict, Any, Optional
from src.agents.base.base_innovation import BaseInnovationAgent
from src.agents.tools.research_tools import (
    WebSearchTool,
    ContentExtractorTool,
    ResearchSynthesizerTool,
)
from src.core.state import WorkflowState
from src.core.exceptions import ResearchError
import asyncio
from datetime import datetime
import backoff
import logging
from src.agents.tools.content_tools import ContentExtractor
from langchain.tools import Tool
from src.agents.tools.web_tools import WebSearchTool

logger = logging.getLogger(__name__)


class ResearchAgent(BaseInnovationAgent):
    """Agent for conducting research"""

    def __init__(self, search_provider: str = "duckduckgo"):
        """Initialize research agent with tools"""
        # Initialize web search tool
        self.web_search_tool = WebSearchTool()
        self.content_extractor = ContentExtractor()

        tools = [
            Tool(
                name="web_search",
                func=self._search,
                description="Search the web for information",
                return_direct=True
            ),
            Tool(
                name="content_extractor",
                func=self._extract_content,
                description="Extract content from a webpage",
                return_direct=True
            )
        ]

        system_prompt = """You are a research assistant that helps gather and analyze information.
        Follow these steps:
        1. Search for relevant information
        2. Extract and analyze content
        3. Synthesize findings into a coherent summary
        4. Provide source citations
        """

        super().__init__(tools=tools, system_prompt=system_prompt)

    async def _search(self, query: str) -> Any:
        """Wrapper method for web search"""
        try:
            return await self.web_search_tool._arun(query)  # Just await once and return
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return f"Search failed: {str(e)}"

    async def _extract_content(self, url: str) -> Dict[str, Any]:
        """Extract content from a webpage"""
        try:
            content = await self.content_extractor.extract_from_url(url)
            return {
                "content": content.get("content", ""),
                "metadata": content.get("metadata", {})
            }
        except Exception as e:
            logger.error(f"Content extraction failed: {str(e)}")
            return {
                "content": f"Error extracting content: {str(e)}",
                "metadata": {}
            }

    async def research(self, query: str) -> Dict[str, Any]:
        """Conduct basic research on a query"""
        try:
            # Get search results using the tool directly
            search_tool = next(t for t in self.tools if t.name == "web_search")
            # Need to await the function since it's async
            results = await search_tool.func(query)
            
            return {
                "query": query,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Research failed: {str(e)}")
            raise ResearchError(f"Research failed: {str(e)}") from e

    async def research_topic(
        self, topic: str, depth: int = 1, max_sources: int = 5
    ) -> Dict[str, Any]:
        """Conduct research on a topic"""
        try:
            if not topic.strip():
                raise ValueError("Topic cannot be empty")

            start_time = datetime.now()
            logger.info(f"Starting research on topic: {topic}")

            # Get search results using the tool directly
            search_tool = next(t for t in self.tools if t.name == "web_search")
            # Need to await the function since it's async
            search_results = await search_tool.func(topic)
            
            if isinstance(search_results, str):
                search_results = self._parse_search_results(search_results)
            
            logger.info(f"Found {len(search_results)} search results")

            # Extract content from each source
            content_tool = next(t for t in self.tools if t.name == "content_extractor")
            contents = []
            errors = []

            for result in search_results[:max_sources]:
                try:
                    if result.get("link"):
                        logger.info(f"Extracting content from: {result['link']}")
                        # Need to await the function since it's async
                        content = await content_tool.func(result["link"])
                        if content and isinstance(content, dict) and content.get("content"):
                            contents.append({
                                "title": result["title"],
                                "content": content["content"],
                                "url": result["link"]
                            })
                            logger.info(f"Successfully extracted content from {result['link']}")
                        else:
                            error_msg = f"No content extracted from {result['link']}"
                            logger.warning(error_msg)
                            errors.append(error_msg)
                    else:
                        logger.warning(f"Empty link in search result: {result}")
                except Exception as e:
                    error_msg = f"Failed to extract content from {result.get('link', 'unknown URL')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # Generate comprehensive summary using LLM
            summary = await self._synthesize_content_with_llm(contents, topic) if contents else "No relevant content found"

            # Format sources
            sources = [
                {"title": result["title"], "url": result.get("link", "")}
                for result in search_results[:max_sources]
            ]

            completion_time = datetime.now()
            duration = completion_time - start_time

            return {
                "topic": topic,
                "summary": summary,
                "sources": sources,
                "metadata": {
                    "depth": depth,
                    "source_count": len(sources),
                    "completion_time": completion_time.isoformat(),
                    "duration": str(duration),
                    "errors": errors
                }
            }

        except Exception as e:
            logger.error(f"Research failed: {str(e)}")
            raise ResearchError(f"Research failed: {str(e)}") from e

    def _parse_search_results(self, results_str: str) -> List[Dict[str, str]]:
        """Parse search results from string format to list of dictionaries"""
        results = []
        current_result = {}
        
        for line in results_str.split('\n'):
            line = line.strip()
            if line.startswith('Title: '):
                if current_result:
                    results.append(current_result)
                current_result = {'title': line[7:], 'link': '', 'snippet': ''}
            elif line.startswith('Snippet: '):
                current_result['snippet'] = line[9:]
                current_result['link'] = f"https://example.com/result_{len(results)}"
                
        if current_result:
            results.append(current_result)
            
        return results

    async def _synthesize_content_with_llm(self, contents: List[Dict[str, str]], topic: str) -> str:
        """Synthesize content using LLM"""
        try:
            prompt = f"Synthesize the following information about {topic}:\n\n"
            for content in contents:
                prompt += f"Source: {content['title']}\n{content['content']}\n\n"
            
            result = await self.run(prompt)
            return result
        except Exception as e:
            logger.error(f"Content synthesis failed: {str(e)}")
            return f"Content synthesis failed: {str(e)}"

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()

    @backoff.on_exception(backoff.expo, Exception, max_tries=3, max_time=30)
    async def _identify_subtopics(self, content: str) -> List[str]:
        """Identify important subtopics for deeper research"""
        try:
            messages = [
                {
                    "role": "user",
                    "content": f"""Analyze this content and identify 2-3 key subtopics that warrant deeper research:
            Content: {content[:2000]}... # Truncated for token limit
            
            Return only the subtopics as a comma-separated list.""",
                }
            ]

            response = await self.async_openai_client.chat.completions.create(
                model="gpt-4-turbo-preview", messages=messages, temperature=0.7
            )

            subtopics_text = response.choices[0].message.content
            return [t.strip() for t in subtopics_text.split(",")]
        except Exception as e:
            logger.error(f"Error identifying subtopics: {str(e)}")
            return [f"Error identifying subtopics: {str(e)}"]

    async def _extract_key_findings_with_llm(
        self, contents: List[Dict[str, str]], topic: str
    ) -> Dict[str, List[str]]:
        """Extract key findings using LLM"""
        try:
            combined_content = "\n\n".join(
                [
                    f"Source: {c['title']}\n{c.get('content', '')[:2000]}"
                    for c in contents
                ]
            )

            prompt = f"""Analyze the following content about "{topic}" and extract key findings in these categories:
            - Tax changes and reforms
            - Economic measures and policies
            - Social initiatives and welfare programs
            - Infrastructure development
            - Other important highlights
            
            Content:
            {combined_content[:4000]}
            
            Format the response as bullet points under each category."""

            messages = [{"role": "user", "content": prompt}]
            response = await self.async_openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            )

            # Parse the response into categories
            text = response.choices[0].message.content
            categories = text.split("\n\n")
            findings = {
                "tax_changes": [],
                "economic_measures": [],
                "social_initiatives": [],
                "infrastructure": [],
                "other_highlights": [],
            }

            current_category = None
            for line in text.split("\n"):
                line = line.strip()
                if line.lower().startswith("tax"):
                    current_category = "tax_changes"
                elif line.lower().startswith("economic"):
                    current_category = "economic_measures"
                elif line.lower().startswith("social"):
                    current_category = "social_initiatives"
                elif line.lower().startswith("infrastructure"):
                    current_category = "infrastructure"
                elif line.lower().startswith("other"):
                    current_category = "other_highlights"
                elif line.startswith("- ") and current_category:
                    findings[current_category].append(line[2:])

            return findings
        except Exception as e:
            logger.error(f"Failed to extract key findings with LLM: {str(e)}")
            return self._extract_key_findings_basic(contents)

    async def _extract_statistics_with_llm(
        self, contents: List[Dict[str, str]], topic: str
    ) -> Dict[str, List[str]]:
        """Extract statistics using LLM"""
        try:
            combined_content = "\n\n".join(
                [
                    f"Source: {c['title']}\n{c.get('content', '')[:2000]}"
                    for c in contents
                ]
            )

            prompt = f"""Extract important statistics and numerical data from the following content about "{topic}".
            Categorize them into:
            - Fiscal indicators and targets
            - Budget allocations
            - Growth targets and projections
            
            Content:
            {combined_content[:4000]}
            
            Format each statistic as a clear statement."""

            messages = [{"role": "user", "content": prompt}]
            response = await self.async_openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            )

            # Parse the response into categories
            text = response.choices[0].message.content
            stats = {"fiscal": [], "allocations": [], "targets": []}

            current_category = None
            for line in text.split("\n"):
                line = line.strip()
                if line.lower().startswith("fiscal"):
                    current_category = "fiscal"
                elif line.lower().startswith("budget") or line.lower().startswith(
                    "allocation"
                ):
                    current_category = "allocations"
                elif line.lower().startswith("growth") or line.lower().startswith(
                    "target"
                ):
                    current_category = "targets"
                elif line.startswith("- ") and current_category:
                    stats[current_category].append(line[2:])

            return stats
        except Exception as e:
            logger.error(f"Failed to extract statistics with LLM: {str(e)}")
            return self._extract_statistics_basic(contents)

    async def _execute_tool(self, tool_name: str, input_data: Any, state: Any) -> Any:
        """Execute a tool and handle async properly"""
        try:
            tool = next(t for t in self.tools if t.name == tool_name)
            result = await tool._arun(input_data)
            result = await result
            state.metadata["steps_taken"].append(
                {"tool": tool_name, "timestamp": datetime.now()}
            )
            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            raise ResearchError(f"Tool execution failed: {str(e)}")

    def get_initial_state(self) -> WorkflowState:
        """Create and return initial workflow state"""
        state = WorkflowState()
        state.metadata.update(
            {"errors": [], "start_time": datetime.now(), "steps_taken": []}
        )
        return state

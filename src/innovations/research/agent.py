from typing import List, Dict, Any, Optional
from src.agents.base.base_innovation import BaseInnovationAgent
from src.agents.tools.research_tools import WebSearchTool, ContentExtractorTool, ResearchSynthesizerTool
from src.core.state import WorkflowState
from src.core.exceptions import ResearchError
import asyncio
from datetime import datetime
import backoff
import logging
from src.agents.tools.content_tools import ContentExtractor

logger = logging.getLogger(__name__)

class ResearchAgent(BaseInnovationAgent):
    """Agent for conducting research"""
    
    def __init__(self, search_provider: str = "auto", api_key: Optional[str] = None, cx: Optional[str] = None):
        """Initialize research agent"""
        
        # Initialize tools
        self.tools = [
            WebSearchTool(provider_type=search_provider, api_key=api_key, cx=cx),
            ContentExtractorTool()
        ]
        
        system_prompt = """You are a research assistant. Your task is to:
        1. Search for information on given topics
        2. Extract relevant content from web pages
        3. Synthesize findings into coherent summaries
        Always verify information from multiple sources when possible."""
        
        super().__init__(tools=self.tools, system_prompt=system_prompt)
    
    async def research(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Conduct research on a topic"""
        try:
            search_tool = next(t for t in self.tools if t.name == "web_search")
            results = search_tool._run(query=query, num_results=num_results)
            
            return {
                "results": results,
                "metadata": {
                    "query": query,
                    "num_results": num_results
                }
            }
        except Exception as e:
            logger.error(f"Research failed: {str(e)}")
            raise ResearchError(f"Research failed: {str(e)}")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=30
    )
    async def _identify_subtopics(self, content: str) -> List[str]:
        """Identify important subtopics for deeper research"""
        try:
            messages = [{"role": "user", "content": f"""Analyze this content and identify 2-3 key subtopics that warrant deeper research:
            Content: {content[:2000]}... # Truncated for token limit
            
            Return only the subtopics as a comma-separated list."""}]
            
            response = await self.async_openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                temperature=0.7
            )
            
            subtopics_text = response.choices[0].message.content
            return [t.strip() for t in subtopics_text.split(',')]
        except Exception as e:
            logger.error(f"Error identifying subtopics: {str(e)}")
            return [f"Error identifying subtopics: {str(e)}"]
    
    async def research_topic(self, topic: str, depth: int = 1, max_sources: int = 5) -> Dict[str, Any]:
        """Conduct research on a topic"""
        try:
            if not topic.strip():
                raise ValueError("Topic cannot be empty")
            
            start_time = datetime.now()
            logger.info(f"Starting research on topic: {topic}")
            
            # Get search results
            search_tool = next(t for t in self.tools if t.name == "web_search")
            logger.info("Executing web search...")
            search_results = search_tool._run(topic, max_sources)
            logger.info(f"Found {len(search_results)} search results")
            
            # Extract content from each source
            content_tool = next(t for t in self.tools if t.name == "content_extractor")
            contents = []
            errors = []
            
            for result in search_results[:max_sources]:
                try:
                    if result.get('link'):
                        logger.info(f"Extracting content from: {result['link']}")
                        content = await content_tool._arun(result['link'])
                        if content and content.get('content'):
                            contents.append({
                                'title': result['title'],
                                'content': content['content'],
                                'url': result['link']
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
    
    async def _synthesize_content_with_llm(self, contents: List[Dict[str, str]], topic: str) -> str:
        """Synthesize content using LLM"""
        try:
            # Combine all content with source attribution
            combined_content = "\n\n".join([
                f"Source: {c['title']}\n{c.get('content', '')[:2000]}"
                for c in contents
            ])
            
            prompt = f"""Analyze and synthesize the following content about "{topic}". 
            Provide a clear, concise summary focusing on the main points and key announcements.
            
            Content:
            {combined_content[:4000]}  # Limit total content to avoid token limits
            
            Provide a professional summary in 3-4 paragraphs."""
            
            messages = [{"role": "user", "content": prompt}]
            response = await self.async_openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Failed to synthesize content with LLM: {str(e)}")
            return self._synthesize_content_basic(contents)
    
    async def _extract_key_findings_with_llm(self, contents: List[Dict[str, str]], topic: str) -> Dict[str, List[str]]:
        """Extract key findings using LLM"""
        try:
            combined_content = "\n\n".join([
                f"Source: {c['title']}\n{c.get('content', '')[:2000]}"
                for c in contents
            ])
            
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
                max_tokens=1000
            )
            
            # Parse the response into categories
            text = response.choices[0].message.content
            categories = text.split('\n\n')
            findings = {
                "tax_changes": [],
                "economic_measures": [],
                "social_initiatives": [],
                "infrastructure": [],
                "other_highlights": []
            }
            
            current_category = None
            for line in text.split('\n'):
                line = line.strip()
                if line.lower().startswith('tax'):
                    current_category = "tax_changes"
                elif line.lower().startswith('economic'):
                    current_category = "economic_measures"
                elif line.lower().startswith('social'):
                    current_category = "social_initiatives"
                elif line.lower().startswith('infrastructure'):
                    current_category = "infrastructure"
                elif line.lower().startswith('other'):
                    current_category = "other_highlights"
                elif line.startswith('- ') and current_category:
                    findings[current_category].append(line[2:])
            
            return findings
        except Exception as e:
            logger.error(f"Failed to extract key findings with LLM: {str(e)}")
            return self._extract_key_findings_basic(contents)
    
    async def _extract_statistics_with_llm(self, contents: List[Dict[str, str]], topic: str) -> Dict[str, List[str]]:
        """Extract statistics using LLM"""
        try:
            combined_content = "\n\n".join([
                f"Source: {c['title']}\n{c.get('content', '')[:2000]}"
                for c in contents
            ])
            
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
                max_tokens=1000
            )
            
            # Parse the response into categories
            text = response.choices[0].message.content
            stats = {
                "fiscal": [],
                "allocations": [],
                "targets": []
            }
            
            current_category = None
            for line in text.split('\n'):
                line = line.strip()
                if line.lower().startswith('fiscal'):
                    current_category = "fiscal"
                elif line.lower().startswith('budget') or line.lower().startswith('allocation'):
                    current_category = "allocations"
                elif line.lower().startswith('growth') or line.lower().startswith('target'):
                    current_category = "targets"
                elif line.startswith('- ') and current_category:
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
            state.metadata["steps_taken"].append({
                "tool": tool_name,
                "timestamp": datetime.now()
            })
            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            raise ResearchError(f"Tool execution failed: {str(e)}")
    
    def get_initial_state(self) -> WorkflowState:
        """Create and return initial workflow state"""
        state = WorkflowState()
        state.metadata.update({
            "errors": [],
            "start_time": datetime.now(),
            "steps_taken": []
        })
        return state 
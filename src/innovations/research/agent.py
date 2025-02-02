from typing import List, Dict, Any, Optional
from src.agents.base.base_innovation import BaseInnovationAgent
from src.agents.tools.research_tools import WebSearchTool, ContentExtractorTool, ResearchSynthesizerTool
from src.core.state import WorkflowState
from src.core.exceptions import ResearchError
import asyncio
from datetime import datetime
import backoff
import logging

logger = logging.getLogger(__name__)

class ResearchAgent(BaseInnovationAgent):
    """Advanced research agent capable of conducting comprehensive research"""
    
    def __init__(self):
        tools = [
            WebSearchTool(),
            ContentExtractorTool(),
            ResearchSynthesizerTool()
        ]
        
        system_prompt = """You are an advanced research agent specialized in conducting thorough research.
        Follow these guidelines:
        1. Break down complex topics into key aspects
        2. Search multiple sources for each aspect
        3. Verify information across sources
        4. Synthesize findings into coherent insights
        5. Cite sources for all key information
        6. Maintain objectivity in analysis
        """
        
        super().__init__(tools=tools, system_prompt=system_prompt)
    
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
    
    async def research_topic(self, topic: str, depth: int = 2, max_sources: int = 5) -> Dict[str, Any]:
        """Conduct comprehensive research on a topic"""
        if not topic.strip():
            raise ResearchError("Empty topic provided")
            
        try:
            # Initialize research state
            state = self.get_initial_state()
            state.metadata.update({
                "topic": topic,
                "depth": depth,
                "max_sources": max_sources,
                "start_time": datetime.now(),
                "errors": []
            })
            
            # Try different search variations
            search_variations = [
                topic,
                f"latest news about {topic}",
                f"recent developments in {topic}",
                f"current information about {topic}"
            ]
            
            all_results = []
            for query in search_variations:
                results = await self._execute_tool(
                    "web_search",
                    query,
                    state
                )
                all_results.extend(results)
                if len(all_results) >= max_sources:
                    break
            
            # Deduplicate results
            seen_links = set()
            unique_results = []
            for r in all_results:
                if r['link'] not in seen_links:
                    seen_links.add(r['link'])
                    unique_results.append(r)
            
            if not unique_results:
                logger.warning(f"No search results found for topic: {topic}")
                return {
                    "topic": topic,
                    "summary": "No relevant information found.",
                    "key_points": ["No information available for the specified topic."],
                    "sources": [],
                    "metadata": {
                        "depth": depth,
                        "source_count": 0,
                        "completion_time": datetime.now(),
                        "duration": str(datetime.now() - state.metadata["start_time"]),
                        "errors": ["No search results found"]
                    }
                }
            
            # Phase 2: Content Extraction
            content_data = []
            for result in unique_results[:max_sources]:
                try:
                    content = await self._execute_tool(
                        "content_extractor",
                        result['link'],
                        state
                    )
                    content_data.append(content)
                except Exception as e:
                    state.metadata["errors"].append(f"Content extraction error: {str(e)}")
            
            # Phase 3: Deep Research (if depth > 1)
            if depth > 1:
                for content in content_data:
                    # Extract and research subtopics
                    subtopics = await self._identify_subtopics(content['content'])
                    for subtopic in subtopics:
                        sub_results = await self.research_topic(
                            subtopic,
                            depth=depth-1,
                            max_sources=max_sources-2
                        )
                        content_data.extend(sub_results.get('findings', []))
            
            # Phase 4: Synthesis
            synthesis = await self._execute_tool(
                "research_synthesizer",
                content_data,
                state
            )
            
            # Final Processing
            research_output = {
                "topic": topic,
                "summary": synthesis['summary'],
                "key_findings": {
                    "Tax and Financial Changes": synthesis['key_points']['tax_changes'],
                    "Economic Measures": synthesis['key_points']['economic_measures'],
                    "Social Initiatives": synthesis['key_points']['social_initiatives'],
                    "Infrastructure Development": synthesis['key_points']['infrastructure'],
                    "Other Important Highlights": synthesis['key_points']['other_highlights']
                },
                "statistics": {
                    "Fiscal Indicators": synthesis['statistics']['fiscal'],
                    "Budget Allocations": synthesis['statistics']['allocations'],
                    "Targets and Goals": synthesis['statistics']['targets']
                },
                "sources": synthesis['sources'],
                "metadata": {
                    "depth": depth,
                    "source_count": len(synthesis['sources']),
                    "completion_time": datetime.now(),
                    "duration": str(datetime.now() - state.metadata["start_time"]),
                    "errors": state.metadata.get("errors", [])
                }
            }
            
            return research_output
            
        except Exception as e:
            raise ResearchError(f"Research failed: {str(e)}")
    
    async def _execute_tool(self, tool_name: str, input_data: Any, state: WorkflowState) -> Any:
        """Execute a tool and update state"""
        try:
            tool = next(t for t in self.tools if t.name == tool_name)
            result = await tool._arun(input_data)
            state.metadata["steps_taken"].append({
                "tool": tool_name,
                "timestamp": datetime.now()
            })
            return result
        except StopIteration:
            raise ResearchError(f"Tool '{tool_name}' not found")
        except Exception as e:
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
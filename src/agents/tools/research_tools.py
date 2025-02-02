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

logger = logging.getLogger(__name__)

class WebSearchConfig(BaseModel):
    engine: str = "google"
    max_results: int = 5
    retry_attempts: int = 3
    retry_delay: float = 2.0

class WebSearchTool(BaseTool):
    """Tool for searching the web"""
    name: str = "web_search"
    description: str = "Search the web for information on a given topic"
    config: WebSearchConfig = Field(default_factory=WebSearchConfig)
    api_key: str = Field(default_factory=lambda: os.getenv('SERPAPI_API_KEY', ''))
    
    def __init__(self, **data):
        super().__init__(**data)
        self.config = WebSearchConfig()
        self.api_key = os.getenv('SERPAPI_API_KEY')
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY environment variable not set")
    
    def _run(self, query: str) -> List[Dict[str, str]]:
        """Synchronous run method required by BaseTool"""
        try:
            # Basic search parameters
            params = {
                "api_key": self.api_key,  # Use the actual API key string
                "q": query,
                "google_domain": "google.co.in",
                "gl": "in",
                "hl": "en",
                "num": 10,
                "start": 0
            }
            
            results = []
            
            # Try web search
            web_params = params.copy()
            web_params["engine"] = "google"
            
            logger.debug(f"Performing web search for query: {query}")
            search = GoogleSearch(web_params)
            search_results = search.get_dict()
            
            if "error" in search_results:
                logger.error(f"SerpAPI error: {search_results['error']}")
                return []
            
            # Extract organic results
            if "organic_results" in search_results:
                for r in search_results.get("organic_results", []):
                    if r.get("link") and r.get("title"):
                        results.append({
                            'title': r.get('title', '').strip(),
                            'link': r.get('link', '').strip(),
                            'snippet': r.get('snippet', '').strip()
                        })
                        logger.debug(f"Found organic result: {r.get('title')}")
            
            # Try news search if needed
            if len(results) < self.config.max_results:
                news_params = params.copy()
                news_params["engine"] = "google_news"
                
                logger.debug(f"Performing news search for query: {query}")
                news_search = GoogleSearch(news_params)
                news_results = news_search.get_dict()
                
                if "news_results" in news_results:
                    for r in news_results.get("news_results", []):
                        if r.get("link") and r.get("title"):
                            results.append({
                                'title': r.get('title', '').strip(),
                                'link': r.get('link', '').strip(),
                                'snippet': r.get('snippet', r.get('description', '')).strip()
                            })
                            logger.debug(f"Found news result: {r.get('title')}")
            
            # Deduplicate and limit results
            seen_links = set()
            unique_results = []
            for r in results:
                if r['link'] not in seen_links:
                    seen_links.add(r['link'])
                    unique_results.append(r)
                if len(unique_results) >= self.config.max_results:
                    break
            
            logger.info(f"Found {len(unique_results)} unique search results for query: {query}")
            return unique_results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}", exc_info=True)
            return []
    
    async def _arun(self, query: str) -> List[Dict[str, str]]:
        """Async run method"""
        if not query:
            return []
            
        try:
            # Run sync method in thread pool since SerpAPI is sync
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._run, query)
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []

class ContentExtractorConfig(BaseModel):
    timeout: int = 30
    max_content_length: int = 10000
    fallback_content: str = "Content extraction failed."
    retry_attempts: int = 2
    retry_delay: float = 1.0

class ContentExtractorTool(BaseTool):
    """Tool for extracting content from web pages"""
    name: str = "content_extractor"
    description: str = "Extract and process content from web pages"
    config: ContentExtractorConfig = Field(default_factory=ContentExtractorConfig)
    
    def __init__(self, **data):
        super().__init__(**data)
        self.config = ContentExtractorConfig()
    
    def _run(self, url: str) -> Dict[str, Any]:
        """Synchronous run method required by BaseTool"""
        try:
            with httpx.Client(
                timeout=self.config.timeout,
                follow_redirects=True,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            ) as client:
                response = client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract title
                title = soup.title.string if soup.title else ''
                
                # Try multiple content extraction strategies
                content = ""
                
                # Strategy 1: Look for article content
                article = soup.find(['article', 'main'])
                if article:
                    content = article.get_text(separator='\n', strip=True)
                
                # Strategy 2: Look for div with content
                if not content:
                    for div in soup.find_all('div', class_=lambda x: x and ('content' in x.lower() or 'article' in x.lower())):
                        content = div.get_text(separator='\n', strip=True)
                        if content:
                            break
                
                # Strategy 3: Fallback to paragraphs
                if not content:
                    paragraphs = soup.find_all('p')
                    content = '\n'.join(p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 50)
                
                if content:
                    logger.info(f"Successfully extracted content from {url}")
                    return {
                        'content': content[:self.config.max_content_length],
                        'metadata': {
                            'title': title,
                            'url': url,
                            'source': str(response.url)
                        }
                    }
                    
        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {e}")
            
        return self._create_error_response(f"Failed to extract content from {url}")
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=30
    )
    async def _arun(self, url: str) -> Dict[str, Any]:
        """Async run method"""
        if not url or not url.startswith('http'):
            return self._create_error_response("Invalid URL provided")
            
        try:
            async with httpx.AsyncClient(
                timeout=self.config.timeout,
                follow_redirects=True,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract title
                title = soup.title.string if soup.title else ''
                
                # Try multiple content extraction strategies
                content = ""
                
                # Strategy 1: Look for article content
                article = soup.find(['article', 'main'])
                if article:
                    content = article.get_text(separator='\n', strip=True)
                
                # Strategy 2: Look for div with content
                if not content:
                    for div in soup.find_all('div', class_=lambda x: x and ('content' in x.lower() or 'article' in x.lower())):
                        content = div.get_text(separator='\n', strip=True)
                        if content:
                            break
                
                # Strategy 3: Fallback to paragraphs
                if not content:
                    paragraphs = soup.find_all('p')
                    content = '\n'.join(p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 50)
                
                if content:
                    logger.info(f"Successfully extracted content from {url}")
                    return {
                        'content': content[:self.config.max_content_length],
                        'metadata': {
                            'title': title,
                            'url': url,
                            'source': str(response.url)
                        }
                    }
                    
        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {e}")
            
        return self._create_error_response(f"Failed to extract content from {url}")
    
    def _create_error_response(self, error_msg: str) -> Dict[str, Any]:
        return {
            'content': self.config.fallback_content,
            'metadata': {
                'title': 'Error',
                'description': error_msg,
                'url': 'https://example.com/error'
            }
        }

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
            valid_data = [d for d in research_data if isinstance(d, dict) and 'content' in d]
            
            if not valid_data:
                logger.warning("No valid research data provided for synthesis")
                return self._create_fallback_synthesis()
            
            # Combine all content
            all_content = "\n".join(d['content'] for d in valid_data)
            
            # Extract key sections
            synthesis = {
                'summary': self._extract_summary(all_content),
                'key_points': {
                    'tax_changes': [],
                    'economic_measures': [],
                    'social_initiatives': [],
                    'infrastructure': [],
                    'other_highlights': []
                },
                'statistics': {
                    'fiscal': [],
                    'allocations': [],
                    'targets': []
                },
                'sources': self._format_sources(valid_data)
            }
            
            # Process content to extract structured information
            for data in valid_data:
                content = data['content']
                
                # Extract key points by category
                synthesis['key_points']['tax_changes'].extend(
                    self._extract_category_points(content, ['tax', 'income', 'revenue'])
                )
                synthesis['key_points']['economic_measures'].extend(
                    self._extract_category_points(content, ['economy', 'finance', 'market', 'industry'])
                )
                synthesis['key_points']['social_initiatives'].extend(
                    self._extract_category_points(content, ['welfare', 'social', 'education', 'health'])
                )
                synthesis['key_points']['infrastructure'].extend(
                    self._extract_category_points(content, ['infrastructure', 'development', 'construction'])
                )
                
                # Extract statistics
                synthesis['statistics']['fiscal'].extend(
                    self._extract_statistics(content, ['deficit', 'gdp', 'growth'])
                )
                synthesis['statistics']['allocations'].extend(
                    self._extract_statistics(content, ['allocation', 'fund', 'budget'])
                )
            
            # Deduplicate and clean
            for category in synthesis['key_points']:
                synthesis['key_points'][category] = list(set(synthesis['key_points'][category]))
                synthesis['key_points'][category] = [p for p in synthesis['key_points'][category] if len(p) > 20]
            
            for category in synthesis['statistics']:
                synthesis['statistics'][category] = list(set(synthesis['statistics'][category]))
            
            logger.info(f"Synthesized research data into {len(synthesis['key_points'])} categories")
            return synthesis
            
        except Exception as e:
            logger.error(f"Research synthesis failed: {str(e)}")
            return self._create_fallback_synthesis()
    
    def _extract_summary(self, content: str) -> str:
        """Extract a concise summary from the content"""
        # Find sentences that look like summaries
        sentences = content.split('.')
        summary_sentences = [s for s in sentences if any(w in s.lower() for w in 
            ['highlight', 'announce', 'present', 'introduce', 'budget'])]
        
        if summary_sentences:
            return '. '.join(summary_sentences[:3]).strip() + '.'
        return "No summary available."
    
    def _extract_category_points(self, content: str, keywords: List[str]) -> List[str]:
        """Extract points related to specific categories"""
        sentences = content.split('.')
        category_points = []
        
        for sentence in sentences:
            if any(k in sentence.lower() for k in keywords):
                clean_sentence = sentence.strip()
                if clean_sentence and len(clean_sentence) > 20:
                    category_points.append(clean_sentence)
        
        return category_points
    
    def _extract_statistics(self, content: str, keywords: List[str]) -> List[str]:
        """Extract statistical information"""
        sentences = content.split('.')
        stats = []
        
        for sentence in sentences:
            if any(k in sentence.lower() for k in keywords) and any(c.isdigit() for c in sentence):
                clean_sentence = sentence.strip()
                if clean_sentence:
                    stats.append(clean_sentence)
        
        return stats
    
    def _format_sources(self, data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format source information"""
        sources = []
        seen_urls = set()
        
        for d in data:
            if 'metadata' in d and 'url' in d['metadata']:
                url = d['metadata']['url']
                if url not in seen_urls and url != 'https://example.com/error':
                    sources.append({
                        'title': d['metadata'].get('title', 'Unknown Source'),
                        'url': url
                    })
                    seen_urls.add(url)
        
        return sources
    
    def _create_fallback_synthesis(self) -> Dict[str, Any]:
        return {
            'summary': 'Unable to synthesize meaningful findings.',
            'key_points': {
                'tax_changes': [],
                'economic_measures': [],
                'social_initiatives': [],
                'infrastructure': [],
                'other_highlights': []
            },
            'statistics': {
                'fiscal': [],
                'allocations': [],
                'targets': []
            },
            'sources': []
        } 
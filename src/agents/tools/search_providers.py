from typing import List, Dict, Optional
from abc import ABC, abstractmethod
import logging
from duckduckgo_search import DDGS
from serpapi import GoogleSearch
from googleapiclient.discovery import build
from src.core.config import get_settings
import aiohttp
import json
from urllib.parse import quote
from bs4 import BeautifulSoup
import asyncio
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

class SearchProvider(ABC):
    @abstractmethod
    def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        pass

class GoogleSearchProvider(SearchProvider):
    def __init__(self, api_key: str, cx: str):
        logger.info(f"Initializing Google Search with API key: {api_key[:5]}... and CX: {cx[:10]}...")
        try:
            self.service = build("customsearch", "v1", developerKey=api_key)
            self.cx = cx
            logger.info("Google Search service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Search: {str(e)}", exc_info=True)
            raise

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        try:
            logger.info(f"Performing Google search for: {query}")
            results = []
            
            # Execute search in batches of 10 (Google CSE limit)
            for i in range(0, num_results, 10):
                response = self.service.cse().list(
                    q=query,
                    cx=self.cx,
                    num=min(10, num_results - i),
                    start=i + 1,  # Google uses 1-based indexing
                    fields="items(title,link,snippet)",
                    dateRestrict="m1"  # Restrict to last month
                ).execute()
                
                if 'items' in response:
                    for item in response['items']:
                        link = item.get('link', '')
                        title = item.get('title', '')
                        snippet = item.get('snippet', '')
                        
                        if not link or not link.startswith(('http://', 'https://')):
                            logger.warning(f"Invalid or empty URL: {link}")
                            continue
                            
                        results.append({
                            'title': title,
                            'link': link,
                            'snippet': snippet
                        })
                        
                        if len(results) >= num_results:
                            break
                else:
                    logger.warning(f"No items found in response. Keys present: {list(response.keys())}")
                
                if len(results) >= num_results:
                    break
            
            logger.info(f"Search completed. Found {len(results)} results")
            return results[:num_results]

        except Exception as e:
            logger.error(f"Google search failed: {str(e)}", exc_info=True)
            return []

class DuckDuckGoProvider(SearchProvider):
    def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results))
                return [
                    {
                        'title': r.get('title', ''),
                        'link': r.get('link', ''),
                        'snippet': r.get('body', '')
                    }
                    for r in results
                ]
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {str(e)}")
            return []

class SerpAPIProvider(SearchProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        logger.info("Initializing SerpAPI provider")

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        try:
            logger.info(f"Performing SerpAPI search for: {query}")
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": num_results,
                "engine": "google"  # Use Google engine
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            if 'organic_results' in results:
                valid_results = []
                for r in results['organic_results']:
                    link = r.get('link', '')
                    title = r.get('title', '')
                    snippet = r.get('snippet', '')
                    
                    if not link or not link.startswith(('http://', 'https://')):
                        logger.warning(f"Invalid or empty URL: {link}")
                        continue
                        
                    valid_results.append({
                        'title': title,
                        'link': link,
                        'snippet': snippet
                    })
                    
                    if len(valid_results) >= num_results:
                        break
                
                logger.info(f"Found {len(valid_results)} valid results")
                return valid_results
                
            logger.warning("No organic results found in SerpAPI response")
            return []
            
        except Exception as e:
            logger.error(f"SerpAPI search failed: {str(e)}", exc_info=True)
            return []

class BingSearchProvider(SearchProvider):
    """Bing Web Search API provider"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://api.bing.microsoft.com/v7.0/search"
        self.headers = {
            'Ocp-Apim-Subscription-Key': api_key
        }

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        try:
            logger.info(f"Performing Bing search for: {query}")
            
            params = {
                'q': query,
                'count': num_results,
                'responseFilter': 'Webpages',
                'freshness': 'Day'  # Get recent results
            }
            
            async def fetch():
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.endpoint, headers=self.headers, params=params) as response:
                        return await response.json()
            
            response = asyncio.run(fetch())
            
            if 'webPages' in response and 'value' in response['webPages']:
                results = []
                for item in response['webPages']['value']:
                    results.append({
                        'title': item.get('name', ''),
                        'link': item.get('url', ''),
                        'snippet': item.get('snippet', '')
                    })
                logger.info(f"Found {len(results)} results from Bing")
                return results[:num_results]
            
            logger.warning("No results found in Bing response")
            return []
            
        except Exception as e:
            logger.error(f"Bing search failed: {str(e)}", exc_info=True)
            return []

class CustomWebSearchProvider(SearchProvider):
    """Custom web search provider using direct web scraping"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.search_engines = [
            {
                'name': 'Brave',
                'url': 'https://search.brave.com/search',
                'param': 'q'
            },
            {
                'name': 'Qwant',
                'url': 'https://www.qwant.com/',
                'param': 'q'
            },
            {
                'name': 'Ecosia',
                'url': 'https://www.ecosia.org/search',
                'param': 'q'
            }
        ]

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Search across multiple search engines"""
        try:
            logger.info(f"Performing custom web search for: {query}")
            
            results = []
            for engine in self.search_engines:
                try:
                    engine_results = self._search_engine(engine, query, num_results)
                    results.extend(engine_results)
                    if len(results) >= num_results:
                        break
                except Exception as e:
                    logger.warning(f"Search failed for {engine['name']}: {str(e)}")
                    continue
            
            # Remove duplicates based on URL
            unique_results = []
            seen_urls = set()
            for result in results:
                if result['link'] not in seen_urls:
                    seen_urls.add(result['link'])
                    unique_results.append(result)
            
            return unique_results[:num_results]
            
        except Exception as e:
            logger.error(f"Custom web search failed: {str(e)}", exc_info=True)
            return []

    def _search_engine(self, engine: Dict[str, str], query: str, num_results: int) -> List[Dict[str, str]]:
        """Search using a specific search engine"""
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        params = {engine['param']: query}
        
        async def fetch():
            async with aiohttp.ClientSession() as session:
                async with session.get(engine['url'], headers=headers, params=params) as response:
                    return await response.text()
        
        html = asyncio.run(fetch())
        soup = BeautifulSoup(html, 'html.parser')
        
        results = []
        
        # Different parsing logic for each engine
        if engine['name'] == 'Brave':
            for result in soup.select('.snippet'):
                title = result.select_one('.title')
                link = result.select_one('.url')
                snippet = result.select_one('.description')
                if title and link:
                    results.append({
                        'title': title.text.strip(),
                        'link': link.text.strip(),
                        'snippet': snippet.text.strip() if snippet else ''
                    })
        
        elif engine['name'] == 'Qwant':
            for result in soup.select('.result'):
                title = result.select_one('.title')
                link = result.select_one('.url')
                snippet = result.select_one('.desc')
                if title and link:
                    results.append({
                        'title': title.text.strip(),
                        'link': link['href'],
                        'snippet': snippet.text.strip() if snippet else ''
                    })
        
        elif engine['name'] == 'Ecosia':
            for result in soup.select('.result-body'):
                title = result.select_one('.result-title')
                link = result.select_one('.result-url')
                snippet = result.select_one('.result-snippet')
                if title and link:
                    results.append({
                        'title': title.text.strip(),
                        'link': link['href'],
                        'snippet': snippet.text.strip() if snippet else ''
                    })
        
        return results[:num_results]

def get_search_provider(provider_type: str = "auto", api_key: Optional[str] = None, cx: Optional[str] = None) -> SearchProvider:
    settings = get_settings()
    
    # Try Google first (as default)
    if provider_type in ["auto", "google"]:
        api_key = api_key or settings.GOOGLE_API_KEY
        cx = cx or settings.GOOGLE_CSE_ID
        if api_key and cx:
            try:
                return GoogleSearchProvider(api_key, cx)
            except Exception as e:
                logger.warning(f"Failed to initialize Google Search: {str(e)}")
                if provider_type == "google":
                    raise  # If specifically requested Google, raise the error
    
    # Try DuckDuckGo as fallback
    if provider_type in ["auto", "duckduckgo"]:
        logger.info("Using DuckDuckGo as fallback search provider")
        return DuckDuckGoProvider()
    
    # If no suitable provider found and not auto
    if provider_type != "auto":
        raise ValueError(f"No suitable search provider found for type: {provider_type}")
    
    logger.warning("No suitable provider found. Using DuckDuckGo as fallback.")
    return DuckDuckGoProvider() 
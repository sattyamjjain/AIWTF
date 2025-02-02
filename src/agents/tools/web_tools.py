from langchain_core.tools import BaseTool
from bs4 import BeautifulSoup
import requests
from typing import Optional, Any

class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = "Search the web for information about a topic"
    
    def _run(self, query: str) -> str:
        # Simple implementation using DuckDuckGo
        url = f"https://duckduckgo.com/html/?q={query}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        for result in soup.find_all('div', class_='result'):
            title = result.find('h2').text if result.find('h2') else ''
            snippet = result.find('a', class_='result__snippet').text if result.find('a', class_='result__snippet') else ''
            results.append(f"Title: {title}\nSnippet: {snippet}\n")
            
            if len(results) >= 3:  # Limit to top 3 results
                break
                
        return "\n".join(results)

class WebBrowseTool(BaseTool):
    name: str = "web_browse"
    description: str = "Browse a specific webpage and extract its content"
    
    def _run(self, url: str) -> str:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:4000]  # Limit response size 
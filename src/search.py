"""
Web search functionality using DuckDuckGo Search API.
"""
import logging
from typing import List, Dict, Optional
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


class WebSearcher:
    """Handles web search operations using DuckDuckGo."""
    
    def __init__(self, max_results: int = 5):
        """
        Initialize the web searcher.
        
        Args:
            max_results: Maximum number of search results to return
        """
        self.max_results = max_results
        self.ddgs = DDGS()
    
    def search(self, query: str) -> List[Dict[str, str]]:
        """
        Search the web for the given query.
        
        Args:
            query: The search query string
            
        Returns:
            List of dictionaries containing search results with keys:
            - title: Page title
            - url: Page URL
            - snippet: Brief description/snippet
        """
        try:
            logger.info(f"Searching for: {query}")
            
            # Perform the search
            results = list(self.ddgs.text(
                keywords=query,
                max_results=self.max_results,
                region='wt-wt',  # Worldwide
                safesearch='moderate'
            ))
            
            # Format results
            formatted_results = []
            for i, result in enumerate(results):
                formatted_result = {
                    'title': result.get('title', f'Result {i+1}'),
                    'url': result.get('href', ''),
                    'snippet': result.get('body', '')
                }
                formatted_results.append(formatted_result)
            
            logger.info(f"Found {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []
    
    def get_search_debug_info(self, query: str) -> Dict:
        """
        Get detailed search information for debugging.
        
        Args:
            query: The search query string
            
        Returns:
            Dictionary containing debug information
        """
        try:
            results = self.search(query)
            return {
                'query': query,
                'results_count': len(results),
                'results': results,
                'status': 'success'
            }
        except Exception as e:
            return {
                'query': query,
                'results_count': 0,
                'results': [],
                'status': 'error',
                'error': str(e)
            } 
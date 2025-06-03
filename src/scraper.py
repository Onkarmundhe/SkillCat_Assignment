"""
Web scraping functionality to extract main text content from web pages.
"""
import logging
import requests
import warnings
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from newspaper import Article
import time
import random

# Suppress newspaper3k regex warnings
warnings.filterwarnings("ignore", message="invalid escape sequence", category=SyntaxWarning)

logger = logging.getLogger(__name__)


class WebScraper:
    """Handles web scraping operations to extract main text content."""
    
    def __init__(self, timeout: int = 10, max_retries: int = 2):
        """
        Initialize the web scraper.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        
        # Rotate between different user agents to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        self._update_headers()
    
    def _update_headers(self):
        """Update session headers with a random user agent."""
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def extract_text_newspaper(self, url: str) -> Optional[str]:
        """
        Extract text using newspaper3k library.
        
        Args:
            url: URL to scrape
            
        Returns:
            Extracted text content or None if failed
        """
        try:
            # Suppress newspaper3k warnings during execution
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                article = Article(url)
                article.download()
                article.parse()
            
            if article.text:
                return article.text.strip()
            return None
            
        except Exception as e:
            logger.warning(f"Newspaper extraction failed for {url}: {str(e)}")
            return None
    
    def extract_text_beautifulsoup(self, url: str) -> Optional[str]:
        """
        Extract text using BeautifulSoup as fallback.
        
        Args:
            url: URL to scrape
            
        Returns:
            Extracted text content or None if failed
        """
        try:
            # Update headers for each request
            self._update_headers()
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # Get text from main content areas
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.body
            
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
                # Clean up extra whitespace
                text = ' '.join(text.split())
                return text if len(text) > 100 else None
            
            return None
            
        except Exception as e:
            logger.warning(f"BeautifulSoup extraction failed for {url}: {str(e)}")
            return None
    
    def scrape_url(self, url: str) -> Optional[str]:
        """
        Scrape text content from a single URL with retry logic.
        
        Args:
            url: URL to scrape
            
        Returns:
            Extracted text content or None if failed
        """
        for attempt in range(self.max_retries + 1):
            try:
                # Try newspaper3k first (better for articles)
                text = self.extract_text_newspaper(url)
                if text and len(text) > 100:
                    logger.info(f"Successfully scraped {url} using newspaper3k")
                    return text
                
                # Fallback to BeautifulSoup
                text = self.extract_text_beautifulsoup(url)
                if text:
                    logger.info(f"Successfully scraped {url} using BeautifulSoup")
                    return text
                
                if attempt < self.max_retries:
                    # Random delay between retries to avoid rate limiting
                    time.sleep(random.uniform(1, 3))
                    
            except Exception as e:
                logger.error(f"Scraping attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < self.max_retries:
                    time.sleep(random.uniform(1, 3))
        
        logger.error(f"Failed to scrape {url} after {self.max_retries + 1} attempts")
        return None
    
    def scrape_search_results(self, search_results: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Scrape text content from multiple search results.
        
        Args:
            search_results: List of search result dictionaries
            
        Returns:
            List of results with added 'content' field containing scraped text
        """
        scraped_results = []
        
        for i, result in enumerate(search_results):
            url = result.get('url', '')
            if not url:
                continue
            
            logger.info(f"Scraping result {i+1}/{len(search_results)}: {url}")
            
            content = self.scrape_url(url)
            
            # Add content to result
            result_with_content = result.copy()
            result_with_content['content'] = content or result.get('snippet', '')
            result_with_content['scrape_success'] = content is not None
            
            scraped_results.append(result_with_content)
            
            # Small delay between requests to be respectful
            if i < len(search_results) - 1:
                time.sleep(random.uniform(0.5, 1.5))
        
        successful_scrapes = sum(1 for r in scraped_results if r.get('scrape_success'))
        logger.info(f"Successfully scraped {successful_scrapes}/{len(search_results)} URLs")
        
        return scraped_results 
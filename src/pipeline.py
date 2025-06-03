"""
Main pipeline that orchestrates the Ask the Web functionality.
"""
import logging
import time
from typing import Dict, List, Tuple, Optional
from .search import WebSearcher
from .scraper import WebScraper
from .llm import GeminiLLM

logger = logging.getLogger(__name__)


class AskTheWebPipeline:
    """Main pipeline for the Ask the Web application."""
    
    def __init__(self, gemini_api_key: Optional[str] = None, enable_quality_check: bool = True):
        """
        Initialize the pipeline with all components.
        
        Args:
            gemini_api_key: Gemini API key (if None, will use environment variable)
            enable_quality_check: Whether to enable citation quality checking
        """
        self.searcher = WebSearcher(max_results=5)
        self.scraper = WebScraper(timeout=10, max_retries=2)
        self.llm = GeminiLLM(api_key=gemini_api_key)
        self.enable_quality_check = enable_quality_check
        
        # Metrics tracking
        self.last_query_metrics = {}
    
    def process_query(self, question: str) -> Dict:
        """
        Process a user question through the complete pipeline.
        
        Args:
            question: User's question
            
        Returns:
            Dictionary containing:
            - answer: Generated answer with citations
            - sources: List of source information
            - debug_info: Debug information including search results
            - metrics: Performance metrics
            - quality_check: Citation quality results (if enabled)
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing query: {question}")
            
            # Step 1: Search
            search_start = time.time()
            search_results = self.searcher.search(question)
            search_time = time.time() - search_start
            
            if not search_results:
                return {
                    'answer': "I couldn't find any relevant search results for your question. Please try rephrasing your query.",
                    'sources': [],
                    'debug_info': {
                        'search_results': [],
                        'scraped_results': [],
                        'status': 'no_search_results'
                    },
                    'metrics': {
                        'total_time': time.time() - start_time,
                        'search_time': search_time,
                        'scrape_time': 0,
                        'llm_time': 0,
                        'quality_check_time': 0,
                        'search_results_count': 0,
                        'successful_scrapes': 0
                    },
                    'quality_check': []
                }
            
            # Step 2: Scrape
            scrape_start = time.time()
            scraped_results = self.scraper.scrape_search_results(search_results)
            scrape_time = time.time() - scrape_start
            
            # Filter out results without content
            valid_results = [r for r in scraped_results if r.get('content') and len(r['content']) > 50]
            
            if not valid_results:
                return {
                    'answer': "I found search results but couldn't extract readable content from any of the pages. Please try a different query.",
                    'sources': [],
                    'debug_info': {
                        'search_results': search_results,
                        'scraped_results': scraped_results,
                        'status': 'no_valid_content'
                    },
                    'metrics': {
                        'total_time': time.time() - start_time,
                        'search_time': search_time,
                        'scrape_time': scrape_time,
                        'llm_time': 0,
                        'quality_check_time': 0,
                        'search_results_count': len(search_results),
                        'successful_scrapes': len(valid_results)
                    },
                    'quality_check': []
                }
            
            # Step 3: Generate answer with LLM
            llm_start = time.time()
            answer, sources = self.llm.generate_answer(question, valid_results)
            llm_time = time.time() - llm_start
            
            # Step 4: Citation Quality Check (if enabled)
            quality_check_results = []
            quality_check_time = 0
            
            if self.enable_quality_check and sources:
                quality_start = time.time()
                try:
                    quality_check_results = self.llm.check_citation_quality(answer, sources)
                    quality_check_time = time.time() - quality_start
                    logger.info(f"Citation quality check completed in {quality_check_time:.2f}s")
                except Exception as e:
                    logger.error(f"Citation quality check failed: {str(e)}")
                    quality_check_time = time.time() - quality_start
            
            total_time = time.time() - start_time
            
            # Store metrics
            metrics = {
                'total_time': total_time,
                'search_time': search_time,
                'scrape_time': scrape_time,
                'llm_time': llm_time,
                'quality_check_time': quality_check_time,
                'search_results_count': len(search_results),
                'successful_scrapes': len(valid_results),
                'tokens_used': 'N/A',  # Gemini doesn't provide token count in free tier
                'quality_checks_performed': len(quality_check_results)
            }
            
            self.last_query_metrics = metrics
            
            logger.info(f"Query processed successfully in {total_time:.2f}s")
            
            return {
                'answer': answer,
                'sources': sources,
                'debug_info': {
                    'search_results': search_results,
                    'scraped_results': scraped_results,
                    'valid_results': valid_results,
                    'status': 'success'
                },
                'metrics': metrics,
                'quality_check': quality_check_results
            }
            
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}")
            return {
                'answer': f"An error occurred while processing your question: {str(e)}",
                'sources': [],
                'debug_info': {
                    'search_results': [],
                    'scraped_results': [],
                    'status': 'error',
                    'error': str(e)
                },
                'metrics': {
                    'total_time': time.time() - start_time,
                    'search_time': 0,
                    'scrape_time': 0,
                    'llm_time': 0,
                    'quality_check_time': 0,
                    'search_results_count': 0,
                    'successful_scrapes': 0
                },
                'quality_check': []
            }
    
    def get_last_metrics(self) -> Dict:
        """
        Get metrics from the last query.
        
        Returns:
            Dictionary with performance metrics
        """
        return self.last_query_metrics.copy()
    
    def health_check(self) -> Dict[str, bool]:
        """
        Check if all components are properly configured.
        
        Returns:
            Dictionary with component health status
        """
        try:
            return {
                'searcher': True,  # DuckDuckGo doesn't require API key
                'scraper': True,   # Basic HTTP requests
                'llm': bool(self.llm.api_key),
                'quality_check': self.enable_quality_check and bool(self.llm.api_key),
                'overall': bool(self.llm.api_key)
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'searcher': False,
                'scraper': False,
                'llm': False,
                'quality_check': False,
                'overall': False
            } 
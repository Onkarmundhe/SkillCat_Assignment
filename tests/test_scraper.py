"""
Unit tests for the web scraper module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.scraper import WebScraper


class TestWebScraper:
    """Test cases for WebScraper class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scraper = WebScraper(timeout=5, max_retries=1)
    
    def test_init(self):
        """Test WebScraper initialization."""
        assert self.scraper.timeout == 5
        assert self.scraper.max_retries == 1
        assert self.scraper.session is not None
    
    @patch('src.scraper.Article')
    def test_extract_text_newspaper_success(self, mock_article_class):
        """Test successful text extraction using newspaper3k."""
        # Mock Article instance
        mock_article = Mock()
        mock_article.text = "This is extracted article text content."
        mock_article_class.return_value = mock_article
        
        url = "https://example.com/article"
        result = self.scraper.extract_text_newspaper(url)
        
        assert result == "This is extracted article text content."
        mock_article.download.assert_called_once()
        mock_article.parse.assert_called_once()
    
    @patch('src.scraper.Article')
    def test_extract_text_newspaper_failure(self, mock_article_class):
        """Test newspaper3k extraction failure."""
        mock_article_class.side_effect = Exception("Download failed")
        
        url = "https://example.com/article"
        result = self.scraper.extract_text_newspaper(url)
        
        assert result is None
    
    @patch('src.scraper.requests.Session.get')
    @patch('src.scraper.BeautifulSoup')
    def test_extract_text_beautifulsoup_success(self, mock_soup_class, mock_get):
        """Test successful text extraction using BeautifulSoup."""
        # Mock response
        mock_response = Mock()
        mock_response.content = b"<html><body><main>Main content here</main></body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Mock main content element
        mock_main = Mock()
        mock_main.get_text.return_value = "This is the main content of the webpage that contains enough text to pass the minimum length validation requirement of 100 characters for successful extraction."
        
        # Create mock elements for script removal with decompose method
        mock_script = Mock()
        mock_script.decompose = Mock()
        mock_style = Mock()
        mock_style.decompose = Mock()
        
        # Use MagicMock for proper callable behavior
        mock_soup_instance = MagicMock()
        mock_soup_instance.find.return_value = mock_main
        
        # Configure the mock to return an iterable when called as soup(["script", "style", ...])
        mock_soup_instance.return_value = [mock_script, mock_style]
        
        mock_soup_class.return_value = mock_soup_instance
        
        url = "https://example.com/page"
        result = self.scraper.extract_text_beautifulsoup(url)
        
        assert result == "This is the main content of the webpage that contains enough text to pass the minimum length validation requirement of 100 characters for successful extraction."
        mock_get.assert_called_once_with(url, timeout=5)
        
        # Verify that decompose was called on the mock elements
        mock_script.decompose.assert_called_once()
        mock_style.decompose.assert_called_once()
    
    @patch('src.scraper.requests.Session.get')
    def test_extract_text_beautifulsoup_failure(self, mock_get):
        """Test BeautifulSoup extraction failure."""
        mock_get.side_effect = Exception("Network error")
        
        url = "https://example.com/page"
        result = self.scraper.extract_text_beautifulsoup(url)
        
        assert result is None
    
    def test_scrape_search_results(self):
        """Test scraping multiple search results."""
        # Mock the scrape_url method
        with patch.object(self.scraper, 'scrape_url') as mock_scrape:
            mock_scrape.side_effect = [
                "Content from first URL",
                None,  # Failed scrape
                "Content from third URL"
            ]
            
            search_results = [
                {'title': 'First Result', 'url': 'https://example1.com', 'snippet': 'First snippet'},
                {'title': 'Second Result', 'url': 'https://example2.com', 'snippet': 'Second snippet'},
                {'title': 'Third Result', 'url': 'https://example3.com', 'snippet': 'Third snippet'}
            ]
            
            results = self.scraper.scrape_search_results(search_results)
            
            assert len(results) == 3
            assert results[0]['content'] == "Content from first URL"
            assert results[0]['scrape_success'] is True
            assert results[1]['content'] == 'Second snippet'  # Fallback to snippet
            assert results[1]['scrape_success'] is False
            assert results[2]['content'] == "Content from third URL"
            assert results[2]['scrape_success'] is True
    
    def test_scrape_search_results_empty(self):
        """Test scraping with empty search results."""
        results = self.scraper.scrape_search_results([])
        assert results == []
    
    def test_scrape_search_results_no_url(self):
        """Test scraping with results missing URLs."""
        search_results = [
            {'title': 'No URL Result', 'snippet': 'Some snippet'}
        ]
        
        results = self.scraper.scrape_search_results(search_results)
        assert len(results) == 0  # Should skip results without URLs


class TestTextExtraction:
    """Test cases for text extraction utilities."""
    
    def test_content_length_validation(self):
        """Test that short content is rejected."""
        scraper = WebScraper()
        
        # Mock BeautifulSoup to return short content
        with patch('src.scraper.requests.Session.get') as mock_get, \
             patch('src.scraper.BeautifulSoup') as mock_soup_class:
            
            mock_response = Mock()
            mock_response.content = b"<html><body><main>Short</main></body></html>"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            mock_main = Mock()
            mock_main.get_text.return_value = "Short"  # Less than 100 chars
            
            # Create mock elements for script removal with decompose method
            mock_script = Mock()
            mock_script.decompose = Mock()
            
            # Use MagicMock for proper callable behavior
            mock_soup_instance = MagicMock()
            mock_soup_instance.find.return_value = mock_main
            
            # Configure the mock to return an iterable when called as soup(["script", "style", ...])
            mock_soup_instance.return_value = [mock_script]
            
            mock_soup_class.return_value = mock_soup_instance
            
            result = scraper.extract_text_beautifulsoup("https://example.com")
            assert result is None  # Should reject short content
    
    def test_whitespace_cleanup(self):
        """Test that whitespace is properly cleaned up."""
        scraper = WebScraper()
        
        with patch('src.scraper.requests.Session.get') as mock_get, \
             patch('src.scraper.BeautifulSoup') as mock_soup_class:
            
            mock_response = Mock()
            mock_response.content = b"<html><body><main>Content   with    extra     spaces</main></body></html>"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            mock_main = Mock()
            mock_main.get_text.return_value = "Content   with    extra     spaces   and   more   text   to   make   it   longer   than   100   characters   for   validation   purposes   and   testing   whitespace   cleanup   functionality."
            
            # Create mock elements for script removal with decompose method
            mock_script = Mock()
            mock_script.decompose = Mock()
            
            # Use MagicMock for proper callable behavior
            mock_soup_instance = MagicMock()
            mock_soup_instance.find.return_value = mock_main
            
            # Configure the mock to return an iterable when called as soup(["script", "style", ...])
            mock_soup_instance.return_value = [mock_script]
            
            mock_soup_class.return_value = mock_soup_instance
            
            result = scraper.extract_text_beautifulsoup("https://example.com")
            assert result == "Content with extra spaces and more text to make it longer than 100 characters for validation purposes and testing whitespace cleanup functionality."


if __name__ == "__main__":
    pytest.main([__file__]) 
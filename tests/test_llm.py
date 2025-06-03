"""
Unit tests for the LLM module, focusing on citation parsing logic.
"""
import pytest
from unittest.mock import Mock, patch
from src.llm import GeminiLLM


class TestGeminiLLM:
    """Test cases for GeminiLLM class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock the API key to avoid requiring real credentials in tests
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            with patch('src.llm.genai.configure'), \
                 patch('src.llm.genai.GenerativeModel'):
                self.llm = GeminiLLM()
    
    def test_parse_citations_single(self):
        """Test parsing a single citation from answer text."""
        answer = "This is a fact [1] that needs citation."
        citations = self.llm.parse_citations(answer)
        assert citations == [1]
    
    def test_parse_citations_multiple(self):
        """Test parsing multiple citations from answer text."""
        answer = "First fact [1] and second fact [2] with third fact [3]."
        citations = self.llm.parse_citations(answer)
        assert citations == [1, 2, 3]
    
    def test_parse_citations_none(self):
        """Test parsing text with no citations."""
        answer = "This text has no citations at all."
        citations = self.llm.parse_citations(answer)
        assert citations == []
    
    def test_parse_citations_duplicate(self):
        """Test parsing text with duplicate citations."""
        answer = "First mention [1] and second mention [1] of same source."
        citations = self.llm.parse_citations(answer)
        assert citations == [1, 1]  # Should include duplicates
    
    def test_parse_citations_mixed_format(self):
        """Test parsing text with various citation formats."""
        answer = "Valid citation [1] and invalid (2) and another valid [3]."
        citations = self.llm.parse_citations(answer)
        assert citations == [1, 3]  # Should only match [n] format
    
    def test_parse_citations_large_numbers(self):
        """Test parsing citations with large numbers."""
        answer = "Citation [10] and citation [999] are valid."
        citations = self.llm.parse_citations(answer)
        assert citations == [10, 999]
    
    def test_create_prompt_basic(self):
        """Test basic prompt creation."""
        question = "What is AI?"
        sources = [
            {
                'title': 'AI Article',
                'url': 'https://example.com/ai',
                'content': 'Artificial Intelligence is...',
                'snippet': 'AI snippet'
            }
        ]
        
        prompt = self.llm.create_prompt(question, sources)
        
        assert "What is AI?" in prompt
        assert "AI Article" in prompt
        assert "https://example.com/ai" in prompt
        assert "Artificial Intelligence is..." in prompt
        assert "[1]" in prompt
    
    def test_create_prompt_multiple_sources(self):
        """Test prompt creation with multiple sources."""
        question = "Test question"
        sources = [
            {'title': 'Source 1', 'url': 'https://example1.com', 'content': 'Content 1'},
            {'title': 'Source 2', 'url': 'https://example2.com', 'content': 'Content 2'},
            {'title': 'Source 3', 'url': 'https://example3.com', 'content': 'Content 3'}
        ]
        
        prompt = self.llm.create_prompt(question, sources)
        
        assert "[1]" in prompt
        assert "[2]" in prompt
        assert "[3]" in prompt
        assert "Source 1" in prompt
        assert "Source 2" in prompt
        assert "Source 3" in prompt
    
    def test_create_prompt_long_content_truncation(self):
        """Test that long content gets truncated."""
        question = "Test question"
        long_content = "A" * 3000  # Longer than 2000 char limit
        sources = [
            {'title': 'Long Article', 'url': 'https://example.com', 'content': long_content}
        ]
        
        prompt = self.llm.create_prompt(question, sources)
        
        # Should contain truncated content with ellipsis
        assert "A" * 2000 + "..." in prompt
        assert len([line for line in prompt.split('\n') if 'A' * 100 in line][0]) < 2100
    
    def test_create_prompt_missing_fields(self):
        """Test prompt creation with missing source fields."""
        question = "Test question"
        sources = [
            {'title': 'Complete Source', 'url': 'https://example.com', 'content': 'Full content'},
            {'url': 'https://example2.com', 'content': 'Missing title'},  # No title
            {'title': 'Missing URL', 'content': 'No URL'},  # No URL
            {'title': 'Missing Content', 'url': 'https://example3.com'}  # No content
        ]
        
        prompt = self.llm.create_prompt(question, sources)
        
        # Should handle missing fields gracefully
        assert "Complete Source" in prompt
        assert "Source 2" in prompt  # Default title
        assert "Missing URL" in prompt
        assert "Missing Content" in prompt
    
    def test_create_prompt_fallback_to_snippet(self):
        """Test that prompt falls back to snippet when content is missing."""
        question = "Test question"
        sources = [
            {
                'title': 'Article with snippet',
                'url': 'https://example.com',
                'snippet': 'This is the snippet text'
                # No content field
            }
        ]
        
        prompt = self.llm.create_prompt(question, sources)
        
        assert "This is the snippet text" in prompt
    
    def test_get_model_info(self):
        """Test getting model information."""
        info = self.llm.get_model_info()
        
        assert 'model_name' in info
        assert 'provider' in info
        assert 'api_configured' in info
        assert info['provider'] == 'Google Gemini'
        assert isinstance(info['api_configured'], bool)
    
    def test_extract_sentences_with_citations(self):
        """Test extracting sentences that contain citations."""
        answer = "This is fact one [1]. This is fact two [2] and three [3]. No citation here."
        sentences = self.llm.extract_sentences_with_citations(answer)
        
        assert len(sentences) == 2
        assert sentences[0]['sentence'] == "This is fact one"
        assert sentences[0]['citations'] == [1]
        assert sentences[1]['sentence'] == "This is fact two  and three"
        assert sentences[1]['citations'] == [2, 3]
    
    def test_extract_sentences_with_citations_empty(self):
        """Test extracting sentences with no citations."""
        answer = "This has no citations at all. Neither does this sentence."
        sentences = self.llm.extract_sentences_with_citations(answer)
        
        assert len(sentences) == 0
    
    def test_extract_sentences_complex_citations(self):
        """Test extracting sentences with complex citation patterns."""
        answer = "Multiple citations [1][2] in one place. Citation at end [3]! Question with citation [4]?"
        sentences = self.llm.extract_sentences_with_citations(answer)
        
        assert len(sentences) == 3
        assert sentences[0]['citations'] == [1, 2]
        assert sentences[1]['citations'] == [3]
        assert sentences[2]['citations'] == [4]


class TestCitationValidation:
    """Test cases for citation validation logic."""
    
    def test_citation_format_validation(self):
        """Test that only proper citation formats are recognized."""
        llm = GeminiLLM.__new__(GeminiLLM)  # Create without calling __init__
        
        test_cases = [
            ("[1]", [1]),
            ("[1] [2]", [1, 2]),
            ("(1)", []),  # Wrong format
            ("[a]", []),  # Non-numeric
            ("[1.5]", []),  # Decimal
            ("[01]", [1]),  # Leading zero
            ("[[1]]", [1]),  # Double brackets (should still match inner)
            ("[1] text [2]", [1, 2]),  # Multiple with text
        ]
        
        for text, expected in test_cases:
            result = llm.parse_citations(text)
            assert result == expected, f"Failed for input: {text}"
    
    def test_citation_boundary_cases(self):
        """Test citation parsing boundary cases."""
        llm = GeminiLLM.__new__(GeminiLLM)
        
        # Empty string
        assert llm.parse_citations("") == []
        
        # Only brackets
        assert llm.parse_citations("[]") == []
        
        # Malformed brackets
        assert llm.parse_citations("[") == []
        assert llm.parse_citations("]") == []
        assert llm.parse_citations("[1") == []
        assert llm.parse_citations("1]") == []
        
        # Zero citation
        assert llm.parse_citations("[0]") == [0]
        
        # Very large number
        assert llm.parse_citations("[999999]") == [999999]


if __name__ == "__main__":
    pytest.main([__file__]) 
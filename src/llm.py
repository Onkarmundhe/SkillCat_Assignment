"""
LLM functionality using Google Gemini for generating answers with citations.
"""
import logging
import os
import re
from typing import List, Dict, Tuple, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)


class CitationQualityResult:
    """Result of citation quality check."""
    def __init__(self, citation_id: int, sentence: str, source_content: str, 
                 is_supported: bool, confidence: float, explanation: str):
        self.citation_id = citation_id
        self.sentence = sentence
        self.source_content = source_content
        self.is_supported = is_supported
        self.confidence = confidence
        self.explanation = explanation


class GeminiLLM:
    """Handles LLM operations using Google Gemini."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        """
        Initialize the Gemini LLM.
        
        Args:
            api_key: Gemini API key (if None, will use environment variable)
            model_name: Name of the Gemini model to use
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.model_name = model_name
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Configure the API
        genai.configure(api_key=self.api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )
    
    def create_prompt(self, question: str, sources: List[Dict[str, str]]) -> str:
        """
        Create a prompt for the LLM with the question and sources.
        
        Args:
            question: User's question
            sources: List of source documents with content
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a helpful assistant that answers questions based on provided web sources. 

IMPORTANT INSTRUCTIONS:
1. Answer the question using ONLY the information provided in the sources below
2. Include numbered citations [1], [2], etc. in your answer to reference specific sources
3. Each citation should correspond to a specific source number
4. If information comes from multiple sources, cite all relevant ones
5. If you cannot answer the question based on the provided sources, say so clearly
6. Keep your answer concise but comprehensive
7. Use markdown formatting for better readability

QUESTION: {question}

SOURCES:
"""
        
        for i, source in enumerate(sources, 1):
            content = source.get('content', source.get('snippet', ''))
            title = source.get('title', f'Source {i}')
            url = source.get('url', '')
            
            # Truncate content if too long to avoid context length issues
            if len(content) > 2000:
                content = content[:2000] + "..."
            
            prompt += f"\n[{i}] Title: {title}\nURL: {url}\nContent: {content}\n"
        
        prompt += "\nPlease provide your answer with appropriate citations:"
        
        return prompt
    
    def generate_answer(self, question: str, sources: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, str]]]:
        """
        Generate an answer with citations based on the question and sources.
        
        Args:
            question: User's question
            sources: List of source documents
            
        Returns:
            Tuple of (answer_text, sources_list)
        """
        try:
            if not sources:
                return "I couldn't find any sources to answer your question. Please try a different query.", []
            
            prompt = self.create_prompt(question, sources)
            
            logger.info(f"Generating answer for question: {question}")
            logger.debug(f"Prompt length: {len(prompt)} characters")
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            if not response.text:
                return "I couldn't generate an answer. Please try again.", []
            
            answer = response.text.strip()
            
            # Create sources list for citations
            sources_list = []
            for i, source in enumerate(sources, 1):
                sources_list.append({
                    'id': i,
                    'title': source.get('title', f'Source {i}'),
                    'url': source.get('url', ''),
                    'snippet': source.get('snippet', ''),
                    'content': source.get('content', source.get('snippet', ''))
                })
            
            logger.info("Successfully generated answer with citations")
            return answer, sources_list
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {str(e)}")
            return f"Error generating answer: {str(e)}", []
    
    def parse_citations(self, answer: str) -> List[int]:
        """
        Parse citation numbers from the answer text.
        
        Args:
            answer: The generated answer text
            
        Returns:
            List of citation numbers found in the answer
        """
        # Find all citations in format [1], [2], etc.
        citations = re.findall(r'\[(\d+)\]', answer)
        return [int(c) for c in citations]
    
    def extract_sentences_with_citations(self, answer: str) -> List[Dict[str, any]]:
        """
        Extract sentences that contain citations for quality checking.
        
        Args:
            answer: The generated answer text
            
        Returns:
            List of dictionaries with sentence and citation info
        """
        sentences_with_citations = []
        
        # Split into sentences (simple approach)
        sentences = re.split(r'[.!?]+', answer)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Find citations in this sentence
            citations = re.findall(r'\[(\d+)\]', sentence)
            if citations:
                # Clean sentence of citations for analysis
                clean_sentence = re.sub(r'\[\d+\]', '', sentence).strip()
                sentences_with_citations.append({
                    'sentence': clean_sentence,
                    'original_sentence': sentence,
                    'citations': [int(c) for c in citations]
                })
        
        return sentences_with_citations
    
    def check_citation_quality(self, answer: str, sources: List[Dict[str, str]]) -> List[CitationQualityResult]:
        """
        Check the quality of citations by validating if they support the content.
        
        Args:
            answer: The generated answer with citations
            sources: List of source documents
            
        Returns:
            List of CitationQualityResult objects
        """
        try:
            logger.info("Starting citation quality check")
            
            sentences_with_citations = self.extract_sentences_with_citations(answer)
            quality_results = []
            
            for sentence_info in sentences_with_citations:
                sentence = sentence_info['sentence']
                citations = sentence_info['citations']
                
                for citation_id in citations:
                    # Find the corresponding source
                    source = None
                    for src in sources:
                        if src.get('id') == citation_id:
                            source = src
                            break
                    
                    if not source:
                        quality_results.append(CitationQualityResult(
                            citation_id=citation_id,
                            sentence=sentence,
                            source_content="Source not found",
                            is_supported=False,
                            confidence=0.0,
                            explanation="Citation refers to non-existent source"
                        ))
                        continue
                    
                    # Create prompt for quality check
                    quality_prompt = f"""You are a fact-checking expert. Your task is to determine if a citation properly supports a claim.

CLAIM: "{sentence}"

SOURCE CONTENT: "{source.get('content', source.get('snippet', ''))[:1000]}"

INSTRUCTIONS:
1. Determine if the source content supports, contradicts, or is irrelevant to the claim
2. Provide a confidence score from 0.0 to 1.0
3. Give a brief explanation

Respond in this exact format:
SUPPORTED: [YES/NO]
CONFIDENCE: [0.0-1.0]
EXPLANATION: [Brief explanation]"""

                    try:
                        # Generate quality check response
                        response = self.model.generate_content(quality_prompt)
                        
                        if response.text:
                            result_text = response.text.strip()
                            
                            # Parse the response
                            supported_match = re.search(r'SUPPORTED:\s*(YES|NO)', result_text, re.IGNORECASE)
                            confidence_match = re.search(r'CONFIDENCE:\s*([0-9.]+)', result_text)
                            explanation_match = re.search(r'EXPLANATION:\s*(.+)', result_text, re.DOTALL)
                            
                            is_supported = supported_match.group(1).upper() == 'YES' if supported_match else False
                            confidence = float(confidence_match.group(1)) if confidence_match else 0.5
                            explanation = explanation_match.group(1).strip() if explanation_match else "Unable to parse explanation"
                            
                            quality_results.append(CitationQualityResult(
                                citation_id=citation_id,
                                sentence=sentence,
                                source_content=source.get('content', source.get('snippet', ''))[:200] + "...",
                                is_supported=is_supported,
                                confidence=confidence,
                                explanation=explanation
                            ))
                        
                    except Exception as e:
                        logger.error(f"Quality check failed for citation {citation_id}: {str(e)}")
                        quality_results.append(CitationQualityResult(
                            citation_id=citation_id,
                            sentence=sentence,
                            source_content=source.get('content', source.get('snippet', ''))[:200] + "...",
                            is_supported=False,
                            confidence=0.0,
                            explanation=f"Quality check error: {str(e)}"
                        ))
            
            logger.info(f"Citation quality check completed for {len(quality_results)} citations")
            return quality_results
            
        except Exception as e:
            logger.error(f"Citation quality check failed: {str(e)}")
            return []
    
    def get_model_info(self) -> Dict[str, str]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_name': self.model_name,
            'provider': 'Google Gemini',
            'api_configured': bool(self.api_key)
        } 
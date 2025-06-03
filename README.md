# Ask the Web 🌐

A Streamlit-based Q&A application that searches the web, scrapes content, and provides AI-generated answers with citations using Google Gemini and DuckDuckGo Search.

## Features

- **Real-time Web Search**: Uses DuckDuckGo Search API to find relevant web content
- **Intelligent Scraping**: Extracts main text content using newspaper3k and BeautifulSoup
- **AI-Powered Answers**: Generates comprehensive answers with numbered citations using Google Gemini
- **Citation Quality Check**: Second LLM validates citation accuracy with pass/fail badges (Stretch Feature)
- **Modern UI**: Clean, responsive Streamlit interface with real-time metrics
- **Debug Mode**: Expandable debug section showing raw search results and processing status
- **Dockerized**: Ready-to-deploy Docker container

## Quick Setup

1. **Clone and navigate to the repository**
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Set up environment**: Copy `env.example` to `.env` and add your Gemini API key
4. **Run the application**: `streamlit run app.py`
5. **Access the app**: Open http://localhost:8501 in your browser

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   Pipeline       │    │   Components    │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │ Question    │ │───▶│ │ 1. Search    │ │───▶│ │ DuckDuckGo  │ │
│ │ Input       │ │    │ │              │ │    │ │ Search      │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ └─────────────┘ │
│                 │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ ┌─────────────┐ │    │ │ 2. Scrape    │ │───▶│ │ Web Scraper │ │
│ │ Answer +    │ │◀───│ │              │ │    │ │ (newspaper3k│ │
│ │ Citations   │ │    │ └──────────────┘ │    │ │ + BS4)      │ │
│ └─────────────┘ │    │ ┌──────────────┐ │    │ └─────────────┘ │
│                 │    │ │ 3. Generate  │ │    │ ┌─────────────┐ │
│ ┌─────────────┐ │    │ │ Answer       │ │───▶│ │ Google      │ │
│ │ Debug Info  │ │    │ │              │ │    │ │ Gemini LLM  │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## LLM Prompts

### Main Answer Generation Prompt

The system uses a carefully crafted prompt that:

**Rationale**: Ensures accurate citations by explicitly instructing the model to use numbered references and providing clear source mapping. The prompt includes content truncation to manage context length and fallback to snippets when full content isn't available.

**Key Instructions**:
- Answer using ONLY provided sources
- Include numbered citations [1], [2], etc.
- Map each citation to specific source numbers
- Use markdown formatting for readability
- Handle cases where sources don't contain sufficient information

### Citation Quality Check Prompt (Stretch Feature)

A second LLM call validates each citation using a fact-checking prompt:

**Rationale**: Provides transparency about citation accuracy by having the LLM critique its own work. Uses structured output format for reliable parsing and confidence scoring.

**Key Instructions**:
- Evaluate if source content supports the claim
- Provide binary SUPPORTED (YES/NO) decision
- Include confidence score (0.0-1.0)
- Give brief explanation of reasoning

## Environment Variables

Create a `.env` file with:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey).

## Docker Deployment

```bash
# Build the image
docker build -t ask-web .

# Run the container
docker run -p 8501:8501 --env-file .env ask-web
```

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Tests cover:
- Web scraper text extraction logic
- Citation parsing functionality
- Error handling and edge cases

## Known Limitations

1. **Rate Limiting**: DuckDuckGo may rate limit requests with heavy usage
2. **Scraping Reliability**: Some websites may block automated scraping (403 Forbidden errors)
   - The app uses user agent rotation and random delays to minimize this
   - Falls back to search snippets when scraping fails
3. **Context Length**: Very long articles are truncated to fit LLM context limits
4. **Citation Accuracy**: LLM may occasionally misattribute information despite careful prompting
5. **Language Support**: Optimized for English content
6. **Library Warnings**: newspaper3k library may show regex warnings (suppressed in production)

## Dependencies

- **streamlit**: Web application framework
- **duckduckgo-search**: Web search functionality
- **newspaper3k**: Article extraction
- **beautifulsoup4**: HTML parsing fallback
- **google-generativeai**: Gemini LLM integration
- **requests**: HTTP client for web scraping
- **python-dotenv**: Environment variable management

## Performance Metrics

The application tracks:
- Total processing time
- Search time
- Scraping time
- LLM generation time
- Citation quality check time (when enabled)
- Number of successful scrapes
- Search results count
- Quality checks performed
- Citation accuracy statistics

## Contributing

1. Follow the existing code structure
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure Docker build passes

## License

This project is for educational and evaluation purposes as part of the SkillCat work sample assignment. 
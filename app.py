"""
Ask the Web - Streamlit Q&A Application with Citations
"""
import streamlit as st
import logging
import json
import os
import warnings
from dotenv import load_dotenv
from src.pipeline import AskTheWebPipeline

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=SyntaxWarning)
warnings.filterwarnings("ignore", message="invalid escape sequence")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Ask the Web",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .answer-container {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .source-item {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'pipeline' not in st.session_state:
        try:
            # Check if quality check is enabled
            enable_quality_check = st.session_state.get('enable_quality_check', True)
            st.session_state.pipeline = AskTheWebPipeline(enable_quality_check=enable_quality_check)
            st.session_state.pipeline_status = "ready"
        except Exception as e:
            st.session_state.pipeline = None
            st.session_state.pipeline_status = f"error: {str(e)}"
    
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    if 'enable_quality_check' not in st.session_state:
        st.session_state.enable_quality_check = True

def display_header():
    """Display the main header."""
    st.markdown("""
    <div class="main-header">
        <h1>🌐 Ask the Web</h1>
        <p>Get answers to your questions with real-time web search and AI-powered citations</p>
    </div>
    """, unsafe_allow_html=True)

def display_sidebar():
    """Display the sidebar with metrics and health status."""
    st.sidebar.title("📊 System Status")
    
    # Quality Check Toggle
    st.sidebar.subheader("⚙️ Settings")
    new_quality_check = st.sidebar.checkbox(
        "Enable Citation Quality Check", 
        value=st.session_state.enable_quality_check,
        help="Uses a second LLM call to validate citation accuracy"
    )
    
    # Update pipeline if setting changed
    if new_quality_check != st.session_state.enable_quality_check:
        st.session_state.enable_quality_check = new_quality_check
        try:
            st.session_state.pipeline = AskTheWebPipeline(enable_quality_check=new_quality_check)
        except Exception as e:
            st.sidebar.error(f"Failed to update pipeline: {str(e)}")
    
    # Health check
    if st.session_state.pipeline:
        health = st.session_state.pipeline.health_check()
        
        st.sidebar.subheader("Component Health")
        for component, status in health.items():
            if component != 'overall':
                icon = "✅" if status else "❌"
                st.sidebar.write(f"{icon} {component.title()}: {'OK' if status else 'Error'}")
        
        # Overall status
        overall_status = health.get('overall', False)
        status_class = "status-success" if overall_status else "status-error"
        status_text = "Ready" if overall_status else "Configuration Error"
        st.sidebar.markdown(f'<p class="{status_class}">Overall: {status_text}</p>', unsafe_allow_html=True)
        
        # Last query metrics
        if hasattr(st.session_state.pipeline, 'last_query_metrics') and st.session_state.pipeline.last_query_metrics:
            st.sidebar.subheader("📈 Last Query Metrics")
            metrics = st.session_state.pipeline.last_query_metrics
            
            col1, col2 = st.sidebar.columns(2)
            with col1:
                st.metric("Total Time", f"{metrics.get('total_time', 0):.2f}s")
                st.metric("Search Results", metrics.get('search_results_count', 0))
                if metrics.get('quality_check_time', 0) > 0:
                    st.metric("Quality Checks", metrics.get('quality_checks_performed', 0))
            
            with col2:
                st.metric("LLM Time", f"{metrics.get('llm_time', 0):.2f}s")
                st.metric("Scraped Pages", metrics.get('successful_scrapes', 0))
                if metrics.get('quality_check_time', 0) > 0:
                    st.metric("QC Time", f"{metrics.get('quality_check_time', 0):.2f}s")
    
    else:
        st.sidebar.error("Pipeline not initialized")
        st.sidebar.write("Please check your environment configuration.")

def display_main_interface():
    """Display the main query interface."""
    st.subheader("💬 Ask Your Question")
    
    # Query input
    col1, col2 = st.columns([4, 1])
    
    with col1:
        question = st.text_input(
            "Enter your question:",
            placeholder="e.g., What are the latest developments in artificial intelligence?",
            key="question_input"
        )
    
    with col2:
        st.write("")  # Spacing
        ask_button = st.button("🔍 Ask", type="primary", use_container_width=True)
    
    # Process query
    if ask_button and question.strip():
        if not st.session_state.pipeline:
            st.error("Pipeline not initialized. Please check your configuration.")
            return
        
        with st.spinner("🔍 Searching the web and generating answer..."):
            try:
                result = st.session_state.pipeline.process_query(question.strip())
                
                # Store in history
                st.session_state.query_history.append({
                    'question': question.strip(),
                    'result': result
                })
                
                # Display results
                display_results(result)
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                logger.error(f"Query processing error: {str(e)}")
    
    elif ask_button and not question.strip():
        st.warning("Please enter a question before clicking Ask.")

def display_results(result):
    """Display the query results."""
    answer = result.get('answer', '')
    sources = result.get('sources', [])
    debug_info = result.get('debug_info', {})
    quality_check = result.get('quality_check', [])
    
    # Answer section
    if answer:
        st.subheader("📝 Answer")
        st.markdown(f'<div class="answer-container">{answer}</div>', unsafe_allow_html=True)
    
    # Citation Quality Check Results
    if quality_check:
        st.subheader("🔍 Citation Quality Check")
        
        # Summary stats
        total_checks = len(quality_check)
        passed_checks = sum(1 for qc in quality_check if qc.is_supported)
        avg_confidence = sum(qc.confidence for qc in quality_check) / total_checks if total_checks > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Citations", total_checks)
        with col2:
            st.metric("Passed", f"{passed_checks}/{total_checks}")
        with col3:
            st.metric("Avg Confidence", f"{avg_confidence:.2f}")
        
        # Individual citation results
        for qc in quality_check:
            badge_color = "#28a745" if qc.is_supported else "#dc3545"
            badge_text = "✅ PASS" if qc.is_supported else "❌ FAIL"
            confidence_color = "#28a745" if qc.confidence > 0.7 else "#ffc107" if qc.confidence > 0.4 else "#dc3545"
            
            st.markdown(f"""
            <div class="source-item">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <strong>Citation [{qc.citation_id}]</strong>
                    <div>
                        <span style="background-color: {badge_color}; color: white; padding: 0.2rem 0.5rem; border-radius: 0.3rem; font-size: 0.8rem; margin-right: 0.5rem;">{badge_text}</span>
                        <span style="background-color: {confidence_color}; color: white; padding: 0.2rem 0.5rem; border-radius: 0.3rem; font-size: 0.8rem;">{qc.confidence:.2f}</span>
                    </div>
                </div>
                <div style="margin-bottom: 0.5rem;">
                    <strong>Claim:</strong> "{qc.sentence}"
                </div>
                <div style="margin-bottom: 0.5rem;">
                    <strong>Explanation:</strong> {qc.explanation}
                </div>
                <div style="font-size: 0.9rem; color: #6c757d;">
                    <strong>Source excerpt:</strong> {qc.source_content}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Sources section
    if sources:
        st.subheader("📚 Sources")
        for source in sources:
            source_id = source.get('id', '')
            title = source.get('title', 'Untitled')
            url = source.get('url', '')
            snippet = source.get('snippet', '')
            
            # Check if this source has quality check results
            source_quality_checks = [qc for qc in quality_check if qc.citation_id == source_id]
            quality_indicator = ""
            
            if source_quality_checks:
                passed = sum(1 for qc in source_quality_checks if qc.is_supported)
                total = len(source_quality_checks)
                if passed == total:
                    quality_indicator = ' <span style="color: #28a745;">✅</span>'
                elif passed > 0:
                    quality_indicator = f' <span style="color: #ffc107;">⚠️ {passed}/{total}</span>'
                else:
                    quality_indicator = ' <span style="color: #dc3545;">❌</span>'
            
            st.markdown(f"""
            <div class="source-item">
                <strong>[{source_id}] {title}{quality_indicator}</strong><br>
                <a href="{url}" target="_blank">{url}</a><br>
                <small>{snippet}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Debug section (expandable)
    with st.expander("🔧 Debug Information"):
        st.subheader("Search Results")
        search_results = debug_info.get('search_results', [])
        if search_results:
            st.json(search_results)
        else:
            st.write("No search results available")
        
        st.subheader("Processing Status")
        status = debug_info.get('status', 'unknown')
        st.write(f"Status: {status}")
        
        if 'error' in debug_info:
            st.error(f"Error: {debug_info['error']}")
        
        # Quality check debug info
        if quality_check:
            st.subheader("Quality Check Details")
            quality_data = []
            for qc in quality_check:
                quality_data.append({
                    'Citation': qc.citation_id,
                    'Supported': qc.is_supported,
                    'Confidence': qc.confidence,
                    'Sentence': qc.sentence[:100] + "..." if len(qc.sentence) > 100 else qc.sentence
                })
            st.json(quality_data)

def display_query_history():
    """Display query history."""
    if st.session_state.query_history:
        st.subheader("📜 Query History")
        
        for i, entry in enumerate(reversed(st.session_state.query_history[-5:])):  # Show last 5
            with st.expander(f"Query {len(st.session_state.query_history) - i}: {entry['question'][:50]}..."):
                st.write(f"**Question:** {entry['question']}")
                st.write(f"**Answer:** {entry['result']['answer'][:200]}...")
                
                if entry['result']['sources']:
                    st.write("**Sources:**")
                    for source in entry['result']['sources']:
                        st.write(f"- [{source['id']}] {source['title']}")

def main():
    """Main application function."""
    # Initialize
    initialize_session_state()
    
    # Display UI
    display_header()
    display_sidebar()
    
    # Main content
    display_main_interface()
    
    # Divider
    st.markdown("---")
    
    # Query history
    display_query_history()
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #6c757d;">
        <p>Built with Streamlit, DuckDuckGo Search, and Google Gemini</p>
        <p>🌐 Ask the Web - Real-time Q&A with Citations</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 
import streamlit as st
from app import ClimateRiskAnalyzer
import pandas as pd
import time
from datetime import datetime

# Initialize analyzer
analyzer = ClimateRiskAnalyzer()

# Page configuration
st.set_page_config(
    page_title="Climate Risk Insurance AI",
    page_icon="🌍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .risk-high { color: #ff4b4b; font-weight: bold; }
    .risk-medium { color: #ffa500; font-weight: bold; }
    .risk-low { color: #4CAF50; font-weight: bold; }
    .article-card {
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        background: #f9f9f9;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'analyses' not in st.session_state:
    st.session_state.analyses = []

# Header
st.title("🌍 Climate Risk Insurance AI Agent")
st.markdown("Real-time monitoring of climate risks impacting insurance portfolios")

# Sidebar controls
with st.sidebar:
    st.header("Search Parameters")
    query = st.text_input(
        "Search Query", 
        value="latest climate risks for insurance industry"
    )
    max_results = st.slider("Max Results", 1, 20, 5)
    auto_refresh = st.checkbox("Auto-refresh every 5 minutes", False)
    
    if st.button("Clear All Results"):
        st.session_state.analyses = []
        st.rerun()

# Main tabs
tab1, tab2 = st.tabs(["News Analysis", "Risk Dashboard"])

with tab1:
    if st.button("Fetch & Analyze News") or auto_refresh:
        with st.spinner("Fetching latest climate risk news..."):
            try:
                articles = analyzer.fetch_climate_news(query)[:max_results]
                
                if not articles:
                    st.error("""
                    No articles found. Possible reasons:
                    - API service might be unavailable
                    - Your search didn't match any articles
                    - There was an error processing the response
                    """)
                else:
                    for article in articles:
                        with st.container():
                            st.markdown(f"""
                            <div class="article-card">
                                <h3>{article['title']}</h3>
                                <p><i>{article['source']} • {article['published_date']}</i></p>
                                <p>{article['content'][:500]}...</p>
                                <a href="{article['url']}" target="_blank">Read full article</a>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            analysis = analyzer.analyze_article(article)
                            st.markdown("**Insurance Impact Analysis**")
                            st.markdown(analysis['analysis'])
                            st.session_state.analyses.append(analysis)
                            
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

with tab2:
    st.header("Risk Analysis Dashboard")
    
    if not st.session_state.analyses:
        st.info("No analyses available. Fetch some news first!")
    else:
        # Prepare data
        risk_data = []
        for analysis in st.session_state.analyses:
            content = analysis['analysis']
            risk_score = 50  # Default
            
            if "Confidence:" in content:
                try:
                    risk_score = int(content.split("Confidence:")[1].strip().split("%")[0])
                except:
                    pass
            
            risk_data.append({
                'Title': analysis['original_article']['title'],
                'Source': analysis['original_article']['source'],
                'Risk Score': risk_score,
                'Analysis': content
            })
        
        df = pd.DataFrame(risk_data)
        
        # Visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Risk Distribution")
            st.bar_chart(df, x="Title", y="Risk Score")
        
        with col2:
            st.subheader("Highest Risk Items")
            high_risk = df[df['Risk Score'] > 70]
            
            if not high_risk.empty:
                for _, row in high_risk.iterrows():
                    st.markdown(f"""
                    <div class="article-card">
                        <h4 class="risk-high">{row['Title']}</h4>
                        <p>Source: {row['Source']}</p>
                        <p>Risk Score: <span class="risk-high">{row['Risk Score']}%</span></p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Full data
        st.subheader("All Analyses")
        st.dataframe(df, use_container_width=True)

# Auto-refresh logic
if auto_refresh:
    time.sleep(300)
    st.rerun()
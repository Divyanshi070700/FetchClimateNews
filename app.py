import os
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class ClimateRiskAnalyzer:
    def __init__(self):
        self.llm = self._initialize_llm()
        self.search_tool = self._initialize_search_tool()

    def _initialize_llm(self) -> ChatOpenAI:
        """Initialize the OpenAI language model"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            api_key=api_key,
            temperature=0.3
        )

    def _initialize_search_tool(self) -> TavilySearchResults:
        """Initialize the Tavily search tool"""
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables")
        
        return TavilySearchResults(
            api_key=api_key,
            max_results=10,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=True
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def _make_api_request(self, query: str):
        """Protected method with retry logic"""
        return self.search_tool.invoke({"query": query})

    def fetch_climate_news(self, query: str = "climate risk insurance") -> List[Dict[str, str]]:
        """Fetch and process climate risk news articles"""
        try:
            logger.info(f"Fetching news for query: {query}")
            raw_response = self._make_api_request(query)
            
            if not raw_response:
                logger.error("Empty API response received")
                return []
                
            # Handle different response formats
            if isinstance(raw_response, dict):
                articles = raw_response.get('results', raw_response.get('answer', []))
            elif isinstance(raw_response, list):
                articles = raw_response
            else:
                logger.error(f"Unexpected response type: {type(raw_response)}")
                return []
            
            # Process articles
            processed_articles = []
            for article in articles:
                try:
                    processed = {
                        'title': str(article.get('title', 'No Title')).strip(),
                        'source': str(article.get('source', 'Unknown Source')).strip(),
                        'url': str(article.get('url', '#')).strip(),
                        'published_date': str(article.get('published_date', '')).strip(),
                        'content': str(article.get('content', article.get('raw_content', ''))[:2000])
                    }
                    
                    if processed['title'] and processed['content']:
                        processed_articles.append(processed)
                except Exception as e:
                    logger.warning(f"Error processing article: {str(e)}")
                    continue
            
            logger.info(f"Successfully processed {len(processed_articles)} articles")
            return processed_articles
               
        except Exception as e:
            logger.error(f"Error in fetch_climate_news: {str(e)}", exc_info=True)
            return []

    def analyze_article(self, article: Dict[str, str]) -> Dict[str, str]:
        """Analyze an article for insurance risk impact"""
        try:
            prompt = ChatPromptTemplate.from_template("""
            As an insurance risk analyst, provide:
            
            1. Risk Type: [Flood/Wildfire/Drought/etc.]
            2. Severity: [High/Medium/Low]
            3. Affected Regions: [List regions]
            4. Insurance Impact: [Premium changes/New products/Claims]
            5. Confidence: [1-100%]
            
            Article Title: {title}
            Content: {content}
            """)
            
            chain = prompt | self.llm
            response = chain.invoke({
                "title": article.get('title', ''),
                "content": article.get('content', '')
            })
            
            return {
                'analysis': response.content,
                'original_article': article
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_article: {str(e)}")
            return {
                'analysis': "Analysis failed. Please try another article.",
                'original_article': article
            }

# Initialize analyzer instance
analyzer = ClimateRiskAnalyzer()
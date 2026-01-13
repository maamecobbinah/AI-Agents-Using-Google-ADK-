import os
import requests
from bs4 import BeautifulSoup
from google.adk.agents import Agent
from datetime import datetime
import json

# ============================================================================
# SEARCH FUNCTION: this searches for news based on user query
# ============================================================================

def search_news(query: str, max_results: int = 5) -> dict:
    """
    Search Google News RSS for recent news articles matching the given query.
    
    Args:
        query: Search term or topic to find news about
        max_results: Maximum number of articles to return (default: 5)
    
    Returns:
        Dictionary with status and results or error message
    """
    
    # === INPUT VALIDATION ===
    # More robust validation with helpful error messages
    if not query or not isinstance(query, str):
        return {
            "status": "error",
            "error_message": "Query must be a non-empty string.",
            "timestamp": datetime.now().isoformat()
        }
    
    if not isinstance(max_results, int) or max_results < 1 or max_results > 20:
        max_results = 5  # Default to 5 if invalid
    
    # Clean the query - remove extra whitespace and encode properly
    query = query.strip()
    

      # === BUILD RSS URL ===
    # Global News RSS endpoint with proper encoding
    rss_url = (
        "https://globalnews-ca-staging.go-vip.net/feed/"  ### utilizing gloabal news feed instead 
        f"?s={requests.utils.quote(query)}"  # Search parameter is 's' not 'q'
    )

    # === FETCH NEWS WITH RETRY LOGIC ===
    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = requests.get(
                rss_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                timeout=15,  # Increased timeout for reliability
            )
            response.raise_for_status()
            break  # Success - exit retry loop
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                continue  # Retry
            return {
                "status": "error",
                "error_message": "Request timed out. Google News may be slow to respond.",
                "timestamp": datetime.now().isoformat()
            }
        except requests.exceptions.HTTPError as e:
            return {
                "status": "error",
                "error_message": f"HTTP error {response.status_code}: Unable to fetch news.",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"Network error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    # === PARSE RSS FEED ===
    try:
        soup = BeautifulSoup(response.text, "xml")
        items = soup.find_all("item")
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to parse RSS feed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
    
    if not items:
        return {
            "status": "error",
            "error_message": f"No news articles found for query: '{query}'",
            "query": query,
            "timestamp": datetime.now().isoformat()
        }
    
    # === EXTRACT ARTICLE DATA ===
    results = []
    for item in items[:max_results]:
        # Extract publication date if available
        pub_date = None
        if item.pubDate:
            try:
                pub_date = item.pubDate.text
            except:
                pass
        
        # Extract source if available
        source = None
        if item.source:
            try:
                source = item.source.text
            except:
                pass
        
        article = {
            "title": item.title.text if item.title else "No title",
            "url": item.link.text if item.link else "",
            "summary": item.description.text if item.description else "",
            "published": pub_date,
            "source": source
        }
        results.append(article)
    
    return {
        "status": "success",
        "query": query,
        "total_results": len(results),
        "results": results,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# ENHANCED WEB CONTENT FETCHER - MAAME COBBY TXT 
# ============================================================================

def fetch_article_content(url: str) -> dict:
    """
    Fetch the full content of a news article from its URL with enhanced
    scraping capabilities and better error handling.
    
    Args:
        url: The full URL of the article to fetch
    
    Returns:
        Dictionary with status and article content or error message
    """
    
    if not url or not isinstance(url, str):
        return {
            "status": "error",
            "error_message": "URL must be a non-empty string."
        }
    
    # === ENHANCED HEADERS TO MIMIC REAL BROWSER ===
    # These headers help bypass basic anti-scraping protection
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",  # Do Not Track
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0"
    }
    
    try:
        # === FETCH THE WEBPAGE ===
        response = requests.get(
            url,
            headers=headers,
            timeout=15,
            allow_redirects=True  # Follow redirects (important for news sites)
        )
        response.raise_for_status()
        
        # === PARSE HTML CONTENT ===
        soup = BeautifulSoup(response.text, "html.parser")
        
        # === REMOVE NON-CONTENT ELEMENTS ===
        # Remove scripts, styles, navigation, ads, etc.
        for element in soup(["script", "style", "nav", "header", "footer", 
                            "aside", "iframe", "noscript", "form"]):
            element.decompose()
        
        # === INTELLIGENT CONTENT EXTRACTION ===
        # Try multiple strategies to find the main article content
        article_content = None
        
        # Strategy 1: Look for <article> tag (most semantic)
        article = soup.find("article")
        if article:
            article_content = article.get_text()
        
        # Strategy 2: Look for <main> tag
        if not article_content:
            main = soup.find("main")
            if main:
                article_content = main.get_text()
        
        # Strategy 3: Look for common article container class names
        if not article_content:
            common_classes = [
                "article-content", "article-body", "article__content",
                "story-content", "story-body", "story__content",
                "post-content", "post-body", "post__content",
                "entry-content", "entry-body",
                "content-body", "main-content",
                "article-text", "body-content"
            ]
            for class_name in common_classes:
                content_div = soup.find(class_=class_name)
                if content_div:
                    article_content = content_div.get_text()
                    break
        
        # Strategy 4: Look for common article container IDs
        if not article_content:
            common_ids = ["article-body", "article-content", "story-body", "main-content"]
            for id_name in common_ids:
                content_div = soup.find(id=id_name)
                if content_div:
                    article_content = content_div.get_text()
                    break
        
        # Strategy 5: Find all <p> tags (paragraph extraction)
        if not article_content:
            paragraphs = soup.find_all("p")
            if paragraphs:
                # Filter out very short paragraphs (likely not article content)
                meaningful_paragraphs = [p.get_text() for p in paragraphs if len(p.get_text().strip()) > 50]
                if meaningful_paragraphs:
                    article_content = "\n\n".join(meaningful_paragraphs)
        
        # Strategy 6: Fallback to all text (last resort)
        if not article_content:
            article_content = soup.get_text()
        
        # === CLEAN UP EXTRACTED TEXT ===
        # Remove excessive whitespace and empty lines
        lines = (line.strip() for line in article_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # === VALIDATE CONTENT QUALITY ===
        # Check if we extracted meaningful content
        if len(text) < 100:
            return {
                "status": "error",
                "error_message": (
                    f"Unable to extract meaningful content from this article. "
                    f"The website may require JavaScript rendering, have paywall protection, "
                    f"or use anti-scraping measures. "
                    f"Please visit the article directly at: {url}"
                ),
                "url": url,
                "suggestion": "Visit the URL directly in your browser for full content.",
                "timestamp": datetime.now().isoformat()
            }
        
        # === LIMIT CONTENT LENGTH ===
        # Truncate to avoid token limits while keeping useful content
        if len(text) > 4000:
            text = text[:4000] + "\n\n[Content truncated for length. Visit the URL for the complete article.]"
        
        return {
            "status": "success",
            "url": url,
            "content": text,
            "content_length": len(text),
            "timestamp": datetime.now().isoformat()
        }
        
    # === COMPREHENSIVE ERROR HANDLING ===
    
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, 'response') else 'unknown'
        error_messages = {
            403: "Access forbidden (403). The website is blocking automated access.",
            404: "Article not found (404). The URL may be incorrect or the article may have been removed.",
            429: "Too many requests (429). Please wait a moment before trying again.",
            500: "Server error (500). The website may be experiencing issues.",
            503: "Service unavailable (503). The website may be temporarily down."
        }
        
        message = error_messages.get(status_code, f"HTTP error {status_code}")
        
        return {
            "status": "error",
            "error_message": f"{message} Please visit the URL directly: {url}",
            "url": url,
            "http_status": status_code,
            "suggestion": "Try visiting the article directly in your browser.",
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error_message": "Request timed out while trying to fetch the article. The website may be slow or unresponsive.",
            "url": url,
            "suggestion": "Try again in a moment or visit the URL directly.",
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "error_message": "Connection error. Unable to reach the website. Please check your internet connection.",
            "url": url,
            "suggestion": "Verify your internet connection and try again.",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Unexpected error while fetching article: {str(e)}",
            "url": url,
            "suggestion": "The website may have anti-scraping protection. Try visiting the URL directly.",
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# SAVE NEWS SUMMARY 
# ============================================================================

def save_news_summary(filename: str, content: str) -> dict:
    """
    Save a news summary to a text file.
    Useful for keeping records of researched topics.
    
    Args:
        filename: Name of the file to save (without path)
        content: The content to save
    
    Returns:
        Dictionary with status and file path or error message
    """
    
    if not filename or not isinstance(filename, str):
        return {
            "status": "error",
            "error_message": "Filename must be a non-empty string."
        }
    
    if not content or not isinstance(content, str):
        return {
            "status": "error",
            "error_message": "Content must be a non-empty string."
        }
    
    # Sanitize filename - remove potentially dangerous characters
    safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.'))
    if not safe_filename.endswith('.txt'):
        safe_filename += '.txt'
    
    # Save to a 'summaries' subfolder in the agent directory
    summaries_dir = os.path.join(os.path.dirname(__file__), 'summaries')
    os.makedirs(summaries_dir, exist_ok=True)
    
    filepath = os.path.join(summaries_dir, safe_filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "status": "success",
            "filepath": filepath,
            "message": f"Summary saved to {safe_filename}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to save file: {str(e)}"
        }
# ============================================================================
# SENTIMENT ANALYSIS TOOL 
# ============================================================================

def analyze_sentiment(text: str) -> dict:
    """
    Analyze the sentiment of news text to determine if it's positive, 
    negative, or neutral.
    
    Args:
        text: The text to analyze (article content, title, or summary)
    
    Returns:
        Dictionary with sentiment classification and confidence score
    """
    
    if not text or not isinstance(text, str):
        return {
            "status": "error",
            "error_message": "Text must be a non-empty string."
        }
    
    # Convert to lowercase for analysis
    text_lower = text.lower()
    
    # === SENTIMENT WORD DICTIONARIES ===
    # Positive words commonly found in news
    positive_words = [
        'success', 'successful', 'growth', 'gain', 'profit', 'surge', 'rise',
        'improve', 'improvement', 'positive', 'breakthrough', 'advance', 'win',
        'victory', 'achievement', 'innovation', 'excellent', 'outstanding',
        'record', 'milestone', 'boost', 'soar', 'rally', 'recovery', 'progress',
        'expansion', 'optimistic', 'promising', 'strong', 'robust', 'thriving',
        'benefit', 'advantage', 'opportunity', 'celebrate', 'triumph', 'upbeat'
    ]
    
    # Negative words commonly found in news
    negative_words = [
        'crisis', 'crash', 'decline', 'fall', 'loss', 'fail', 'failure',
        'collapse', 'disaster', 'threat', 'risk', 'concern', 'worry', 'fear',
        'problem', 'issue', 'controversy', 'scandal', 'chaos', 'violence',
        'conflict', 'war', 'attack', 'protest', 'criticism', 'condemn',
        'reject', 'deny', 'worse', 'worst', 'recession', 'layoff', 'cut',
        'deficit', 'debt', 'struggle', 'difficult', 'challenge', 'negative',
        'drop', 'plunge', 'slump', 'downturn', 'turmoil', 'volatile'
    ]
    
    # === COUNT SENTIMENT WORDS ===
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    total_sentiment_words = positive_count + negative_count
    
    # === DETERMINE SENTIMENT ===
    if total_sentiment_words == 0:
        # No clear sentiment indicators
        sentiment = "neutral"
        confidence = 0.50
    elif positive_count > negative_count:
        sentiment = "positive"
        # Confidence based on the ratio
        confidence = min(0.95, 0.60 + (positive_count - negative_count) / 10)
    elif negative_count > positive_count:
        sentiment = "negative"
        confidence = min(0.95, 0.60 + (negative_count - positive_count) / 10)
    else:
        # Equal positive and negative
        sentiment = "neutral"
        confidence = 0.55
    
    # Round confidence to 2 decimal places
    confidence = round(confidence, 2)
    
    return {
        "status": "success",
        "sentiment": sentiment,
        "confidence": confidence,
        "positive_indicators": positive_count,
        "negative_indicators": negative_count,
        "analysis": f"Found {positive_count} positive and {negative_count} negative indicators",
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# MCP-ENHANCED AGENT CONFIGURATION WITH IMPROVED INSTRUCTIONS
# ============================================================================

root_agent = Agent(
    name="enhanced_news_agent",
    model=os.getenv("ROOT_AGENT_MODEL", "gemini-2.0-flash"),
    description=(
        "An intelligent news research agent that can search for news, "
        "fetch full article content, and save summaries. Uses MCP tools "
        "to provide comprehensive news analysis."
    ),
    
    # === ENHANCED INSTRUCTIONS FOR MCP INTEGRATION ===
instruction=(
    "You are an advanced news research assistant with multiple capabilities:\n\n"
    
    "TOOL USAGE:\n"
    "1. **search_news**: Use this to find recent news articles on any topic.\n"
    "   - Always start with this tool when users ask about news\n"
    "   - Extract key topics from user queries (e.g., 'Toronto housing' from 'Tell me about Toronto real estate')\n"
    "   - If no results, try rephrasing the query\n\n"
    
    "2. **fetch_article_content**: Use this to read full articles when:\n"
    "   - User wants detailed information beyond summaries\n"
    "   - User asks 'what is this about?' or 'tell me more about the first/second article'\n"
    "   - User asks 'can you read the full article?'\n"
    "   - IMPORTANT: If fetching fails (common with paywalled or protected sites),\n"
    "     provide a detailed summary based on the article title and RSS description\n"
    "     from search_news results, then include the URL so user can read it directly\n\n"
    
    "3. **analyze_sentiment**: Use this to analyze the tone of news when:\n"
    "   - User asks about sentiment, tone, or 'is this good/bad news?'\n"
    "   - User asks 'what's the sentiment?' or 'how positive/negative is this?'\n"
    "   - Can analyze titles, summaries, or full article content\n\n"
    
    "4. **save_news_summary**: Use this when:\n"
    "   - User asks to save, export, or keep a record\n"
    "   - After completing comprehensive research they might want to reference later\n"
    "   - User says 'save this' or 'keep a copy'\n\n"
    
    "HANDLING FETCH FAILURES (VERY IMPORTANT):\n"
    "When fetch_article_content returns an error:\n"
    "- DO NOT just apologize and say you couldn't access it\n"
    "- Instead, provide maximum value from available data:\n"
    "  * Analyze the article TITLE (often very informative about content)\n"
    "  * Use the RSS SUMMARY from search_news results (contains key info)\n"
    "  * Consider the SOURCE (Politico, CNN, CBC, CTV, Global News, BBC = different perspectives)\n"
    "  * Provide context from related articles in the search results\n"
    "- ALWAYS include the article URL prominently so user can read it themselves\n"
    "- Example response: 'Based on the title and summary from Google News, this article\n"
    "  discusses [your analysis]. The article appears to focus on [key points].\n"
    "  You can read the full article here: [URL]'\n\n"
    
    "WORKFLOW:\n"
    "- For simple queries: search_news → summarize results with context\n"
    "- For detailed requests: search_news → try fetch_article_content → if fails, use RSS data\n"
    "- For sentiment queries: search_news → analyze_sentiment on relevant text\n"
    "- For research projects: search_news → fetch_article_content → save_news_summary\n\n"
    
    "OUTPUT FORMAT:\n"
    "- Present news clearly with titles, sources, and key points\n"
    "- Include article URLs prominently (especially when fetch fails)\n"
    "- Provide publication dates when available\n"
    "- When presenting sentiment: show type and confidence (e.g., 'Positive (85% confidence)')\n"
    "- Be informative even when technical limitations exist\n"
    "- Use RSS summaries intelligently - they often contain substantial information\n\n"
    
    "BEST PRACTICES:\n"
    "- Always cite sources with URLs\n"
    "- Distinguish between information from full articles vs. summaries\n"
    "- Be transparent about information sources\n"
    "- When fetch fails, gracefully maximize value from title + RSS summary\n"
    "- Don't apologize excessively - focus on providing helpful information\n"
    "- If news is breaking or rapidly evolving, mention that the situation may have developed further"
),
    
    # === REGISTER ALL TOOLS ===
    # This is the MCP integration - the agent can now use multiple tools intelligently
tools=[
       search_news,
       fetch_article_content,
       analyze_sentiment, 
       save_news_summary
   ],
)

# ============================================================================
# AGENT ARCHITECTURE SUMMARY
# ============================================================================
#
# AGENT TYPE: Single Agent with Sequential Tool Execution
#
# DESCRIPTION:
# This is a single AI agent (Gemini) that intelligently orchestrates multiple
# tools using the Model Context Protocol (MCP) pattern. The agent decides 
# which tool(s) to use and in what order based on user queries.
#
# ARCHITECTURE:
# - ONE agent (root_agent) makes all decisions
# - FOUR tools available: search_news, fetch_article_content, 
#   analyze_sentiment, save_news_summary
# - Tools execute SEQUENTIALLY (one after another, not in parallel)
# - Agent adapts workflow based on tool responses (success/error)
#
# HOW IT WORKS:
# 1. User asks a question
# 2. Agent analyzes query and decides which tool(s) to use
# 3. Agent calls tools in logical sequence (e.g., search → fetch → analyze)
# 4. Each tool returns structured data with "status" field
# 5. Agent uses tool outputs to decide next steps
# 6. Agent synthesizes all tool results into a final response
#
# EXAMPLE WORKFLOW:
# User: "Find Tesla news and analyze sentiment of the first article"
#   Step 1: search_news("Tesla") → returns list of articles
#   Step 2: fetch_article_content(url) → returns article text
#   Step 3: analyze_sentiment(text) → returns sentiment analysis
#   Step 4: Agent combines all data → presents comprehensive response
#
# KEY FEATURES:
# - Adaptive: Agent changes strategy if tools fail (e.g., uses RSS summary 
#   if article fetch fails)
# - Sequential: Tools called one at a time in logical order
# - Intelligent: Agent decides tool usage based on context, not hardcoded rules
# - Extensible: New tools can be added easily without changing agent logic
#
# MCP INTEGRATION:
# - Tools return standardized dictionaries with "status" field
# - Agent instructions teach it when/how to use each tool
# - Structured data enables intelligent multi-step workflows
# - Error handling allows graceful degradation when tools fail
#
# FUTHER ENHANCEMENT:
# - Tools to get feedback response from the users engaing with the agent 
# - Thumbs up and thumbs down to see responses of the agent meets the user needs 
# ============================================================================
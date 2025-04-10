"""
Web scraping functionality using DuckDuckGo and Crawl4AI.
"""
import logging
import subprocess
from typing import List, Dict, Any
from duckduckgo_search import DDGS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def search_duckduckgo(keywords_groups: List[List[str]], total_limit: int = 6) -> List[Dict[str, Any]]:
    """
    Search DuckDuckGo for relevant web pages using keyword groups.
    
    Args:
        keywords_groups: List of keyword groups from process_search_query
        total_limit: Maximum total results across all keyword groups
        
    Returns:
        List of dictionaries containing search results
    """
    results = []
    try:
        with DDGS() as ddgs:
            # Calculate results per group to stay within total limit
            num_groups = len(keywords_groups)
            results_per_group = total_limit // num_groups if num_groups > 0 else total_limit
            
            # Process each keyword group
            for keyword_group in keywords_groups:
                if len(results) >= total_limit:
                    break
                    
                # Join keywords with OR for broader search
                search_query = " OR ".join(keyword_group)
                logger.info(f"Searching DuckDuckGo with keywords: {search_query}")
                
                # Use text search with specific parameters
                ddg_results = list(ddgs.text(
                    keywords=search_query,
                    region="us-en",
                    safesearch="moderate",
                    backend="auto",
                    max_results=results_per_group
                ))
                
                # Only take enough results to stay under total_limit
                remaining = total_limit - len(results)
                ddg_results = ddg_results[:remaining]
                
                for result in ddg_results:
                    # Extract fields from the text search result
                    title = result.get("title")
                    body = result.get("body")
                    href = result.get("href")
                    
                    if not href:
                        logger.warning(f"No href found in result: {result}")
                        continue
                        
                    # Add keywords used for this result
                    results.append({
                        "title": title or "",
                        "url": href,
                        "snippet": body or "",
                        "date": result.get("date", ""),
                        "keywords_used": keyword_group
                    })
                
        logger.info(f"Found {len(results)} total results from DuckDuckGo across all keyword groups (limited to {total_limit})")
        return results
    except Exception as e:
        logger.error(f"Error searching DuckDuckGo: {str(e)}", exc_info=True)
        return []

def crawl_webpage(url: str) -> Dict[str, Any]:
    """
    Crawl a webpage using Crawl4AI CLI with basic markdown output.
    
    Args:
        url: URL to crawl
        
    Returns:
        Dictionary containing crawled content
    """
    try:
        # Skip if URL is empty
        if not url:
            logger.error("Empty URL provided to crawl_webpage")
            return {
                "url": url,
                "content": "",
                "success": False,
                "error": "Empty URL provided"
            }

        # Basic command for crawling with markdown output only
        cmd = ["crwl", url, "-o", "markdown"]
            
        # Run crawl4ai command and capture output
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the markdown output
        content = result.stdout.strip()
        
        if not content:
            logger.warning(f"No content retrieved from {url}")
            return {
                "url": url,
                "content": "",
                "success": False,
                "error": "No content retrieved"
            }
        
        # Log the successful crawl
        logger.info(f"Crawled {url} successfully")
        logger.info(f"Content: {content[:1000]}...")  # Log first 1000 chars of content
        
        return {
            "url": url,
            "content": content,
            "success": True
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"Error crawling {url}: {str(e)}")
        return {
            "url": url,
            "content": "",
            "success": False,
            "error": str(e)
        }

def search_and_crawl(keywords_groups: List[List[str]], total_limit: int = 6) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Search DuckDuckGo using keyword groups and crawl found pages.
    
    Args:
        keywords_groups: List of keyword groups from process_search_query
        total_limit: Maximum total results across all keyword groups
        
    Returns:
        Tuple containing:
        - List of dictionaries containing original DDG search results
        - List of dictionaries containing search results with crawled content
    """
    results = []
    
    # First get search results using keyword groups
    search_results = search_duckduckgo(keywords_groups, total_limit)
    
    # Save original DDG results before crawling
    ddg_sources = [
        {
            "title": result["title"],
            "url": result["url"],
            "snippet": result["snippet"],
            "date": result["date"],
            "keywords_used": result["keywords_used"]
        }
        for result in search_results
    ]
    
    # Then crawl each result
    for result in search_results:
        try:
            # Basic crawl without any query parameter
            crawl_result = crawl_webpage(result["url"])
            
            # Combine search and crawl results
            if crawl_result["success"]:
                result["content"] = crawl_result["content"]
                results.append(result)
            
        except Exception as e:
            logger.error(f"Error processing {result['url']}: {str(e)}")
            continue
    
    return results, ddg_sources
import os
import requests
from typing import Dict, Any, List, Optional
from langsmith import traceable
# from tavily import TavilyClient
from duckduckgo_search import DDGS
from langchain_core.runnables import RunnableConfig

from configuration import Configuration
# from langchain_ollama import ChatOllama
# from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic
# from langchain_google_genai import ChatGoogleGenerativeAI

def deduplicate_and_format_sources(search_response, max_tokens_per_source, include_raw_content=False):
    """
    Takes either a single search response or list of responses from search APIs and formats them.
    Limits the raw_content to approximately max_tokens_per_source.
    include_raw_content specifies whether to include the raw_content from Tavily in the formatted string.
    
    Args:
        search_response: Either:
            - A dict with a 'results' key containing a list of search results
            - A list of dicts, each containing search results
            
    Returns:
        str: Formatted string with deduplicated sources
    """
    # Convert input to list of results
    if isinstance(search_response, dict):
        sources_list = search_response['results']
    elif isinstance(search_response, list):
        sources_list = []
        for response in search_response:
            if isinstance(response, dict) and 'results' in response:
                sources_list.extend(response['results'])
            else:
                sources_list.extend(response)
    else:
        raise ValueError("Input must be either a dict with 'results' or a list of search results")
    
    # Deduplicate by URL
    unique_sources = {}
    for source in sources_list:
        if source['url'] not in unique_sources:
            unique_sources[source['url']] = source
    
    # Format output
    formatted_text = "Sources:\n\n"
    for i, source in enumerate(unique_sources.values(), 1):
        formatted_text += f"Source {source['title']}:\n===\n"
        formatted_text += f"URL: {source['url']}\n===\n"
        formatted_text += f"Most relevant content from source: {source['content']}\n===\n"
        if include_raw_content:
            # Using rough estimate of 4 characters per token
            char_limit = max_tokens_per_source * 4
            # Handle None raw_content
            raw_content = source.get('raw_content', '')
            if raw_content is None:
                raw_content = ''
                print(f"Warning: No raw_content found for source {source['url']}")
            if len(raw_content) > char_limit:
                raw_content = raw_content[:char_limit] + "... [truncated]"
            formatted_text += f"Full source content limited to {max_tokens_per_source} tokens: {raw_content}\n\n"
                
    return formatted_text.strip()

def format_sources(search_results):
    """Format search results into a bullet-point list of sources.
    
    Args:
        search_results (dict): Tavily search response containing results
        
    Returns:
        str: Formatted string with sources and their URLs
    """
    return '\n'.join(
        f"* {source['title']} : {source['url']}"
        for source in search_results['results']
    )

@traceable
def duckduckgo_search(query: str, max_results: int = 3, fetch_full_page: bool = False) -> Dict[str, List[Dict[str, str]]]:
    """Search the web using DuckDuckGo.
    
    Args:
        query (str): The search query to execute
        max_results (int): Maximum number of results to return
        
    Returns:
        dict: Search response containing:
            - results (list): List of search result dictionaries, each containing:
                - title (str): Title of the search result
                - url (str): URL of the search result
                - content (str): Snippet/summary of the content
                - raw_content (str): Same as content since DDG doesn't provide full page content
    """
    try:
        with DDGS() as ddgs:
            results = []
            search_results = list(ddgs.text(query, max_results=max_results))
            
            for r in search_results:
                url = r.get('href')
                title = r.get('title')
                content = r.get('body')
                
                if not all([url, title, content]):
                    print(f"Warning: Incomplete result from DuckDuckGo: {r}")
                    continue

                raw_content = content
                if fetch_full_page:
                    try:
                        # Try to fetch the full page content using curl
                        import urllib.request
                        from bs4 import BeautifulSoup

                        response = urllib.request.urlopen(url)
                        html = response.read()
                        soup = BeautifulSoup(html, 'html.parser')
                        raw_content = soup.get_text()
                        
                    except Exception as e:
                        print(f"Warning: Failed to fetch full page content for {url}: {str(e)}")
                
                # Add result to list
                result = {
                    "title": title,
                    "url": url,
                    "content": content,
                    "raw_content": raw_content
                }
                results.append(result)
            
            return {"results": results}
    except Exception as e:
        print(f"Error in DuckDuckGo search: {str(e)}")
        print(f"Full error details: {type(e).__name__}")
        return {"results": []}

# @traceable
# def tavily_search(query, include_raw_content=True, max_results=3):
#     """ Search the web using the Tavily API.
    
#     Args:
#         query (str): The search query to execute
#         include_raw_content (bool): Whether to include the raw_content from Tavily in the formatted string
#         max_results (int): Maximum number of results to return
        
#     Returns:
#         dict: Search response containing:
#             - results (list): List of search result dictionaries, each containing:
#                 - title (str): Title of the search result
#                 - url (str): URL of the search result
#                 - content (str): Snippet/summary of the content
#                 - raw_content (str): Full content of the page if available"""
     
#     api_key = os.getenv("TAVILY_API_KEY")
#     if not api_key:
#         raise ValueError("TAVILY_API_KEY environment variable is not set")
#     tavily_client = TavilyClient(api_key=api_key)
#     return tavily_client.search(query, 
#                          max_results=max_results, 
#                          include_raw_content=include_raw_content)

# @traceable
# def perplexity_search(query: str, perplexity_search_loop_count: int) -> Dict[str, Any]:
#     """Search the web using the Perplexity API.
    
#     Args:
#         query (str): The search query to execute
#         perplexity_search_loop_count (int): The loop step for perplexity search (starts at 0)
  
#     Returns:
#         dict: Search response containing:
#             - results (list): List of search result dictionaries, each containing:
#                 - title (str): Title of the search result
#                 - url (str): URL of the search result
#                 - content (str): Snippet/summary of the content
#                 - raw_content (str): Full content of the page if available
#     """

#     headers = {
#         "accept": "application/json",
#         "content-type": "application/json",
#         "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}"
#     }
    
#     payload = {
#         "model": "sonar-pro",
#         "messages": [
#             {
#                 "role": "system",
#                 "content": "Search the web and provide factual information with sources."
#             },
#             {
#                 "role": "user",
#                 "content": query
#             }
#         ]
#     }
    
#     response = requests.post(
#         "https://api.perplexity.ai/chat/completions",
#         headers=headers,
#         json=payload
#     )
#     response.raise_for_status()  # Raise exception for bad status codes
    
#     # Parse the response
#     data = response.json()
#     content = data["choices"][0]["message"]["content"]

#     # Perplexity returns a list of citations for a single search result
#     citations = data.get("citations", ["https://perplexity.ai"])
    
#     # Return first citation with full content, others just as references
#     results = [{
#         "title": f"Perplexity Search {perplexity_search_loop_count + 1}, Source 1",
#         "url": citations[0],
#         "content": content,
#         "raw_content": content
#     }]
    
#     # Add additional citations without duplicating content
#     for i, citation in enumerate(citations[1:], start=2):
#         results.append({
#             "title": f"Perplexity Search {perplexity_search_loop_count + 1}, Source {i}",
#             "url": citation,
#             "content": "See above for full content",
#             "raw_content": None
#         })
    
#     return {"results": results}

# def get_llm(llm_name: str,  **kwargs):
#     """Get a langchain chat model based on the specified name with customizable parameters.
    
#     Args:
#         llm_name (str): Name of the LLM provider, one of: "openai", "ollama", "claude", "gemini"
#         **kwargs: Additional keyword arguments to pass to the model constructor
#             Common parameters:
#             - temperature: Controls randomness (default: 0.7)
#             - model: Model name (defaults vary by provider)
            
#             Ollama-specific:
#             - base_url: URL for Ollama API (default: http://localhost:11434)
#             - format: Response format (e.g., "json")
            
#             Provider-specific parameters will be passed through to the constructor
        
#     Returns:
#         A configured Langchain chat model instance
        
#     Raises:
#         ValueError: If an invalid llm_name is provided or if required API keys are missing
#     """
#     llm_name = llm_name.lower()
#     # configurable = Configuration.from_runnable_config(config)
    
#     # Check for required API keys
#     if llm_name == "openai" and not os.getenv("OPENAI_API_KEY"):
#         raise ValueError("OPENAI_API_KEY environment variable is not set")
#     elif llm_name == "claude" and not os.getenv("ANTHROPIC_API_KEY"):
#         raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
#     elif llm_name == "gemini" and not os.getenv("GOOGLE_API_KEY"):
#         raise ValueError("GOOGLE_API_KEY environment variable is not set")
    
#     # Default parameters that can be overridden by kwargs
#     if llm_name == "openai":
#         defaults = {
#             "temperature": 0.7,
#             "model": "gpt-3.5-turbo"
#         }
#         # Update defaults with any provided kwargs
#         defaults.update(kwargs)
#         return ChatOpenAI(**defaults)
    
#     elif llm_name == "ollama":
#         defaults = {
#             "model": "llama3.2",
#             "temperature": 0.7,
#             "base_url": "http://localhost:11434"
#         }
#         defaults.update(kwargs)
#         return ChatOllama(**defaults)
    
#     elif llm_name == "claude":
#         defaults = {
#             "model": "claude-3-sonnet-20240229",
#             "temperature": 0.7
#         }
#         defaults.update(kwargs)
#         return ChatAnthropic(**defaults)
    
#     elif llm_name == "gemini":
#         defaults = {
#             "model": "gemini-pro",
#             "temperature": 0.7
#         }
#         defaults.update(kwargs)
#         return ChatGoogleGenerativeAI(**defaults)
    
#     elif llm_name == "deepseek":
#         defaults = {
#             "model": "deepseek-chat",
#             "temperature": 0.7
#         }
#         defaults.update(kwargs)
#         return ChatOpenAI(**defaults)
    
#     else:
#         raise ValueError(f"Invalid LLM name: {llm_name}. Choose from 'openai', 'ollama', 'claude', or 'gemini'.")


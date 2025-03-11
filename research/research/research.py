# This script does the paper research and the web search
from research.scraper.scrape import scrape_arxiv
from research.websearch2.search import websearch_2
from crawl4ai import *
import asyncio
import os


async def crawl_url(url):
    print("Starting web crawl...")
    try:
        # Add a timeout to the crawler
        async with AsyncWebCrawler() as crawler:
            # Set a timeout for the crawl operation
            result = await asyncio.wait_for(
                crawler.arun(
                    url=url,
                ),
                timeout=60  # 60 second timeout
            )
            print("Page crawled successfully!")
            
            # Check if we got valid content
            if not result or not hasattr(result, 'markdown') or not result.markdown:
                print("Error: No valid content was retrieved from the webpage")
                return None
                
            return result.markdown
            
    except asyncio.TimeoutError:
        print("Error: Web crawling operation timed out after 60 seconds")
        return None
    except Exception as e:
        print(f"Error during execution: {type(e).__name__}: {e}")
        return None



async def research_async(query):
    """
    This function does the paper research and the web search and returns all the text for our RAG

    Args:
        query (str): The search query to process
    
    Returns:
        dict (str): Dictionary of strings containing all the text for our RAG
    """
    # Create dictionary for the text and the urls they come from
    rag_docs = {}
    
    results = scrape_arxiv(query, max_papers=3)

    # Results returns as a list of dictionaries
    # Keys: "abstract", "authors", "date", "doi", "journal", "text", "title"

    for result in results:
        # example of doi: 10.48550/arXiv.1910.13518
        url = f"https://doi.org/{result['doi']}"
        rag_docs[url] = result['text']

    # Web search
    web_results = websearch_2(query)


    # Easy method
    for result in web_results:
        rag_docs[result['url']] = result['content']
    #########################################################

    # Web results returns as a list of dictionaries
    # Keys: "content", "raw_content", "title", "url"
    # need to extract the urls and use crawler to get the text
    # for result in web_results:
    #     url = result['url']

    #     text = await crawl_url(url)
    #     if text:
    #         rag_docs[url] = text
    
    return rag_docs


def research(query):
    """
    Synchronous wrapper for the async research function
    """
    return asyncio.run(research_async(query))






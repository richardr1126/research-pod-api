# This script does the paper resseach and the web search
from research.scraper.scrape import scrape_arxiv

def research(query):
    """
    This function does the paper research and the web search and returns all the text for our RAG

    Args:
        query (str): The search query to process
    
    Returns:
        list (str): List of strings containing all the text for our RAG
    """
    rag_docs = []
    
    
    results = scrape_arxiv(query, max_papers=3)

    # Results returns as a list of dictionaries
    # Keys: "abstract", "authors", "date", "doi", "journal", "text", "title"
    for result in results:
        rag_docs.append(result['text'])

    # Web search
    # web_results = websearch(query)
    
    
    return rag_docs



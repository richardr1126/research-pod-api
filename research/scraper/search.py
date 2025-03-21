from .websearch import langgraph
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def websearch(query):
    try:
        input_data = {
            "research_topic": query
        }
        logger.info("Executing graph...")
        result = langgraph.graph.invoke(input_data)
        logger.info("Graph executed successfully.")
        # return result and source

        # Source with url, title
        ddg_sources = []
        for result in result['sources_gathered']['results']:
            ddg_sources.append({"title": result['title'], "url": result['url']})

        return result['sources_gathered']['results'], ddg_sources
    except Exception as e:
        logger.error(f"Error during web search: {e}")
        return None
        
# TESTING #
# def main():
#     if len(sys.argv) < 2:
#         print("Usage: python test_search.py 'your search query'")
#         return
    
#     query = sys.argv[1]
#     print(f"Searching for: {query}")
    
#     results = websearch(query)
    
#     if results:
#         print("\nSearch Results:")
#         print(results)
#         # for i, result in enumerate(results['results'], 1):
#         #     print(f"\n--- Result {i} ---")
#         #     print(f"Title: {result.get('title', 'N/A')}")
#         #     print(f"URL: {result.get('url', 'N/A')}")
#         #     print(f"Content snippet: {result.get('content', 'N/A')[:150]}...")
#     else:
#         print("No results found or an error occurred.")

# if __name__ == "__main__":
#     main()

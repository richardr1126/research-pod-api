from graph import graph
import sys


def websearch(query):
    try:
        input_data = {
            "research_topic": query
        }
        print("Executing graph...")
        result = graph.invoke(input_data)
        print("Graph executed successfully.")
        # return result
        return result['sources_gathered']['results']
    except Exception as e:
        print(f"Error during web search: {e}")
        return None
        
# TESTING #
def main():
    if len(sys.argv) < 2:
        print("Usage: python test_search.py 'your search query'")
        return
    
    query = sys.argv[1]
    print(f"Searching for: {query}")
    
    results = websearch(query)
    
    if results:
        print("\nSearch Results:")
        print(results)
        # for i, result in enumerate(results['results'], 1):
        #     print(f"\n--- Result {i} ---")
        #     print(f"Title: {result.get('title', 'N/A')}")
        #     print(f"URL: {result.get('url', 'N/A')}")
        #     print(f"Content snippet: {result.get('content', 'N/A')[:150]}...")
    else:
        print("No results found or an error occurred.")

if __name__ == "__main__":
    main()

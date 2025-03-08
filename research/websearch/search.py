from research.websearch.graph import graph


def websearch(query):
    try:
        input_data = {
            "research_topic": query
        }
        print("Executing graph...")
        result = graph.invoke(input_data)
        print("Graph executed successfully.")
        return result['running_summary']
    except Exception as e:
        print(f"Error during web search: {e}")
        return None
        
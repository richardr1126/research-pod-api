import os
import time
# from dotenv import load_dotenv
from research.websearch.graph import graph
# from research.scraper.nlp import setup_client, send_messages
# # Start timing
# start_time = time.time()

# # Load environment variables from .env file
# load_dotenv()

# # Debug: Print environment variables
# print(f"DEEPSEEK_API_KEY exists: {os.getenv('DEEPSEEK_API_KEY') is not None}")

# query = "Research the history of Boulder, Colorado."

# input_data = {
#     "research_topic": query
# }

# result = graph.invoke(input_data)
# print("\n\n" + result['running_summary'])
# print("\n\n\n")
# print(result['sources_gathered'])

# # Calculate and print elapsed time
# end_time = time.time()
# elapsed_time = end_time - start_time
# print(f"\nTotal execution time: {elapsed_time:.2f} seconds")


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
        
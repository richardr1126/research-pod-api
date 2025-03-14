import os
import time
from dotenv import load_dotenv
from research.websearch2.graph import graph

# Start timing
start_time = time.time()

# Load environment variables from .env file
load_dotenv()

# Debug: Print environment variables
print(f"DEEPSEEK_API_KEY exists: {os.getenv('DEEPSEEK_API_KEY') is not None}")

query = "Research the history of Boulder, Colorado."

input_data = {
    "research_topic": query
}

result = graph.invoke(input_data)


# print("\n\n" + result['running_summary'])
# print("\n\n\n")
# print(result['sources_gathered'])

# Calculate and print elapsed time
end_time = time.time()
elapsed_time = end_time - start_time
print(f"\nTotal execution time: {elapsed_time:.2f} seconds")


print(result['sources_gathered']['results'])
print(result['sources_gathered']['results'][0]['content'])

# import requests
# import json
# import time

# # Make the initial request
# url = "http://localhost:8888/v1/websearch"
# payload = {"query": "legal natural language processing"}
# headers = {"Content-Type": "application/json"}

# response = requests.post(url, json=payload, headers=headers)
# initial_response = response.json()
# print(json.dumps(initial_response, indent=2))

# # Check if we got a task_id
# if "task_id" in initial_response:
#     task_id = initial_response["task_id"]
    
#     # Poll for results
#     print("\nPolling for results...")
#     status_url = f"http://localhost:8888/v1/websearch/status/{task_id}"
    
#     while True:
#         status_response = requests.get(status_url).json()
        
#         if status_response["status"] == "completed":
#             print("\nSearch completed!")
#             print(json.dumps(status_response, indent=2))
#             break
#         elif status_response["status"] == "failed":
#             print("\nSearch failed!")
#             print(json.dumps(status_response, indent=2))
#             break
#         else:
#             print(".", end="", flush=True)
#             time.sleep(2)  # Wait 2 seconds before checking again
# else:
#     print("Error: No task_id in response")
import os
from dotenv import load_dotenv
from graph import graph

# Load environment variables from .env file
load_dotenv()

# Debug: Print environment variables
print(f"DEEPSEEK_API_KEY exists: {os.getenv('DEEPSEEK_API_KEY') is not None}")

query = "Research everything about bees."

input_data = {
    "research_topic": query
}

result = graph.invoke(input_data)
print(result)
from openai import OpenAI
from typing import List, Dict
from dataclasses import dataclass
import os
import json

def setup_client():
    """Initialize DeepSeek Chat client with API key from environment"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable is required")
    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )

def send_messages(client, messages, tools):
    """Send messages to DeepSeek Chat API"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools
    )
    return response.choices[0].message

def process_search_query(query: str) -> List[List[str]]:
    """
    Process a search query using DeepSeek Chat's function calling to extract and categorize keywords.
    The function uses example-based categorization to guide the model.
    
    Args:
        query (str): The search query to process
        
    Returns:
        List[List[str]]: List of categorized keyword groups
    """
    client = setup_client()
    
    # Define the function schema
    tools = [
        {
            "type": "function",
            "function": {
                "name": "categorize_keywords",
                "description": "Extract and categorize keywords from a search query into semantically related groups",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keyword_groups": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "keywords": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "List of related keywords"
                                    },
                                    "category": {
                                        "type": "string",
                                        "description": "Category name for this group of keywords"
                                    }
                                },
                                "required": ["keywords", "category"]
                            },
                            "description": "List of semantically related keyword groups"
                        }
                    },
                    "required": ["keyword_groups"]
                }
            }
        }
    ]

    example = """
    Example categorization:
    Query: "Impact of COVID-19 on medical imaging using artificial intelligence"
    Categories:
    covid19 = ['COVID-19', 'SARS-CoV-2']
    ai = ['Artificial intelligence', 'Deep learning', 'Machine learning']
    mi = ['Medical imaging']
    """

    # Initial message to process the query
    messages = [
        {
            "role": "system",
            "content": f"Extract and categorize keywords from the search query into semantically related groups. Group similar or related terms together. {example}"
        },
        {
            "role": "user",
            "content": query
        }
    ]

    # Get initial response with function call
    message = send_messages(client, messages, tools)
    
    # Parse the response
    try:
        if message.tool_calls and message.tool_calls[0].function.name == "categorize_keywords":
            result = json.loads(message.tool_calls[0].function.arguments)
            return [group['keywords'] for group in result['keyword_groups']]
    except (json.JSONDecodeError, AttributeError, KeyError) as e:
        print(f"Error processing DeepSeek Chat response: {e}")
    
    # Fallback: return the entire query as a single group
    return [[query]]
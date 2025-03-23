from typing import List
from pydantic import BaseModel, Field
from langchain_openai import AzureChatOpenAI
from langchain_deepseek import ChatDeepSeek
import os
import json

class KeywordGroup(BaseModel):
    """Structure for a group of related keywords"""
    keywords: List[str] = Field(description="List of related keywords")
    category: str = Field(description="Category name for this group of keywords")

class KeywordCategories(BaseModel):
    """Structure for categorized keyword groups"""
    keyword_groups: List[KeywordGroup] = Field(description="List of semantically related keyword groups")

def setup_client():
    """Initialize Azure OpenAI client with LangChain"""
    # Getting ready to fully switch to Azure AI, contact me for keys
    # return AzureChatOpenAI(
    #     openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
    #     azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    #     azure_deployment='gpt-4o-mini',
    #     api_version="2025-02-01-preview",
    # )
    return ChatDeepSeek(
        model='deepseek-chat',
        api_key=os.getenv("DEEPSEEK_API_KEY")
    )


def process_search_query(query: str) -> List[List[str]]:
    """
    Process a search query using Azure OpenAI to extract and categorize keywords.
    
    Args:
        query (str): The search query to process
        
    Returns:
        List[List[str]]: List of categorized keyword groups
    """
    client = setup_client()
    
    # Create a model with structured output
    model_with_structure = client.with_structured_output(KeywordCategories)
    
    system_prompt = """Extract and categorize keywords from the search query into semantically related groups. 
    Group similar or related terms together.
    
    Example categorization:
    Query: "Impact of COVID-19 on medical imaging using artificial intelligence"
    Should produce groups like:
    - COVID-19 related: ['COVID-19', 'SARS-CoV-2']
    - AI related: ['Artificial intelligence', 'Deep learning', 'Machine learning']
    - Medical imaging: ['Medical imaging']
    """
    
    # Get categorized keywords
    try:
        result = model_with_structure.invoke(
            f"{system_prompt}\n\nQuery: {query}"
        )
        return [group.keywords for group in result.keyword_groups]
    except Exception as e:
        print(f"Error processing Azure OpenAI response: {e}")
        return [[query]]
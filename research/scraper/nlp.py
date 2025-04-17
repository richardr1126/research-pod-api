from typing import List
from pydantic import BaseModel, Field
from langchain_openai import AzureChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import json

class KeywordGroup(BaseModel):
    """Structure for a group of related keywords"""
    keywords: List[str] = Field(description="List of related keywords")
    category: str = Field(description="Category name for this group of keywords")

class KeywordCategories(BaseModel):
    """Structure for categorized keyword groups"""
    keyword_groups: List[KeywordGroup] = Field(description="List of semantically related keyword groups")

class PodcastTitle(BaseModel):
    """Structure for a podcast title"""
    title: str = Field(description="A short, catchy title for the podcast episode based on the transcript.")

def setup_client():
    """Initialize Azure OpenAI client with LangChain"""
    # Getting ready to fully switch to Azure AI, contact me for keys
    # return AzureChatOpenAI(
    #     openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
    #     azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    #     azure_deployment='gpt-4o-mini',
    #     api_version="2025-02-01-preview",
    # )
    return ChatGoogleGenerativeAI(
        model='gemini-2.0-flash',
        api_key=os.getenv("GOOGLE_API_KEY"),
    )


def process_search_query(query: str) -> List[List[str]]:
    """
    Process a search query using Google Generative AI to extract and categorize keywords.
    
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

def generate_podcast_title(transcript: str, query: str) -> str:
    """
    Generate a short title for a podcast episode based on its transcript and the original search query.
    
    Args:
        transcript (str): The full transcript of the podcast episode.
        query (str): The original search query related to the podcast.
        
    Returns:
        str: A short, catchy title for the podcast.
    """
    client = setup_client()
    
    # Create a model with structured output for the title
    model_with_structure = client.with_structured_output(PodcastTitle)
    
    system_prompt = """Analyze the provided podcast transcript and the original search query to generate a short, catchy, and relevant title for the episode. 
    The title should capture the main topic or essence of the discussion, considering the context provided by the query. Aim for a title that is concise and engaging."""
    
    # Get the structured title
    try:
        result = model_with_structure.invoke(
            f"{system_prompt}\\n\\nOriginal Query: {query}\\n\\nTranscript:\\n{transcript}"
        )
        return result.title
    except Exception as e:
        print(f"Error generating podcast title: {e}")
        # Fallback to the first few words of the query
        query_words = query.split()
        fallback_title = " ".join(query_words[:5]) # Use first 5 words
        if len(query_words) > 5:
            fallback_title += "..."
        return fallback_title if fallback_title else "Podcast Episode" # Ensure there's always some fallback
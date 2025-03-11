import asyncio
from crawl4ai import *
import os
from openai import OpenAI

DEEPSEEK_API_KEY="sk-6b8a10306276448f958e79eab1a4a56d"

def setup_client():
    """Initialize DeepSeek Chat client with API key from environment"""
    api_key = DEEPSEEK_API_KEY
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable is required")
    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )

def send_messages(client, messages):
    """Send messages to DeepSeek Chat API"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages
    )
    return response.choices[0].message


async def main():
    print("Starting web crawl...")
    try:
        # Add a timeout to the crawler
        async with AsyncWebCrawler() as crawler:
            # Set a timeout for the crawl operation
            result = await asyncio.wait_for(
                crawler.arun(
                    url="https://en.wikipedia.org/wiki/Timeline_of_Boulder,_Colorado",
                    # Try with a simpler page if Wikipedia is causing issues
                    # url="https://example.com",
                ),
                timeout=60  # 60 second timeout
            )
            print("Page crawled successfully!")
            
            # Check if we got valid content
            if not result or not hasattr(result, 'markdown') or not result.markdown:
                print("Error: No valid content was retrieved from the webpage")
                return
                
            # Proceed with LLM processing
            print("Sending to LLM for summarization...")
            client = setup_client()
            messages = [
                {"role": "system", "content": "You are a helpful assistant that summarizes web content."},
                {"role": "user", "content": f"Summarize the following web content:\n\n{result.markdown[:4000]}"}  # Limit content size
            ]

            llm_call = send_messages(client, messages)
            print("LLM Response:")
            print(llm_call.content)
            print("\n\n\n")
            print(result.markdown)
            
    except asyncio.TimeoutError:
        print("Error: Web crawling operation timed out after 60 seconds")
    except Exception as e:
        print(f"Error during execution: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
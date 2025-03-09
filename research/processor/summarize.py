# This can probably be added the the nlp file

import os
import json
import traceback
from research.scraper.nlp import setup_client, send_messages

def process_papers(papers_data):
    """
    Process the papers data using an LLM to generate a summary
    
    Args:
        papers_data (list): List of paper data from the scrape endpoint
        
    Returns:
        str: A summary of the papers
    """
    try:
        client = setup_client()
        
        arxiv_papers = papers_data['papers']
        web_results = papers_data['websearch']

        # Extract titles and abstracts for the prompt
        papers_info = []
        for i, paper in enumerate(arxiv_papers, 1):
            papers_info.append(f"Paper {i}:\nTitle: {paper.get('title', 'N/A')}\nAbstract: {paper.get('abstract', 'N/A')}")
        
        papers_text = "\n\n".join(papers_info)


        # Create websearch text
        websearch_text = ""
        for i, content in enumerate(web_results, 1):
            websearch_text += f"Web Search Result {i}:\n{content}\n\n"
        
        # Define the function schema for summarization
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "summarize_papers",
                    "description": "Generate a comprehensive summary of research papers",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "A markdown-formatted summary of the papers"
                            },
                            "main_themes": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of main themes across the papers"
                            },
                            "key_findings": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of key findings or methodologies"
                            },
                            "applications": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of potential applications or implications"
                            }
                        },
                        "required": ["summary"]
                    }
                }
            }
        ]
        
        # Create messages for the LLM
        messages = [
            {
                "role": "system",
                "content": "You are a helpful research assistant that summarizes academic papers and web search results. Your goal is to synthesize information from both academic and web sources into a coherent summary."
            },
            {
                "role": "user", 
                "content": f"""I have collected the following research papers and web search results:

<Academic Papers>
{papers_text}
</Academic Papers>

<Web Search Results>
{websearch_text}
</Web Search Results>

Please analyze these sources and provide:
1. A concise summary of the main themes across both academic and web sources
2. Key findings or methodologies mentioned in the papers and web results
3. Potential applications or implications of this research

Format your response in markdown."""
            }
        ]
        
        # Send the request using the function from nlp.py
        # message = send_messages(client, messages, tools)
        message = send_messages(client, messages)
        
        # Parse the response
        try:
            if message.tool_calls and message.tool_calls[0].function.name == "summarize_papers":
                result = json.loads(message.tool_calls[0].function.arguments)
                
                # Format the response in markdown
                markdown_response = f"# Research Summary\n\n"
                markdown_response += f"{result.get('summary', '')}\n\n"
                
                if 'main_themes' in result and result['main_themes']:
                    markdown_response += "## Main Themes\n\n"
                    for theme in result['main_themes']:
                        markdown_response += f"- {theme}\n"
                    markdown_response += "\n"
                
                if 'key_findings' in result and result['key_findings']:
                    markdown_response += "## Key Findings\n\n"
                    for finding in result['key_findings']:
                        markdown_response += f"- {finding}\n"
                    markdown_response += "\n"
                
                if 'applications' in result and result['applications']:
                    markdown_response += "## Applications & Implications\n\n"
                    for app in result['applications']:
                        markdown_response += f"- {app}\n"
                
                return markdown_response
            else:
                # If function calling didn't work, use the content directly
                return message.content or "No summary was generated."
        except (json.JSONDecodeError, AttributeError, KeyError) as e:
            print(f"Error parsing LLM response: {e}")
            # Fallback to using the content directly
            return message.content or f"Error parsing summary: {str(e)}"
            
    except Exception as e:
        print(f"Error in process_papers: {str(e)}")
        print(traceback.format_exc())
        return f"Error generating summary: {str(e)}" 
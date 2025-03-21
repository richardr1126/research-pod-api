# import json

from typing_extensions import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.output_parsers import JsonOutputParser
# from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel#, Field
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph

from configuration import Configuration, SearchAPI
from utils import deduplicate_and_format_sources, duckduckgo_search
from state import SummaryState, SummaryStateInput, SummaryStateOutput
from prompts import query_writer_instructions, summarizer_instructions, reflection_instructions, podcast_script_instructions

import os
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

# LOCAL TESTING
# from dotenv import load_dotenv
# load_dotenv()
# deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

# Nodes
def generate_query(state: SummaryState, config: RunnableConfig):
    """ Generate a query for web search """
    print("Generating query...")
    # Format the prompt
    query_writer_instructions_formatted = query_writer_instructions.format(research_topic=state.research_topic)
    
    # Generate a query
    # configurable = Configuration.from_runnable_config(config)
    llm = ChatOpenAI(model="deepseek-chat",base_url="https://api.deepseek.com",api_key=deepseek_api_key,temperature=0)
    
    # Set up JSON output parser
    class QueryOutput(BaseModel):
        query: str
        aspect: str
        rationale: str

    parser = JsonOutputParser(pydantic_object=QueryOutput)

    chain = llm | parser

    # result = chain.invoke({"query": "Generate a query for web search:"})
    result = chain.invoke(
        [SystemMessage(content=query_writer_instructions_formatted + f"\n\n{parser.get_format_instructions()}"),
        HumanMessage(content=f"Generate a query for web search:")]
    )

    query = result

    return {"search_query": query['query']}

def web_research(state: SummaryState, config: RunnableConfig):
    """ Gather information from the web """
    print("Gathering information from the web...")
    # Configure
    configurable = Configuration.from_runnable_config(config)

    try:
        search_results = duckduckgo_search(state.search_query, max_results=3, fetch_full_page=configurable.fetch_full_page)
        search_str = deduplicate_and_format_sources(search_results, max_tokens_per_source=1000, include_raw_content=True)
    except:
        raise ValueError(f"Unsupported search API: {configurable.search_api}")

    # Add the formatted search results to web_research_results
    state.web_research_results.append(search_str)
    
    # Return the search results dictionary
    return {"sources_gathered": search_results}

def summarize_sources(state: SummaryState, config: RunnableConfig):
    """ Summarize the gathered sources """
    print("Summarizing the gathered sources...")
    # Existing summary
    existing_summary = state.running_summary

    # Most recent web research
    most_recent_web_research = state.web_research_results[-1]

    # Build the human message
    if existing_summary:
        human_message_content = (
            f"<User Input> \n {state.research_topic} \n <User Input>\n\n"
            f"<Existing Summary> \n {existing_summary} \n <Existing Summary>\n\n"
            f"<New Search Results> \n {most_recent_web_research} \n <New Search Results>"
        )
    else:
        human_message_content = (
            f"<User Input> \n {state.research_topic} \n <User Input>\n\n"
            f"<Search Results> \n {most_recent_web_research} \n <Search Results>"
        )

    # Run the LLM
    configurable = Configuration.from_runnable_config(config)
    llm = ChatOpenAI(model="deepseek-chat",base_url="https://api.deepseek.com",api_key=deepseek_api_key,temperature=0)
    result = llm.invoke(
        [SystemMessage(content=summarizer_instructions),
        HumanMessage(content=human_message_content)]
    )

    running_summary = result.content

    # TODO: This is a hack to remove the <think> tags w/ Deepseek models
    # It appears very challenging to prompt them out of the responses
    while "<think>" in running_summary and "</think>" in running_summary:
        start = running_summary.find("<think>")
        end = running_summary.find("</think>") + len("</think>")
        running_summary = running_summary[:start] + running_summary[end:]

    return {"running_summary": running_summary}

def reflect_on_summary(state: SummaryState, config: RunnableConfig):
    """ Reflect on the summary and generate a follow-up query """
    print("Reflecting on the summary and generating a follow-up query...")
    # Generate a query
    configurable = Configuration.from_runnable_config(config)
    llm = ChatOpenAI(model="deepseek-chat",base_url="https://api.deepseek.com",api_key=deepseek_api_key,temperature=0)
    
    # Set up JSON output parser
    class QueryOutput(BaseModel):
        knowledge_gap: str
        follow_up_query: str

    parser = JsonOutputParser(pydantic_object=QueryOutput)

    chain = llm | parser

    result = chain.invoke(
        [SystemMessage(content=reflection_instructions.format(research_topic=state.research_topic) + f"\n\n{parser.get_format_instructions()}"),
        HumanMessage(content=f"Identify a knowledge gap and generate a follow-up web search query based on our existing knowledge: {state.running_summary}")]
    )

    # Get the follow-up query
    query = result.get('follow_up_query')

    # JSON mode can fail in some cases
    if not query:

        # Fallback to a placeholder query
        return {"search_query": f"Tell me more about {state.research_topic}"}

    # Update search query with follow-up query
    return {"search_query": result['follow_up_query']}

def finalize_summary(state: SummaryState):
    """ Finalize the summary """
    print("Finalizing the summary...")
    # Format all accumulated sources into a single bulleted list
    all_sources = "\n".join(source for source in state.sources_gathered)
    state.running_summary = f"## Summary\n\n{state.running_summary}\n\n ### Sources:\n{all_sources}"
    return {"running_summary": state.running_summary}

def debug_state(state: SummaryState):
    """ Debug the current state """
    print(f"DEBUG STATE: {vars(state)}")
    # Just pass through without modifying
    return {}

def route_research(state: SummaryState, config: RunnableConfig) -> Literal["finalize_summary", "web_research"]:
    """ Route the research based on the follow-up query """
    print("Routing the research...")
    configurable = Configuration.from_runnable_config(config)
    if state.research_loop_count <= configurable.max_web_research_loops:
        return "web_research"
    else:
        return "finalize_summary"

# Add nodes and edges
builder = StateGraph(SummaryState, input=SummaryStateInput, output=SummaryStateOutput, config_schema=Configuration)
builder.add_node("generate_query", generate_query)
builder.add_node("web_research", web_research)

# Add edges
builder.add_edge(START, "generate_query")
builder.add_edge("generate_query", "web_research")
builder.add_edge("web_research", END)

graph = builder.compile()
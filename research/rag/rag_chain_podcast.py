"""
RAG chain implementation using LangChain, DeepSeek Chat, and Milvus Lite.
"""
import os
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_deepseek import ChatDeepSeek
from typing import List, Any
from . import vector_store

# Initialize components
llm = ChatDeepSeek(
    model='deepseek-chat',
    api_key=os.getenv("DEEPSEEK_API_KEY")
)

# Define the prompt template for generating AI responses
prompt = PromptTemplate(
    template="""
    Human: You are an expert podcast script writer for a research podcast generator. This process started with a user topic: {research_topic}. Your task is to generate a podcast script that will be read verbatim by a single host using a text-to-speech model. The script should be plain text only, with no additional formatting or extra instructions, and should not include any introductions or host names—the words are read exactly as they appear.

    <GOAL>
    1. Convert the provided context into a podcast script that flows naturally in a conversational style.
    2. Ensure the script is engaging and informative for a general audience.
    3. Include all relevant information from the context, keeping the script concise and focused on the topic.
    4. The script is intended for a single host reading the words directly off the page via a text-to-speech model.
    </GOAL>

    <EXAMPLE>
    Example output:
    Today, we dive into the fascinating world of artificial intelligence, exploring its latest trends and the innovations shaping our future. Stay tuned as we uncover key insights from recent research.
    </EXAMPLE>

    <context>
    {context}
    </context>

    Assistant:""",
    input_variables=["context", "research_topic"]
)

def _format_docs(docs: List[Any]) -> str:
    """Format retrieved documents into a string."""
    return "\n\n".join(doc.page_content for doc in docs)

# Build the RAG chain
chain = (
    {
        "context": vector_store.milvus.as_retriever() | _format_docs,
        "research_topic": RunnablePassthrough()
    }
    | prompt
    | llm
    | StrOutputParser()
)

    

def query(research_topic: str) -> str:
    """
    Query the RAG chain with a research topic.
    
    Args:
        research_topic: The research topic to answer
        
    Returns:
        Generated answer based on retrieved context
    """
    return chain.invoke(research_topic)
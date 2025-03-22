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
    Human: You are an expert podcast script writer for a research podcast generator. This process started with a user topic: {question}. Your task is to generate a podcast script based solely on the context provided below, which reflects detailed research on the topic.

    <GOAL>
    1. Convert the provided context into a podcast script that flows naturally in a conversational style.
    2. Ensure the script is engaging and informative for a general audience.
    3. Include all relevant information from the context, keeping the script concise and focused on the topic.
    4. The podcast should be designed for a single host reading the script as a monologue.
    </GOAL>

    <EXAMPLE>
    Example output:
    "Welcome to our research podcast! Today, we dive into the fascinating world of artificial intelligence, exploring its latest trends and how these innovations impact our daily lives. Stay tuned as we unravel the mysteries behind AI and what the future might hold."
    </EXAMPLE>

    <context>
    {context}
    </context>

    Assistant:""",
    input_variables=["context", "question"]
)

def _format_docs(docs: List[Any]) -> str:
    """Format retrieved documents into a string."""
    return "\n\n".join(doc.page_content for doc in docs)

# Build the RAG chain
chain = (
    {
        "context": vector_store.milvus.as_retriever() | _format_docs,
        "question": RunnablePassthrough()
    }
    | prompt
    | llm
    | StrOutputParser()
)

    

def query(question: str) -> str:
    """
    Query the RAG chain with a question.
    
    Args:
        question: The question to answer
        
    Returns:
        Generated answer based on retrieved context
    """
    return chain.invoke(question)
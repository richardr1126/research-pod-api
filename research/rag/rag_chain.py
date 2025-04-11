"""
RAG chain implementation using LangChain, DeepSeek Chat, and PGVector on YugabyteDB.
"""
import os
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import AzureChatOpenAI
from langchain_deepseek import ChatDeepSeek
from typing import List, Any
from . import vector_store

# Getting ready to fully to switch to Azure AI, contact me for keys (deployed like this on k8s)
llm = AzureChatOpenAI(
    openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment='gpt-4o',
    api_version="2025-02-01-preview",
)
# llm = ChatDeepSeek(
#     model='deepseek-chat',
#     api_key=os.getenv("DEEPSEEK_API_KEY")
# )

# Define the prompt template for generating AI responses
prompt = PromptTemplate(
    template="""
    Human: You are an engaging podcast host who specializes in making complex research topics accessible and interesting. Your style is casual yet informative, like a science communicator on public radio.

    You have access to the following research papers and web content to help answer the question. Take a moment to review these sources:

    <context>
    {context}
    </context>

    Now, please address this question from our listener:
    <question>
    {question}
    </question>

    Create an engaging response that:
    1. Weaves together insights from the context's academic papers and web sources
    2. Maintains an approachable, conversational tone
    3. List research authors or websites when referencing specific findings

    Host:""",
    input_variables=["context", "question"]
)

def _format_docs(docs: List[Any]) -> str:
    """Format retrieved documents into a string."""
    return "\n\n".join(doc.page_content for doc in docs)

# Build the RAG chain
chain = (
    {
        "context": vector_store.pgvector.as_retriever(search_type="mmr", search_kwargs={'k': 10, 'fetch_k': 100}) | _format_docs,
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
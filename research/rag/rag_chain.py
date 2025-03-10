"""
RAG chain implementation using LangChain, DeepSeek Chat, and Milvus Lite.
"""
import os
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_deepseek import ChatDeepSeek
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Any
from . import vector_store

# Initialize components
llm = ChatDeepSeek(
    model='deepseek-chat',
    api_key=os.getenv("DEEPSEEK_API_KEY")
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200
)

# Define the prompt template for generating AI responses
prompt = PromptTemplate(
    template="""
      You are an AI research assistant that helps users understand academic papers.
      Use the following pieces of information to provide a detailed and specific answer to the question.
      Use quotes and cite paper titles when possible.

      Context:
      {context}

      Question:
      {question}

      Answer:""",
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

def add_papers(papers: List[Dict[str, Any]], job_id: str = None):
    """
    Add research papers to the vector store.
    
    Args:
        papers: List of paper dictionaries containing metadata and content
        job_id: Optional job ID to associate with the documents (not used for filtering)
    """
    for paper in papers:
        # Create metadata dictionary
        metadata = {
            "title": paper.get("title", ""),
            "authors": paper.get("authors", ""),
            "doi": paper.get("doi", ""),
            "date": paper.get("date", ""),
            "journal": paper.get("journal", ""),
            "abstract": paper.get("abstract", "")
        }
        
        # Split the paper text into chunks
        chunks = text_splitter.create_documents(
            texts=[paper["text"]],
            metadatas=[metadata]
        )
        
        # Add chunks to vector store
        vector_store.milvus.add_documents(chunks)

def query(question: str) -> str:
    """
    Query the RAG chain with a question.
    
    Args:
        question: The question to answer
        
    Returns:
        Generated answer based on retrieved context
    """
    return chain.invoke(question)
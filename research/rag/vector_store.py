"""
Vector store implementation using PGVector on YugabyteDB.
"""

import os
from typing import List, Any, Dict
from langchain_openai.embeddings import AzureOpenAIEmbeddings, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from uuid_v7.base import uuid7

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200
)

# Getting ready to fully switch to Azure AI, contact me for keys
embeddings = AzureOpenAIEmbeddings(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment="text-embedding-3-large",
    api_version="2025-02-01-preview",
)
# embeddings = OpenAIEmbeddings(
#     api_key=os.getenv("OPENAI_API_KEY"),
#     model="text-embedding-3-large",
# )

pgvector = PGVector(
    embeddings=embeddings,
    collection_name=f"research-{uuid7()}",
    connection=os.getenv("SQLALCHEMY_DATABASE_URI"),
    use_jsonb=True,
    create_extension=False
)

def add_documents(documents: List[Dict[str, Any]], doc_type: str = "paper"):
    """
    Add documents to the vector store.
    
    Args:
        documents: List of document dictionaries containing metadata and content
        doc_type: Type of document ("paper" or "websearch") to determine content field
    """
    for doc in documents:
        # Create metadata dictionary
        metadata = {
            "doc_type": doc_type,
            "title": doc.get("title", ""),
            "url": doc.get("url", ""),
            "authors": doc.get("authors", ""),
            "doi": doc.get("doi", ""),
            "date": doc.get("date", ""),
            "journal": doc.get("journal", ""),
            "abstract": doc.get("abstract", "")
        }
        
        # Get content based on document type
        content = doc.get("text" if doc_type == "paper" else "content", "")
        
        # Split the document text into chunks
        chunks = text_splitter.create_documents(
            texts=[content],
            metadatas=[metadata]
        )
        
        # Add chunks to vector store
        pgvector.add_documents(chunks)

def clear():
    """
    Clear all documents from the vector store.
    """
    try:
        # Delete the collection
        pgvector.delete_collection()
        
        # Recreate the collection
        pgvector.create_collection()
    except Exception as e:
        raise  # Re-raise the exception to make sure caller knows about the failure

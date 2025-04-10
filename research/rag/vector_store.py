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

# Create separate vector stores for documents and transcripts
pgvector = PGVector(
    embeddings=embeddings,
    collection_name=f"research-docs-{uuid7()}",
    connection=os.getenv("SQLALCHEMY_DATABASE_URI"),
    use_jsonb=True,
    create_extension=False
)

transcript_store = PGVector(
    embeddings=embeddings,
    collection_name="research-transcripts",  # Fixed collection name for transcripts
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
        # Only delete the documents collection, keep transcripts
        pgvector.delete_collection()
        pgvector.create_collection()
    except Exception as e:
        raise  # Re-raise the exception to make sure caller knows about the failure

def add_transcript(transcript: str, pod_id: str):
    """
    Add a research pod transcript to the permanent vector store.
    
    Args:
        transcript: The transcript text to embed
        pod_id: The ID of the research pod
    """
    try:
        # Create metadata
        metadata = {
            "doc_type": "transcript",
            "pod_id": pod_id
        }
        
        # Split the transcript text into chunks
        chunks = text_splitter.create_documents(
            texts=[transcript],
            metadatas=[metadata]
        )
        
        # Add chunks to transcript store
        transcript_store.add_documents(chunks)
        return True
    except Exception as e:
        print(f"Error adding transcript: {e}")
        return False

def get_similar_transcripts(pod_id: str, text: str, k: int = 5) -> List[str]:
    """
    Find similar research pods based on transcript content.
    
    Args:
        text: Text to find similar transcripts for
        k: Number of similar transcripts to return
        
    Returns:
        List of pod IDs
    """
    try:
        # Search for similar transcripts
        docs = transcript_store.max_marginal_relevance_search(text, k=k)
        
        # Extract unique pod IDs
        seen_pods = set()
        recommendations = []
        
        for doc in docs:
            similar_pod_id = doc.metadata.get("pod_id")
            # Only include unique pods
            if similar_pod_id and similar_pod_id not in seen_pods and similar_pod_id != pod_id:
                seen_pods.add(similar_pod_id)
                recommendations.append(similar_pod_id)
        
        return recommendations[:k]
    except Exception as e:
        print(f"Error getting similar transcripts: {e}")
        return []

"""
Vector store implementation using Milvus Lite for in-memory storage.
"""

import os
from typing import List, Any, Dict
from langchain_milvus import Milvus
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200
)

# Initialize the embeddings model
embeddings = OpenAIEmbeddings(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="text-embedding-3-large",
)

# Initialize Milvus Lite with local file storage
milvus = Milvus(
    auto_id=True,
    embedding_function=embeddings,
    connection_args={"uri": "./data/milvuslite.db"},  # Local file for Milvus Lite
    index_params={"index_type": "AUTOINDEX"},
    drop_old=True,
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
        milvus.add_documents(chunks)

def clear():
    """
    Deletes the DB file and its lock file.
    Ensures proper cleanup by checking file existence and handling errors.
    """
    try:
        # Close the client connection first
        milvus.client.close()
        
        # Define the files to delete
        db_file = "./data/milvuslite.db"
        lock_file = "./data/.milvuslite.db.lock"
        
        # Delete DB file if it exists
        if os.path.exists(db_file):
            os.remove(db_file)
            if os.path.exists(db_file):
                raise Exception(f"Failed to delete {db_file}")
        
        # Delete lock file if it exists
        if os.path.exists(lock_file):
            os.remove(lock_file)
            if os.path.exists(lock_file):
                raise Exception(f"Failed to delete {lock_file}")
        
        print("Successfully deleted Milvus Lite DB and lock files")
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")
        raise  # Re-raise the exception to make sure caller knows about the failure

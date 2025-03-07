"""
Vector store implementation using Milvus Lite for in-memory storage.
"""

import os
from typing import List, Any
from langchain_milvus import Milvus
from langchain_openai.embeddings import OpenAIEmbeddings

# Initialize the embeddings model
embeddings = OpenAIEmbeddings(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="text-embedding-3-large",
)

# Initialize Milvus Lite with local file storage
vectorstore = Milvus(
    auto_id=True,
    embedding_function=embeddings,
    connection_args={"uri": "./milvuslite.db"},  # Local file for Milvus Lite
    index_params={"index_type": "AUTOINDEX"},
    drop_old=True,
)

def similarity_search(query: str, k: int = 4, filter: dict = None) -> List[Any]:
    """
    Search for similar texts in the vector store.

    Args:
        query: Query text
        k: Number of results to return
        filter: Optional filter conditions

    Returns:
        List of similar documents with metadata
    """
    search_kwargs = {}
    if filter:
        search_kwargs["filter"] = filter

    return vectorstore.similarity_search(
        query=query, k=k, search_kwargs=search_kwargs
    )

def clear():
    """
    Deletes the DB file and its lock file.
    Ensures proper cleanup by checking file existence and handling errors.
    """
    try:
        # Close the client connection first
        vectorstore.client.close()
        
        # Define the files to delete
        db_file = "./milvuslite.db"
        lock_file = "./milvuslite.db.lock"
        
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

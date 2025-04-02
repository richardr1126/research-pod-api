!pip install qdrant-client
!pip install sentence_transformers
!pip install -U langchain-community
!pip install -U langchain chromadb openai

# Brings in Chroma, the local vector database (used to store podcast embeddings)
from langchain_community.vectorstores import Chroma

# Lets you generate text embeddings (numerical vectors from podcast summaries) using Azure OpenAI
from langchain.embeddings import OpenAIEmbeddings

# The standard document format LangChain uses: stores page_content and metadata
from langchain.schema import Document

# SQLAlchemy ORM to load data from your ResearchPod model (which has podcast summaries, titles, etc.)
from sqlalchemy.orm import Session
from web.models.pods import ResearchPod  # model from the codebase
import os
from dotenv import load_dotenv

load_dotenv()

# turns text into meaning (vectors)
embedding_model = OpenAIEmbeddings(
    openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
    openai_api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
    openai_api_type="azure",
    openai_api_version="2023-05-15",
    deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
)

PERSIST_DIR = "recommendation_store"

# Loads all podcast summaries
def build_vectorstore_from_db(session: Session):
    pods = session.query(ResearchPod).filter(ResearchPod.summary != None).all()
    docs = [
        Document(page_content=pod.summary, metadata={"title": pod.query})
        for pod in pods
    ]
    vectorstore = Chroma.from_documents(docs, embedding_model, persist_directory=PERSIST_DIR)
    vectorstore.persist()
    return vectorstore

# search for top 5 closest matches
def get_recommendations(query: str, k=5):
    # chroma: memory box that stores and finds vectors
    vectorstore = Chroma(persist_directory=PERSIST_DIR, embedding_function=embedding_model)
    results = vectorstore.similarity_search(query, k=k)
    return [
        {"title": doc.metadata.get("title", "Untitled"), "summary": doc.page_content}
        for doc in results
    ]

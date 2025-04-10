from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from uuid_v7.base import uuid7
import json

db = SQLAlchemy()

class ResearchPods(db.Model):
    __tablename__ = 'research_pods'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid7()))
    query = db.Column(db.String(512), nullable=False)
    audio_url = db.Column(db.String(512))  # Store the URL of the audio file
    keywords_arxiv = db.Column(db.Text)  # Store the keyword groups as JSON dumps list
    sources_arxiv = db.Column(db.Text)  # Store the sources from arXiv as JSON dumps list
    sources_ddg = db.Column(db.Text)  # Store the sources from web search as JSON dumps list
    transcript = db.Column(db.Text)  # Store the transcript text
    status = db.Column(db.String(50), default='QUEUED')  # QUEUED, PROCESSING, COMPLETED, ERROR
    error_message = db.Column(db.Text)
    consumer_id = db.Column(db.String(50))  # Store which consumer processed this
    similar_pods = db.Column(db.Text)  # Store similar pod recommendations as JSON
    created_at = db.Column(db.BigInteger, default=lambda: int(datetime.now(timezone.utc).timestamp()))
    updated_at = db.Column(db.BigInteger, default=lambda: int(datetime.now(timezone.utc).timestamp()), 
                          onupdate=lambda: int(datetime.now(timezone.utc).timestamp()))
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from uuid_v7.base import uuid7
import json

db = SQLAlchemy()

class ResearchPods(db.Model):
    __tablename__ = 'research_pods'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid7()))
    query = db.Column(db.String(512), nullable=False)
    title = db.Column(db.String(256), nullable=False)  # Store the podcast title
    audio_url = db.Column(db.String(512))  # Store the URL of the audio file
    keywords_arxiv = db.Column(db.Text)  # Store the keyword groups as JSON dumps list
    sources_arxiv = db.Column(db.Text)  # Store the sources from arXiv as JSON dumps list
    sources_ddg = db.Column(db.Text)  # Store the sources from web search as JSON dumps list
    transcript = db.Column(db.Text)  # Store the transcript text
    status = db.Column(db.String(50), default='QUEUED')  # QUEUED, PROCESSING, COMPLETED, ERROR
    error_message = db.Column(db.Text)
    consumer_id = db.Column(db.String(50))  # Store which consumer processed this
    similar_pods = db.Column(db.Text)  # Store list of similar pod IDs as JSON
    created_at = db.Column(db.BigInteger, default=lambda: int(datetime.now(timezone.utc).timestamp()))
    updated_at = db.Column(db.BigInteger, default=lambda: int(datetime.now(timezone.utc).timestamp()), 
                          onupdate=lambda: int(datetime.now(timezone.utc).timestamp()))

    def to_dict(self):
        """
        Convert the research pod to a dictionary with hydrated similar pods.
        
        Returns:
            Dictionary representation of the research pod
        """
        result = {
            'id': self.id,
            'query': self.query,
            'title': self.title,
            'audio_url': self.audio_url,
            'keywords_arxiv': json.loads(self.keywords_arxiv) if self.keywords_arxiv else None,
            'sources_arxiv': json.loads(self.sources_arxiv) if self.sources_arxiv else None,
            'sources_ddg': json.loads(self.sources_ddg) if self.sources_ddg else None,
            'transcript': self.transcript,
            'status': self.status,
            'error_message': self.error_message,
            'consumer_id': self.consumer_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

        # Load and hydrate similar pods
        if self.similar_pods:
            similar_pod_ids = json.loads(self.similar_pods)
            similar_pods_hydrated = []
            
            for pod_id in similar_pod_ids:
                similar_pod = db.get_or_404(ResearchPods, pod_id)
                if similar_pod:
                    similar_pods_hydrated.append({
                        'id': similar_pod.id,
                        'title': similar_pod.title,
                        'query': similar_pod.query,
                        'audio_url': similar_pod.audio_url,
                        'created_at': similar_pod.created_at,
                        'updated_at': similar_pod.updated_at,
                    })
            
            result['similar_pods'] = similar_pods_hydrated
        else:
            result['similar_pods'] = None

        return result
    
    def to_short_dict(self):
        """
        Convert the research pod to a short dictionary representation.
        
        Returns:
            Dictionary representation of the research pod
        """
        return {
            'id': self.id,
            'query': self.query,
            'title': self.title,
            'audio_url': self.audio_url,
            'keywords_arxiv': json.loads(self.keywords_arxiv) if self.keywords_arxiv else None,
            'sources_arxiv': json.loads(self.sources_arxiv) if self.sources_arxiv else None,
            'sources_ddg': json.loads(self.sources_ddg) if self.sources_ddg else None,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def create_from_request(cls, query: str):
        """Create a new research pod from an initial request"""
        # Use temp title based on query
        # Fallback to the first few words of the query
        query_words = query.split()
        fallback_title = " ".join(query_words[:5]) # Use first 5 words
        if len(query_words) > 5:
            fallback_title += "..."
        title = fallback_title if fallback_title else "Podcast Episode" # Ensure there's always some fallback

        return cls(
            query=query,
            title=title,    
            status='QUEUED'
        )
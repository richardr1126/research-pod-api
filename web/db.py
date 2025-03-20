from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from uuid_v7.base import uuid7

db = SQLAlchemy()

class ResearchPods(db.Model):
    __tablename__ = 'research_pods'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid7()))
    query = db.Column(db.String(512), nullable=False)
    summary = db.Column(db.Text)
    status = db.Column(db.String(50), default='QUEUED')  # QUEUED, PROCESSING, COMPLETED, ERROR
    error_message = db.Column(db.Text)
    progress = db.Column(db.Integer, default=0)
    consumer_id = db.Column(db.String(50))  # Store which consumer processed this
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'query': self.query,
            'summary': self.summary,
            'status': self.status,
            'error_message': self.error_message,
            'progress': self.progress,
            'consumer_id': self.consumer_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def create_from_request(cls, query: str):
        """Create a new research pod from an initial request"""
        return cls(
            query=query,
            status='QUEUED',
            progress=0
        )
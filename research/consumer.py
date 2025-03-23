"""
Kafka consumer for processing research paper requests.
"""
from flask import Flask, Response, jsonify
from kafka import KafkaConsumer, KafkaProducer
import json
import os
from dotenv import load_dotenv
import logging
import time
from threading import Thread
from queue import Queue
import redis
import socket
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

# Module imports
from scraper.scrape import scrape_arxiv
from rag import rag_chain
from rag import vector_store
from speech.tts import TextToSpeechClient
from db import db, ResearchPods

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', '')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db.init_app(app)

# Queue for SSE updates
progress_queue = Queue()

# Initialize Kafka components
consumer = KafkaConsumer( # Consumer for scrape requests
    'scrape-requests',
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='research-consumer-group',
    max_poll_interval_ms=600000,  # 10 minutes instead of default 5 minutes
    max_poll_records=1,           # Process one record at a time
    session_timeout_ms=60000,     # 1 minute session timeout
    #security_protocol='SSL',
    #ssl_check_hostname=True,
    #ssl_cafile='/etc/kafka/certs/kafka-ca.crt',
)

producer = KafkaProducer( # Producer to return research results
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    #security_protocol='SSL',
    #ssl_check_hostname=True,
    #ssl_cafile='/etc/kafka/certs/kafka-ca.crt',
)

# Initialize Redis client
redis_client = redis.Redis.from_url(
    os.getenv('REDIS_URL', 'redis://localhost:6379'),
    decode_responses=True
)

# Get consumer ID from hostname (for Kubernetes)
hostname = socket.gethostname()
consumer_id = hostname.split('-')[-1] if '-' in hostname else '0'

def send_progress_update(pod_id: str, status: str, progress: int, message: str = None):
    """Send a progress update to both Redis and SSE stream."""
    # Update Redis
    update_data = {
        "status": status,
        "progress": progress,
        "consumer": consumer_id,
        "message": message or f"Processing {status.lower()} at {progress}%"  # Always include a message
    }
    
    redis_client.hset(f"pod:{pod_id}", mapping=update_data)
    
    # Send to SSE stream
    update = {
        "pod_id": pod_id,
        "status": status,
        "progress": progress,
        "message": update_data["message"]  # Always include message in SSE updates too
    }
    progress_queue.put(update)

def process_message(message):
    """Process a Kafka message, performing scraping and RAG."""
    try:
        data = message.value
        query = data.get('query')
        pod_id = data.get('pod_id')
        
        if not query or not pod_id:
            return
            
        # Update Redis with consumer assignment
        redis_client.hset(f"pod:{pod_id}", 
            mapping={
                "status": "ASSIGNED",
                "consumer": consumer_id
            }
        )
        
        send_progress_update(pod_id, "PROCESSING", 0, "Started processing request")
        logger.info(f"Processing scrape request for pod {pod_id}: {query}")
        
        send_progress_update(pod_id, "IN_PROGRESS", 33, "Scraping papers")
        # Scrape papers
        papers, papers_sources = scrape_arxiv(query, max_papers=3)
        logger.info(f"Scraped {len(papers_sources)} results for pod {pod_id}")
        
        send_progress_update(pod_id, "IN_PROGRESS", 66, "Adding papers to vector store")
        # Add papers to vector store
        vector_store.add_documents(papers)
        logger.info(f"Added papers to vector store for pod {pod_id}")
        
        send_progress_update(pod_id, "IN_PROGRESS", 90, "Generating summary")
        # Generate summary
        summary = rag_chain.query(query)
        transcript = summary

        # Generate audio from summary for now
        with TextToSpeechClient() as tts_client:
            audio_data = tts_client.generate_speech(
                text=transcript,
                model="kokoro",
                voice="af_sarah",
                format="mp3",
                speed=1.0
            )
            # Log audio data size instead of storing it for now
            logger.info(f"Generated audio for pod {pod_id}, size: {len(audio_data)} bytes")

        # Single database update at the end
        with app.app_context():
            research_pod = db.session.get(ResearchPods, pod_id)
            if research_pod:
                research_pod.summary = summary
                research_pod.transcript = transcript
                research_pod.sources_arxiv = json.dumps(papers_sources)
                research_pod.status = "COMPLETED"
                research_pod.progress = 100
                research_pod.consumer_id = consumer_id
                research_pod.updated_at = datetime.now(timezone.utc)
                db.session.commit()
                logger.info(f"Updated database for pod {pod_id}")

        # Prepare response
        response = {
            "pod_id": pod_id,
            "query": query,
            "summary": summary,
            "transcript": transcript,
            "sources_arxiv": papers_sources,
        }

        # Send response to Kafka and mark as complete
        producer.send('research-results', key=pod_id.encode('utf-8'), value=response)
        producer.flush()
        send_progress_update(pod_id, "COMPLETED", 100, "Processing complete")
        logger.info(f"Sent research results for pod {pod_id}")
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        error_response = {
            "pod_id": pod_id if 'pod_id' in locals() else None,
            "query": query if 'query' in locals() else None,
            "error": str(e)
        }
        # Update database with error
        with app.app_context():
            try:
                research_pod = db.session.get(ResearchPods, pod_id)
                if research_pod:
                    research_pod.status = "ERROR"
                    research_pod.error_message = str(e)
                    research_pod.updated_at = datetime.now(timezone.utc)
                    db.session.commit()
                    logger.info(f"Updated error status for pod {pod_id}")
            except Exception as db_error:
                logger.error(f"Failed to update error status in database: {str(db_error)}")
        
        producer.send('research-errors', value=error_response)
        producer.flush()
        send_progress_update(pod_id, "ERROR", 0, str(e))

@app.route('/health')
def health():
    """Simple health check endpoint."""
    return jsonify({"status": "ok"})

@app.route('/v1/events/<pod_id>')
def events(pod_id):
    """SSE endpoint for pod progress updates."""
    def generate():
        while True:
            # Get progress update from queue
            try:
                update = progress_queue.get(timeout=30)  # 30 second timeout
                if update["pod_id"] == pod_id:
                    yield f"data: {json.dumps(update)}\n\n"
                    # If pod is complete or errored, stop streaming
                    if update["status"] in ["COMPLETED", "ERROR"]:
                        break
                else:
                    # Put back updates for other pods
                    progress_queue.put(update)
            except Exception:
                # Send keepalive comment every 30 seconds
                yield ": keepalive\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

def run_consumer():
    """Run the Kafka consumer loop."""
    while True:
        try:
            message_batch = consumer.poll(timeout_ms=1000)
            for topic_partition, messages in message_batch.items():
                for message in messages:
                    process_message(message)
                    consumer.commit()
                    
        except Exception as e:
            logger.error(f"Error in consumer loop: {str(e)}", exc_info=True)
            time.sleep(1)

def run():
    """Run both the Flask server and Kafka consumer."""
    # Start consumer in a separate thread
    consumer_thread = Thread(target=run_consumer)
    consumer_thread.daemon = True
    consumer_thread.start()
    
    # Run Flask server
    app.run(host='0.0.0.0', port=8081)

if __name__ == "__main__":
    run()
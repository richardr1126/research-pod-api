"""
Kafka consumer for processing research paper requests.
"""
import logging
import time
import socket
import os
import json
from flask import Flask, Response, jsonify
from flask_cors import CORS
from prometheus_flask_exporter import PrometheusMetrics
from dotenv import load_dotenv
from threading import Thread
from datetime import datetime, timezone
from azure.storage.blob import BlobServiceClient
from kafka import KafkaConsumer, KafkaProducer, TopicPartition, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError, UnknownTopicOrPartitionError
import redis

# Module imports
from scraper.scrape import scrape_arxiv
from scraper.web_scrape import search_and_crawl
from rag import rag_chain, vector_store
from speech.tts import TextToSpeechClient
from db import db, ResearchPods
from scraper.nlp import generate_podcast_title

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', '')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 1800
}

# Initialize SQLAlchemy YugabyteDB connection
db.init_app(app)

# Initialize Azure Blob Storage client
blob_service_client = BlobServiceClient.from_connection_string(
    os.getenv('AZURE_STORAGE_CONNECTION_STRING')
)
blob_storage_container = blob_service_client.get_container_client('researchpod-audio')

# Initialize Kafka components
consumer = KafkaConsumer( # Consumer for scrape requests
    'scrape-requests',
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    #auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='research-consumer-group',
    max_poll_interval_ms=600000,  # 10 minutes instead of default 5 minutes
    max_poll_records=1,           # Process one record at a time
    session_timeout_ms=60000,     # 1 minute session timeout
    security_protocol='SSL',
    ssl_check_hostname=True,
    ssl_cafile='/etc/kafka/certs/kafka-ca.crt',
)

producer = KafkaProducer( # Producer to return research results
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    security_protocol='SSL',
    ssl_check_hostname=True,
    ssl_cafile='/etc/kafka/certs/kafka-ca.crt',
)

# Initialize Kafka Admin Client
admin_client = KafkaAdminClient(
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
    security_protocol='SSL',
    ssl_check_hostname=True,
    ssl_cafile='/etc/kafka/certs/kafka-ca.crt',
)

def create_sse_consumer(pod_id: str) -> KafkaConsumer:
    """Create a new Kafka consumer for SSE updates for a specific pod."""
    try:
        consumer = KafkaConsumer(
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            enable_auto_commit=False,
            auto_offset_reset='earliest',
            group_id=f'sse-group-{pod_id}',  # Unique group ID per pod
            consumer_timeout_ms=1000,  # 1 second timeout
            max_poll_interval_ms=300000,  # 5 minutes
            security_protocol='SSL',
            ssl_check_hostname=True,
            ssl_cafile='/etc/kafka/certs/kafka-ca.crt',
        )
        
        return consumer
    except Exception as e:
        logger.error(f"Error creating SSE consumer: {str(e)}")
        raise

# Initialize Redis client
redis_client = redis.Redis.from_url(
    os.getenv('REDIS_URL', 'redis://localhost:6379'),
    decode_responses=True
)

# Initialize Prometheus metrics
metrics = PrometheusMetrics(app, defaults_prefix='research')
metrics.info('research_info', 'Application info', version='0.0.1')

# Get consumer ID from hostname (for Kubernetes)
hostname = socket.gethostname()
consumer_id = hostname.split('-')[-1] if '-' in hostname else '0'

def send_progress_update(pod_id: str, status: str, progress: int, message: str = None):
    """Send a progress update to both Redis and Kafka stream."""
    # Update Redis
    update_data = {
        "status": status,
        "progress": progress,
        "consumer": consumer_id,
        "message": message or f"Processing {status.lower()} at {progress}%"
    }
    
    redis_client.hset(f"pod:{pod_id}", mapping=update_data)
    
    # Send to Kafka SSE topic
    update = {
        "pod_id": pod_id,
        "status": status,
        "progress": progress,
        "message": update_data["message"]
    }
    producer.send(f'sse-{pod_id}', value=update)
    producer.flush()

def process_message(message):
    """Process a Kafka message, performing scraping and RAG."""
    try:
        data = message.value
        query = data.get('query')
        pod_id = data.get('pod_id')
        
        if not query or not pod_id:
            return
        
        # Create sse topic if it doesn't exist
        try:
            admin_client.create_topics([
                NewTopic(
                    name=f'sse-{pod_id}',
                    num_partitions=1,
                    replication_factor=1
                )
            ])
        except TopicAlreadyExistsError:
            pass
            
        # Update Redis with consumer assignment
        redis_client.hset(f"pod:{pod_id}", 
            mapping={
                "status": "ASSIGNED",
                "consumer": consumer_id
            }
        )
        
        send_progress_update(pod_id, "PROCESSING", 0, "Started processing request")
        logger.info(f"Processing scrape request for pod {pod_id}: {query}")
        
        # First get papers and keyword groups
        send_progress_update(pod_id, "IN_PROGRESS", 20, "Scraping papers")
        papers, papers_sources, papers_keyword_groups = scrape_arxiv(query, max_papers=3)
        logger.info(f"Scraped {len(papers_sources)} results for pod {pod_id}")
        logger.info(f"Using keyword groups: {papers_keyword_groups}")
        
        # Use the same keyword groups for web search
        send_progress_update(pod_id, "IN_PROGRESS", 40, "Searching web pages")
        web_results, ddg_sources = search_and_crawl(papers_keyword_groups, total_limit=4)
        logger.info(f"Found {len(web_results)} web results for pod {pod_id}")
        
        send_progress_update(pod_id, "IN_PROGRESS", 60, "Adding documents to vector store")
        # Add all documents to vector store
        vector_store.add_documents(papers)
        vector_store.add_documents(web_results, doc_type="websearch")
        logger.info(f"Added documents to vector store for pod {pod_id}")
        
        send_progress_update(pod_id, "IN_PROGRESS", 75, "Generating transcript")
        # Generate transcript using RAG
        transcript = rag_chain.query(query)
        logger.info(f"Generated transcript for pod {pod_id}")

        send_progress_update(pod_id, "IN_PROGRESS", 85, "Adding transcript to vector store")
        # Add transcript to permanent vector store
        vector_store.add_transcript(transcript, pod_id)
        logger.info(f"Added transcript to vector store for pod {pod_id}")

        # Get similar pods based on transcript
        similar_pod_ids = vector_store.get_similar_transcripts(pod_id, transcript)
        logger.info(f"Found {len(similar_pod_ids)} similar pods")

        # Generate podcast title
        title = generate_podcast_title(transcript, query)
        logger.info(f"Generated title for podcast: {title}")

        # Clear temporary document embeddings after use
        vector_store.clear()
        logger.info("Cleared temporary document embeddings")

        send_progress_update(pod_id, "IN_PROGRESS", 90, "Generating podcast audio")
        # Generate audio from transcript
        with TextToSpeechClient() as tts_client:
            audio_data = tts_client.generate_speech(
                text=transcript,
                model="kokoro",
                voice="af_sarah",
                format="mp3",
                speed=1.0
            )
            
            # Upload audio to blob storage
            try:
                blob_name = f"{pod_id}/audio.mp3"
                blob_client = blob_storage_container.get_blob_client(blob_name)
                blob_client.upload_blob(audio_data, overwrite=True)
                audio_url = blob_client.url
                logger.info(f"Uploaded audio to blob storage: {audio_url}")
            except Exception as blob_error:
                logger.error(f"Failed to upload audio to blob storage: {str(blob_error)}")
                raise
        
        send_progress_update(pod_id, "IN_PROGRESS", 95, "Saving results to database")
        # Update database entry
        with app.app_context():
            research_pod = db.session.get(ResearchPods, pod_id)
            if research_pod:
                research_pod.title = title
                research_pod.transcript = transcript
                research_pod.keywords_arxiv = json.dumps(papers_keyword_groups)
                research_pod.sources_arxiv = json.dumps(papers_sources)
                research_pod.sources_ddg = json.dumps(ddg_sources)  # Use ddg_sources instead of web_results
                research_pod.audio_url = audio_url
                research_pod.similar_pods = json.dumps(similar_pod_ids)
                research_pod.status = "COMPLETED"
                research_pod.consumer_id = consumer_id
                research_pod.updated_at = int(datetime.now(timezone.utc).timestamp())
                db.session.commit()
                logger.info(f"Updated database for pod {pod_id}")
        
        response = {
            "pod_id": pod_id,
            "audio_url": audio_url,
            "query": query,
            "transcript": transcript,
            "sources_arxiv": papers_sources,
            "sources_ddg": ddg_sources,  # Use ddg_sources instead of web_results
            "keywords_arxiv": papers_keyword_groups,
            "similar_pods": similar_pod_ids
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
                    research_pod.updated_at = int(datetime.now(timezone.utc).timestamp())
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
        sse_consumer = None
        try:
            sse_consumer = create_sse_consumer(pod_id)
            # Subscribe to the specific pod's SSE topic
            topic = f'sse-{pod_id}'
            sse_consumer.subscribe([topic])
            
            # First check Redis for current status
            current_status = redis_client.hgetall(f"pod:{pod_id}")
            if current_status:
                yield f"data: {json.dumps(current_status)}\n\n"
            
            last_keepalive = time.time()
            keepalive_interval = 15  # Send keepalive every 15 seconds
            
            while True:
                # Poll with a short timeout to allow for frequent checks
                message_batch = sse_consumer.poll(timeout_ms=100)
                
                if message_batch:
                    for tp, messages in message_batch.items():
                        for message in messages:
                            if message and message.value:
                                yield f"data: {json.dumps(message.value)}\n\n"
                                sse_consumer.commit()
                                if message.value.get("status") in ["COMPLETED", "ERROR"]:
                                    return
                
                # Send keepalive if needed
                current_time = time.time()
                if current_time - last_keepalive >= keepalive_interval:
                    yield ": keepalive\n\n"
                    last_keepalive = current_time

        except Exception as e:
            logger.error(f"SSE stream error: {str(e)}")
            yield f"data: {json.dumps({'status': 'ERROR', 'message': 'Stream error'})}\n\n"
            
        finally:
            if sse_consumer:
                try:
                    sse_consumer.close()
                except Exception as e:
                    logger.error(f"Error closing SSE consumer: {str(e)}")

    response = Response(generate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    return response

def periodic_sse_topic_cleanup():
    """Periodically clean up SSE topics based on pod completion status and retention time."""
    RETENTION_MINUTES = 20  # Keep completed/error topics for 20 minutes
    CLEANUP_INTERVAL = 2400  # Check every 40 minutes
    
    while True:
        logger.info("Running periodic SSE topic cleanup...")
        try:
            # Get all topics matching the SSE pattern
            all_topics = admin_client.list_topics()
            sse_topics = [t for t in all_topics if t.startswith('sse-')]

            topics_to_delete = []
            current_time = datetime.now(timezone.utc).timestamp()

            for topic in sse_topics:
                try:
                    pod_id = topic.replace('sse-', '')
                    # Check Redis for pod status
                    pod_info = redis_client.hgetall(f"pod:{pod_id}")
                    
                    if not pod_info:
                        with app.app_context():
                            research_pod = db.session.get(ResearchPods, pod_id)
                            if research_pod:
                                status = research_pod.status
                                updated_at = research_pod.updated_at
                            else:
                                # If pod doesn't exist in DB or Redis, delete the topic
                                topics_to_delete.append(topic)
                                continue
                    else:
                        status = pod_info.get('status')
                        updated_at = int(pod_info.get('updated_at', 0))

                    # Delete completed/error topics after retention period
                    if status in ["COMPLETED", "ERROR"]:
                        minutes_since_update = (current_time - updated_at) / 60
                        if minutes_since_update >= RETENTION_MINUTES:
                            topics_to_delete.append(topic)
                            logger.info(f"Marking SSE topic {topic} for deletion - Age: {minutes_since_update:.1f} minutes")
                    # Also delete orphaned topics with no status after retention period
                    elif not status and (current_time - updated_at) / 60 >= RETENTION_MINUTES:
                        topics_to_delete.append(topic)
                        logger.info(f"Marking orphaned SSE topic {topic} for deletion")

                except Exception as topic_error:
                    logger.error(f"Error processing topic {topic}: {str(topic_error)}")
                    continue

            if topics_to_delete:
                try:
                    logger.info(f"Deleting {len(topics_to_delete)} expired SSE topics: {topics_to_delete}")
                    admin_client.delete_topics(topics_to_delete)
                    
                    # Clean up Redis keys for deleted topics
                    for topic in topics_to_delete:
                        pod_id = topic.replace('sse-', '')
                        redis_client.delete(f"pod:{pod_id}")
                        
                except Exception as delete_error:
                    logger.error(f"Failed to delete topics: {str(delete_error)}")
            else:
                logger.info("No SSE topics found matching retention criteria for deletion")

        except Exception as e:
            logger.error(f"Error during periodic SSE topic cleanup: {str(e)}", exc_info=True)

        # Sleep until next cleanup interval
        time.sleep(CLEANUP_INTERVAL)

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
    
    # Start cleanup thread
    cleanup_thread = Thread(target=periodic_sse_topic_cleanup)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    
    # Run Flask server
    app.run(host='0.0.0.0', port=8081)

if __name__ == "__main__":
    run()
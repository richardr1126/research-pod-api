"""
Kafka consumer for processing research paper requests.
"""
from flask import Flask, Response, jsonify
from kafka import KafkaConsumer, KafkaProducer
import json
import os
from dotenv import load_dotenv
from scraper.scrape import scrape_arxiv
from rag import rag_chain
import logging
import time
from threading import Thread
from queue import Queue
import threading
import redis
import socket
from scraper.search import websearch
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

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
        "consumer": consumer_id
    }
    if message:
        update_data["message"] = message
    
    redis_client.hset(f"pod:{pod_id}", mapping=update_data)
    
    # Send to SSE stream
    update = {
        "pod_id": pod_id,
        "status": status,
        "progress": progress
    }
    if message:
        update["message"] = message
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
        papers = scrape_arxiv(query, max_papers=3)
        logger.info(f"Scraped {len(papers)} results for pod {pod_id}")
        
        # Log the structure of the papers object ### Added by Jack to see the structure of the papers object
        logger.info(f"Papers type: {type(papers)}")
        if papers and len(papers) > 0:
            logger.info(f"Sample paper structure: {json.dumps(papers[0], indent=2, default=str)}")
            logger.info(f"Paper keys: {list(papers[0].keys()) if isinstance(papers[0], dict) else 'Not a dictionary'}")
        else:
            logger.info("No papers were returned from scraping")

        # Web Seach
        logger.info("Web searching...")
        ddg_results = websearch(query) # This returns as a list of dictionaries with title, url, and content

        
        send_progress_update(pod_id, "IN_PROGRESS", 66, "Adding papers/web search results to vector store")
        # Add papers to vector store
        rag_chain.add_papers(papers)
        logger.info(f"Added papers to vector store for pod {pod_id}")

        rag_chain.add_websearch(ddg_results)
        logger.info(f"Added web search results to vector store for pod {pod_id}")
        send_progress_update(pod_id, "IN_PROGRESS", 90, "Generating summary")
        # Generate summary
        summary = rag_chain.query(query)
        
        # Prepare response
        response = {
            "pod_id": pod_id,
            "query": query,
            "summary": summary
        }

        # Send response to Kafka for now and mark as complete
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
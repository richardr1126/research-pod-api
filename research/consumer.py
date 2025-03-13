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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Dictionary to store job progress
job_progress = {}
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

)

producer = KafkaProducer( # Producer to return research results
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def send_progress_update(job_id: str, status: str, progress: int, message: str = None):
    """Send a progress update to the SSE stream."""
    update = {
        "job_id": job_id,
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
        job_id = data.get('job_id')
        
        if not query:
            return
            
        # Initialize job progress
        job_progress[job_id] = {"status": "PROCESSING", "progress": 0}
        send_progress_update(job_id, "PROCESSING", 0, "Started processing request")
        
        logger.info(f"Processing scrape request for job {job_id}: {query}")
        
        # Scrape papers
        send_progress_update(job_id, "IN_PROGRESS", 33, "Scraping papers")
        papers = scrape_arxiv(query, max_papers=3)
        logger.info(f"Scraped {len(papers)} results for job {job_id}")


        # Web search
        
        #########################################################
        
        # Add papers to vector store
        send_progress_update(job_id, "IN_PROGRESS", 66, "Adding papers to vector store")
        rag_chain.add_papers(papers, job_id=job_id)
        logger.info(f"Added papers to vector store for job {job_id}")
        
        # Generate summary
        send_progress_update(job_id, "IN_PROGRESS", 90, "Generating summary")
        summary = rag_chain.query(query)
        
        # Prepare response
        response = {
            "job_id": job_id,
            "query": query,
            "summary": summary
        }
        
        # Send response and mark as complete
        producer.send('research-results', key=job_id.encode('utf-8'), value=response)
        producer.flush()
        send_progress_update(job_id, "COMPLETED", 100, "Processing complete")
        logger.info(f"Sent research results for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        error_response = {
            "job_id": job_id if 'job_id' in locals() else None,
            "query": query if 'query' in locals() else None,
            "error": str(e)
        }
        producer.send('research-errors', value=error_response)
        producer.flush()
        send_progress_update(job_id, "ERROR", 0, str(e))

@app.route('/health')
def health():
    """Health check endpoint."""
    try:
        # Check Kafka connection
        consumer.topics()
        #producer.flush()
        return jsonify({
            "status": "healthy",
            "kafka_connected": True
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "kafka_connected": False,
            "error": str(e)
        }), 503

@app.route('/events/<job_id>')
def events(job_id):
    """SSE endpoint for job progress updates."""
    def generate():
        while True:
            # Get progress update from queue
            try:
                update = progress_queue.get(timeout=30)  # 30 second timeout
                if update["job_id"] == job_id:
                    yield f"data: {json.dumps(update)}\n\n"
                    # If job is complete or errored, stop streaming
                    if update["status"] in ["COMPLETED", "ERROR"]:
                        break
                else:
                    # Put back updates for other jobs
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
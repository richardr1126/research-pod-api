from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import multiprocessing
import json
import uuid
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError
from dotenv import load_dotenv
import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
server = Flask(__name__)
CORS(server)

# Initialize Redis
redis_client = redis.Redis.from_url(
    os.getenv('REDIS_URL', 'redis://localhost:6379'),
    decode_responses=True
)

# Initialize Kafka producer with error handling
try:
    worker_pid = multiprocessing.current_process().pid
    client_id = f"web-api-producer-{worker_pid}"
    
    producer = KafkaProducer(
        bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        client_id=client_id,
        #security_protocol='SSL',
        #ssl_check_hostname=False,
        #ssl_certfile='certs/tls.crt',
        #ssl_keyfile='certs/tls.key',
        #ssl_cafile='certs/ca.crt',
        #ssl_password='kafka123',
        max_in_flight_requests_per_connection=1,  # Ensure ordering
    )
    logger.info(f"Successfully connected to Kafka at {os.getenv('KAFKA_BOOTSTRAP_SERVERS')}")
except Exception as e:
    logger.error(f"Failed to connect to Kafka: {str(e)}")
    producer = None

def get_consumer_url(job_id):
    """Get the consumer URL for a job."""
    # Check if we're running in Kubernetes
    if os.getenv('KUBERNETES_SERVICE_HOST'):
        # Get assigned consumer from Redis
        consumer_id = redis_client.hget(f"job:{job_id}", "consumer")
        if consumer_id:
            return f"https://research-consumer-{consumer_id}.richardr.dev"
        else:
            return None
    # Default to localhost for local development
    return "http://localhost:8081"

@server.route('/v1/api/scrape', methods=['POST'])
def scrape():
    try:
        if not producer:
            return jsonify({"error": "Kafka producer not initialized"}), 503

        body = request.get_json()
        if not body or 'query' not in body:
            return jsonify({"error": "Missing query in request body"}), 400
            
        job_id = str(uuid.uuid4())
        
        # Initialize job in Redis
        redis_client.hset(f"job:{job_id}",
            mapping={
                "status": "QUEUED",
                "progress": 0,
                "query": body['query']
            }
        )
        
        message = {
            "job_id": job_id,
            "query": body['query']
        }
        
        logger.info(f"Attempting to send message with job_id: {job_id}")
        
        # Send to Kafka...
        future = producer.send('scrape-requests', 
            key=job_id.encode('utf-8'), 
            value=message
        )
        
        try:
            record_metadata = future.get(timeout=5)
            logger.info(f"Message sent successfully - topic: {record_metadata.topic}, "
                       f"partition: {record_metadata.partition}, "
                       f"offset: {record_metadata.offset}")
        except KafkaError as e:
            logger.error(f"Failed to send message: {str(e)}")
            return jsonify({"error": f"Failed to send message: {str(e)}"}), 500
        
        return jsonify({
            "status": "success", 
            "message": "Scrape request queued",
            "job_id": job_id
        }), 202

    except Exception as e:
        logger.error(f"Error in scrape endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@server.route('/v1/api/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get job status and details."""
    try:
        job_data = redis_client.hgetall(f"job:{job_id}")
        if not job_data:
            return jsonify({"error": "Job not found"}), 404
        
        response = {
            "job_id": job_id,
            "status": job_data.get("status"),
            "progress": int(job_data.get("progress", 0)),
            "query": job_data.get("query")
        }
        
        # Get consumer URL
        consumer_url = get_consumer_url(job_id)
        if consumer_url:
            events_url = f"{consumer_url}/events/{job_id}"
            response["events_url"] = events_url
            
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Health check endpoint
@server.route('/health')
def health():
    """Simple health check endpoint."""
    status = {
        "status": "healthy",
        "redis": "healthy",
        "kafka_producer": "healthy"
    }
    
    # Check Redis connection
    try:
        redis_client.ping()
    except Exception as e:
        status["redis"] = "unhealthy"
        status["status"] = "degraded"
    
    # Check Kafka producer
    if not producer:
        status["kafka_producer"] = "unhealthy"
        status["status"] = "degraded"
    
    http_status = 200 if status["status"] == "healthy" else 503
    return jsonify(status), http_status
    
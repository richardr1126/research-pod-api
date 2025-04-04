from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import multiprocessing
import json
from uuid_v7.base import uuid7
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError
from dotenv import load_dotenv
import redis
from datetime import datetime, timezone
from db import db, ResearchPods

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
server = Flask(__name__)
CORS(server)

# Database Configuration
server.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', '')
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db.init_app(server)

def init_db():
    with server.app_context():
        db.create_all()

init_db()

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
        max_in_flight_requests_per_connection=1,  # Ensure ordering
        #security_protocol='SSL',
        #ssl_check_hostname=True,
        #ssl_cafile='/etc/kafka/certs/kafka-ca.crt',
    )
    logger.info(f"Successfully connected to Kafka at {os.getenv('KAFKA_BOOTSTRAP_SERVERS')}")
except Exception as e:
    logger.error(f"Failed to connect to Kafka: {str(e)}")
    producer = None

def get_events_url(pod_id):
    """Get the events URL for a pod."""
    # Check if we're running in Kubernetes
    if os.getenv('KUBERNETES_SERVICE_HOST'):
        # Get assigned consumer from Redis
        consumer_id = redis_client.hget(f"pod:{pod_id}", "consumer")
        if (consumer_id):
            return f"https://research-consumer-{consumer_id}.richardr.dev/v1/events/{pod_id}"
        else:
            return None
    # Default to localhost:8081 for local development
    # Check redis for consumer assignment
    consumer_id = redis_client.hget(f"pod:{pod_id}", "consumer")
    if consumer_id:
        return f"http://localhost:8081/v1/events/{pod_id}"
    return None

@server.route('/v1/api/pod/create', methods=['POST'])
def scrape():
    try:
        if not producer:
            return jsonify({"error": "Kafka producer not initialized"}), 503

        body = request.get_json()
        if not body or 'query' not in body:
            return jsonify({"error": "Missing query in request body"}), 400
            
        # Create ResearchPod entry
        research_pod = ResearchPods.create_from_request(
            query=body['query']
        )
        db.session.add(research_pod)
        db.session.commit()
        
        # Initialize pod in Redis
        redis_client.hset(f"pod:{research_pod.id}",
            mapping={
                "status": "QUEUED",
                "progress": 0,
                "query": body['query']
            }
        )
        
        message = {
            "pod_id": research_pod.id,
            "query": body['query']
        }
        
        logger.info(f"Attempting to send message with pod_id: {research_pod.id}")
        
        # Send to Kafka...
        future = producer.send('scrape-requests', 
            key=str(research_pod.id).encode('utf-8'), 
            value=message
        )
        
        try:
            record_metadata = future.get(timeout=5)
            logger.info(f"Message sent successfully - topic: {record_metadata.topic}, "
                       f"partition: {record_metadata.partition}, "
                       f"offset: {record_metadata.offset}")
        except KafkaError as e:
            logger.error(f"Failed to send message: {str(e)}")
            db.session.delete(research_pod)
            db.session.commit()
            return jsonify({"error": f"Failed to send message: {str(e)}"}), 500
        
        return jsonify({
            "pod_id": research_pod.id,
            "status": "success", 
            "message": "Scrape request queued",
            "events_url": None
        }), 202

    except Exception as e:
        logger.error(f"Error in scrape endpoint: {str(e)}")
        # Rollback any database changes if there was an error
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@server.route('/v1/api/pod/status/<pod_id>', methods=['GET'])
def get_status(pod_id):
    """Get pod status and details."""
    try:
        pod_data = redis_client.hgetall(f"pod:{pod_id}")
        if not pod_data:
            return jsonify({"error": "Pod not found"}), 404
        
        response = {
            "pod_id": pod_id,
            "status": pod_data.get("status"),
            "progress": int(pod_data.get("progress", 0)),
            "query": pod_data.get("query")
        }
        
        # Add message if it exists
        if "message" in pod_data:
            response["message"] = pod_data["message"]
        
        # Get consumer URL
        events_url = get_events_url(pod_id)
        if events_url:
            response["events_url"] = events_url
            
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting pod status: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@server.route('/v1/api/pod/get/<pod_id>', methods=['GET'])
def get_pod(pod_id):
    """Get research pod details from database."""
    research_pod = db.get_or_404(ResearchPods, pod_id)
    
    # Convert the ResearchPod to dictionary format
    response = research_pod.to_dict()
    
    return jsonify(response), 200

# Health check endpoint
@server.route('/health')
def health():
    """Health check endpoint with Redis, Kafka, and Database status."""
    status = {
        "status": "healthy",
        "redis": "healthy",
        "kafka_producer": "healthy",
        "database": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Check Redis connection
    try:
        redis_client.ping()
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        status["redis"] = "unhealthy"
        status["status"] = "degraded"
    
    # Check Kafka producer
    if not producer:
        status["kafka_producer"] = "unhealthy"
        status["status"] = "degraded"
    
    # Check database connection
    try:
        db.session.execute(db.select(1))
        db.session.commit()
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        status["database"] = "unhealthy"
        status["status"] = "degraded"
    
    http_status = 200 if status["status"] == "healthy" else 503
    return jsonify(status), http_status

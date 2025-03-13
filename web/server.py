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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
server = Flask(__name__)
CORS(server)

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
        #ssl_cafile='certs/ca.crt',  # Add this line
        #ssl_password='kafka123',
        max_in_flight_requests_per_connection=1,  # Ensure ordering
    )
    logger.info(f"Successfully connected to Kafka at {os.getenv('KAFKA_BOOTSTRAP_SERVERS')}")
except Exception as e:
    logger.error(f"Failed to connect to Kafka: {str(e)}")
    producer = None

@server.route('/v1/api/scrape', methods=['POST'])
def scrape():
    try:
        if not producer:
            return jsonify({"error": "Kafka producer not initialized"}), 503

        body = request.get_json()
        if not body or 'query' not in body:
            return jsonify({"error": "Missing query in request body"}), 400
            
        job_id = str(uuid.uuid4())
        message = {
            "job_id": job_id,
            "query": body['query']
        }
        
        logger.info(f"Attempting to send message with job_id: {job_id}")
        
        # Send message with future to check for errors
        future = producer.send(
            'scrape-requests', 
            key=job_id.encode('utf-8'), 
            value=message
        )
        
        # Wait for message to be delivered or timeout
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

# Example route
@server.route('/v1/api/hello', methods=['GET'])
def hello():
    message = "Hello from Flask!"
    return jsonify({"message": message})
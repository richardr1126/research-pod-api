from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
import uuid
from kafka import KafkaProducer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
server = Flask(__name__)
CORS(server)

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Basic health check endpoint
@server.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

# Scrape endpoint that produces to Kafka
@server.route('/v1/api/scrape', methods=['POST'])
def scrape():
    try:
        body = request.get_json()
        if not body or 'query' not in body:
            return jsonify({"error": "Missing query in request body"}), 400
            
        # Generate a job ID
        job_id = str(uuid.uuid4())
        
        # Add job ID to the message
        message = {
            "job_id": job_id,
            "query": body['query']
        }
            
        # Produce message to Kafka
        producer.send('scrape-requests', key=job_id.encode('utf-8'), value=message)
        producer.flush()
        
        return jsonify({
            "status": "success", 
            "message": "Scrape request queued",
            "job_id": job_id
        }), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Example route
@server.route('/v1/api/hello', methods=['GET'])
def hello():
    message = "Hello from Flask!"
    return jsonify({"message": message})
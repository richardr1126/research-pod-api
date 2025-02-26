from flask import Flask, jsonify
from flask_cors import CORS
import os

# Initialize Flask app
server = Flask(__name__)
CORS(server)

# Basic health check endpoint
@server.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

# Example route
@server.route('/v1/api/hello', methods=['GET'])
def hello():
    message = "Hello from Flask! On PORT: " + os.getenv('PORT')
    return jsonify({"message": message})
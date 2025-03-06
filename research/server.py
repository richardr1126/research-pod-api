from flask import Flask, jsonify, request
from flask_cors import CORS
import os

from dotenv import load_dotenv
from scraper.scrape import scrape_arxiv

# Load environment variables
load_dotenv()

# Initialize Flask app
server = Flask(__name__)
CORS(server)

# Basic health check endpoint
@server.route('/v1/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

# Scrape endpoint
@server.route('/v1/scrape', methods=['POST'])
def scrape():
    try:
        body = request.get_json()
        if not body:
            return jsonify({"error": "Missing data in request body"}), 400
            
        if 'query' not in body:
            return jsonify({"error": "Missing 'query' in request body"}), 400
            
        results = scrape_arxiv(body['query'], max_papers=3)
        
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
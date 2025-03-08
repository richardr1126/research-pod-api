from flask import Flask, jsonify, request
from flask_cors import CORS
import os

from dotenv import load_dotenv
from research.scraper.scrape import scrape_arxiv
from research.processor.summarize import process_papers
from research.websearch.search import websearch

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
    
# Websearch endpoint
@server.route('/v1/websearch', methods=['POST'])
def web_search_endpoint():
    try:
        body = request.get_json()
        if not body:
            return jsonify({"error": "Missing data in request body"}), 400
            
        if 'query' not in body:
            return jsonify({"error": "Missing 'query' in request body"}), 400
            
        results = websearch(body['query'])
        
        # Return results as a dictionary
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Process endpoint
@server.route('/v1/process', methods=['POST'])
def process():
    try:
        body = request.get_json()
        if not body:
            return jsonify({"error": "Missing data in request body"}), 400
            
        if 'papers' not in body:
            return jsonify({"error": "Missing 'papers' in request body"}), 400
            
        summary = process_papers(body['papers'])
        
        return jsonify({"summary": summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
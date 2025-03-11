from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import threading
import uuid
import time

from dotenv import load_dotenv
from research.scraper.scrape import scrape_arxiv
from research.processor.summarize import process_papers
from research.websearch.search import websearch
from research.websearch2.search import websearch_2
from research.research.research import research

# Load environment variables
load_dotenv()

# Initialize Flask app
server = Flask(__name__)
CORS(server)

# Store for background tasks
websearch_tasks = {}

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
        
        # Generate a task ID
        task_id = str(uuid.uuid4())
        
        # Initialize task status
        websearch_tasks[task_id] = {
            "status": "running",
            "query": body['query'],
            "results": None,
            "error": None,
            "created_at": time.time()
        }
        
        # Start background thread
        thread = threading.Thread(
            target=run_websearch_in_background,
            args=(task_id, body['query'])
        )
        thread.daemon = True
        thread.start()
        
        # Return task ID immediately
        return jsonify({
            "task_id": task_id,
            "status": "running",
            "message": "Websearch started in background"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Function to run websearch in background
def run_websearch_in_background(task_id, query):
    try:
        # Run the actual websearch
        results = websearch(query)
        
        # Update task with results
        websearch_tasks[task_id]["status"] = "completed"
        websearch_tasks[task_id]["results"] = results
    except Exception as e:
        # Update task with error
        websearch_tasks[task_id]["status"] = "failed"
        websearch_tasks[task_id]["error"] = str(e)

# Endpoint to check task status
@server.route('/v1/websearch/status/<task_id>', methods=['GET'])
def check_websearch_status(task_id):
    if task_id not in websearch_tasks:
        return jsonify({"error": "Task not found"}), 404
    
    task = websearch_tasks[task_id]
    
    # Clean up completed tasks older than 1 hour
    current_time = time.time()
    for tid in list(websearch_tasks.keys()):
        if websearch_tasks[tid]["status"] in ["completed", "failed"] and \
           current_time - websearch_tasks[tid]["created_at"] > 3600:
            del websearch_tasks[tid]
    
    # Return task status
    response = {
        "task_id": task_id,
        "status": task["status"],
        "query": task["query"]
    }
    
    if task["status"] == "completed":
        response["results"] = task["results"]
    elif task["status"] == "failed":
        response["error"] = task["error"]
    
    return jsonify(response)

# Process endpoint
@server.route('/v1/process', methods=['POST'])
def process():
    try:
        body = request.get_json()
        if not body:
            return jsonify({"error": "Missing data in request body"}), 400
            
        if 'papers' not in body:
            return jsonify({"error": "Missing 'papers' in request body"}), 400
            
        # summary = process_papers(body['papers'])
        summary = process_papers(body['papers'])
        
        return jsonify({"summary": summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# Endpoint for websearch2
@server.route('/v1/websearch2', methods=['POST'])
def websearch2():
    body = request.get_json()
    if not body:
        return jsonify({"error": "Missing data in request body"}), 400
    
    query = body['query']
    results = websearch_2(query)
    
    return jsonify({"results": results})


# Enpoint to do research
@server.route('/v1/research', methods=['POST'])
def research_endpoint():
    body = request.get_json()
    if not body:
        return jsonify({"error": "Missing data in request body"}), 400
    
    results = research(body['query'])
    return jsonify({"results": results})
from recommendation_system.recommender import get_recommendations

# Route 1: While typing
@app.route("/v1/api/pod/suggest", methods=["POST"])
def suggest():
    data = request.get_json()
    query = data.get("query", "")
    if not query:
        return jsonify({"error": "Missing query"}), 400
    suggestions = get_recommendations(query)
    return jsonify(suggestions)

# Route 2: After audio finishes
@app.route("/v1/api/pod/recommend", methods=["POST"])
def recommend():
    data = request.get_json()
    title = data.get("title", "")
    if not title:
        return jsonify({"error": "Missing title"}), 400
    recommendations = get_recommendations(title)
    return jsonify(recommendations)

from flask import Flask, request, jsonify
from config import config
from utils.logger import get_logger

logger = get_logger("main")

app = Flask(__name__)

@app.route("/")
def root():
    return jsonify({"system": "FINIX AI", "status": "online", "version": "0.1.0"})

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/api/query", methods=["POST"])
def query():
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "Missing query field"}), 400
    from schemas.messages import UserQuery
    from agents.finix import finix
    try:
        user_query = UserQuery(
            query=data["query"],
            user_id=data.get("user_id", "default_user"),
            context=data.get("context", {})
        )
        response = finix.handle(user_query)
        return jsonify(response)
    except Exception as e:
        logger.error(f"Query error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/account/preferences", methods=["PATCH"])
def update_preferences():
    data = request.get_json()
    user_id = request.args.get("user_id", "default_user")
    from agents.frank import frank
    frank.update_preferences(user_id, data)
    return jsonify({"status": "updated", "user_id": user_id})

@app.route("/api/account/watchlist", methods=["PATCH"])
def update_watchlist():
    data = request.get_json()
    user_id = request.args.get("user_id", "default_user")
    from agents.frank import frank
    frank.update_watchlist(user_id, add=data.get("add", []), remove=data.get("remove", []))
    return jsonify({"status": "updated", "user_id": user_id})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    logger.info("FINIX AI starting up...")
    app.run(host="0.0.0.0", port=port)

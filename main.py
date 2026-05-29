from flask import Flask, request, jsonify
from config import config
from utils.logger import get_logger

logger = get_logger("main")

app = Flask(__name__)

def get_current_user():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return None
    from auth.auth_service import auth_service
    result = auth_service.validate_token(token)
    if "error" in result:
        return None
    return result["user_id"]

@app.route("/")
def root():
    return jsonify({"system": "FINIX AI", "status": "online", "version": "0.2.0"})

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Username and password required"}), 400
    from auth.auth_service import auth_service
    result = auth_service.register(data["username"], data["password"])
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Username and password required"}), 400
    from auth.auth_service import auth_service
    result = auth_service.login(data["username"], data["password"])
    if "error" in result:
        return jsonify(result), 401
    return jsonify(result)

@app.route("/auth/logout", methods=["POST"])
def logout():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return jsonify({"error": "No token provided"}), 400
    from auth.auth_service import auth_service
    result = auth_service.logout(token)
    return jsonify(result)

@app.route("/admin/create-user", methods=["POST"])
def admin_create_user():
    admin_key = request.headers.get("X-Admin-Key", "")
    if admin_key != config.ADMIN_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Username and password required"}), 400
    from auth.auth_service import auth_service
    result = auth_service.admin_create_user(data["username"], data["password"])
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)

@app.route("/api/query", methods=["POST"])
def query():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized — please login first"}), 401
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "Missing query field"}), 400
    from schemas.messages import UserQuery
    from agents.finix import finix
    try:
        user_query = UserQuery(
            query=data["query"],
            user_id=user_id,
            context=data.get("context", {})
        )
        response = finix.handle(user_query)
        return jsonify(response)
    except Exception as e:
        logger.error(f"Query error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/frank/memory", methods=["GET"])
def view_memory():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    from agents.frank import frank
    data = frank.read_user_context(user_id)
    return jsonify(data)

@app.route("/api/account/preferences", methods=["PATCH"])
def update_preferences():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    from agents.frank import frank
    frank.update_preferences(user_id, data)
    return jsonify({"status": "updated"})

@app.route("/api/account/watchlist", methods=["PATCH"])
def update_watchlist():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    from agents.frank import frank
    frank.update_watchlist(user_id, add=data.get("add", []), remove=data.get("remove", []))
    return jsonify({"status": "updated"})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    logger.info("FINIX AI starting up...")
    app.run(host="0.0.0.0", port=port)

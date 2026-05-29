import bcrypt
import secrets
from memory.supabase_client import supabase_client
from utils.logger import get_logger
import uuid
from datetime import datetime, timedelta

logger = get_logger("auth_service")

class AuthService:
    def __init__(self):
        self.db = supabase_client.get()

    def register(self, username: str, password: str, user_type: str = "human", owner: str = None) -> dict:
        try:
            existing = self.db.table("users").select("user_id").eq("username", username).execute()
            if existing.data:
                return {"error": "Username already exists"}

            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            user_id = str(uuid.uuid4())

            self.db.table("users").insert({
                "user_id": user_id,
                "username": username,
                "password_hash": password_hash,
                "user_type": user_type,
                "owner": owner,
                "preferences": {},
                "watchlist": []
            }).execute()

            logger.info(f"New user registered: {username}")
            return {"success": True, "user_id": user_id, "username": username}

        except Exception as e:
            logger.error(f"Register error: {e}")
            return {"error": str(e)}

    def login(self, username: str, password: str) -> dict:
        try:
            result = self.db.table("users").select(
                "user_id, username, password_hash"
            ).eq("username", username).execute()

            if not result.data:
                return {"error": "Invalid username or password"}

            user = result.data[0]
            if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
                return {"error": "Invalid username or password"}

            token = secrets.token_urlsafe(32)
            expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()

            self.db.table("sessions").insert({
                "token": token,
                "user_id": user["user_id"],
                "expires_at": expires_at
            }).execute()

            logger.info(f"User logged in: {username}")
            return {
                "success": True,
                "token": token,
                "user_id": user["user_id"],
                "username": username
            }

        except Exception as e:
            logger.error(f"Login error: {e}")
            return {"error": str(e)}

    def validate_token(self, token: str) -> dict:
        try:
            result = self.db.table("sessions").select(
                "user_id, expires_at"
            ).eq("token", token).execute()

            if not result.data:
                return {"error": "Invalid token"}

            session = result.data[0]
            expires_at = datetime.fromisoformat(session["expires_at"])

            if datetime.utcnow() > expires_at:
                self.db.table("sessions").delete().eq("token", token).execute()
                return {"error": "Token expired"}

            return {"success": True, "user_id": session["user_id"]}

        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return {"error": str(e)}

    def logout(self, token: str) -> dict:
        try:
            self.db.table("sessions").delete().eq("token", token).execute()
            return {"success": True}
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return {"error": str(e)}

    def admin_create_user(self, username: str, password: str) -> dict:
        return self.register(username, password, user_type="human")

auth_service = AuthService()

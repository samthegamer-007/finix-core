from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import config
from agents.finix import finix
from schemas.messages import UserQuery, FinixResponse
from utils.logger import get_logger

logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("FINIX AI starting up...")
    try:
        config.validate()
        logger.info("Config validated ✓")
    except EnvironmentError as e:
        logger.warning(f"Config warning: {e}")
    logger.info("All agents initialized ✓")
    logger.info("FINIX AI is ready.")
    logger.info("=" * 50)
    yield
    logger.info("FINIX AI shutting down.")

app = FastAPI(
    title="FINIX AI",
    description="Multi-agent financial intelligence system",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"system": "FINIX AI", "status": "online", "version": "0.1.0"}

@app.get("/health")
def health():
    """UptimeRobot pings this endpoint to keep the server warm."""
    return {"status": "healthy"}

@app.post("/api/query", response_model=FinixResponse)
def query(payload: UserQuery):
    """Main FINIX AI query endpoint."""
    logger.info(f"Incoming query | user: {payload.user_id}")
    try:
        response = finix.handle(payload)
        return response
    except Exception as e:
        logger.error(f"Query handler error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/account/preferences")
def update_preferences(user_id: str, preferences: dict):
    from agents.frank import frank
    frank.update_preferences(user_id, preferences)
    return {"status": "updated", "user_id": user_id}

@app.patch("/api/account/watchlist")
def update_watchlist(user_id: str, add: list = [], remove: list = []):
    from agents.frank import frank
    frank.update_watchlist(user_id, add=add, remove=remove)
    return {"status": "updated", "user_id": user_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

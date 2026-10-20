import asyncio
import logging
from contextlib import asynccontextmanager

import jwt
import redis.asyncio as aioredis
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.config import settings
from app.redis_client import EVENTS_CHANNEL
from app.routers import alerts, auth, dashboard, demo, services
from app.security import decode_token
from app.services.ws_manager import manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("cloudpulse")


async def redis_event_listener() -> None:
    """Forward events published by Celery workers (via Redis pub/sub) to browser WebSockets."""
    while True:
        try:
            client = aioredis.from_url(settings.redis_url, decode_responses=True)
            pubsub = client.pubsub()
            await pubsub.subscribe(EVENTS_CHANNEL)
            logger.info("Subscribed to Redis channel %s", EVENTS_CHANNEL)
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await manager.broadcast(message["data"])
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("Redis listener error (%s); retrying in 3s", exc)
            await asyncio.sleep(3)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(redis_event_listener())
    yield
    task.cancel()


app = FastAPI(
    title="CloudPulse API",
    description="Distributed service monitoring with real-time updates, background checks and alerting.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (auth, services, alerts, dashboard, demo):
    app.include_router(module.router)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(_: Request, exc: IntegrityError):
    logger.warning("Integrity error: %s", exc)
    return JSONResponse(status_code=409, content={"detail": "This record conflicts with an existing one"})


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(_: Request, exc: SQLAlchemyError):
    logger.exception("Database error")
    return JSONResponse(status_code=500, content={"detail": "A database error occurred. Please try again."})


@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = ""):
    try:
        decode_token(token)
    except jwt.PyJWTError:
        await websocket.close(code=4401)
        return
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keeps the connection open; clients send nothing
    except WebSocketDisconnect:
        manager.disconnect(websocket)

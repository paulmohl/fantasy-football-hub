import sentry_sdk
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as v1_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.redis import close_redis, get_redis

configure_logging()

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.app_env)

# Socket.IO — Redis adapter for multi-instance fan-out
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[settings.frontend_url],
    logger=False,
    engineio_logger=False,
)


@sio.event
async def connect(sid: str, environ: dict, auth: dict | None = None) -> None:
    pass


@sio.event
async def disconnect(sid: str) -> None:
    pass


app = FastAPI(
    title="Fantasy Football Hub",
    version="0.1.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)


@app.on_event("startup")
async def startup() -> None:
    redis = await get_redis()
    mgr = socketio.AsyncRedisManager(settings.redis_url)
    sio.manager = mgr


@app.on_event("shutdown")
async def shutdown() -> None:
    await close_redis()


# Mount Socket.IO at /ws
combined_app = socketio.ASGIApp(sio, other_asgi_app=app, socketio_path="/ws")

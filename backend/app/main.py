import json

import sentry_sdk
import socketio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import router as v1_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.rate_limit import RateLimitedWithCache
from app.core.redis import close_redis, get_redis
from app.sockets.draft_namespace import DraftNamespace

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


# DR-07 / D-01 LOCKED: register /draft namespace before ASGIApp construction
sio.register_namespace(DraftNamespace('/draft'))

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

from starlette.middleware.sessions import SessionMiddleware  # noqa: E402
app.add_middleware(SessionMiddleware, secret_key=settings.app_secret_key)

app.include_router(v1_router)


@app.exception_handler(RateLimitedWithCache)
async def rate_limited_cache_handler(request: Request, exc: RateLimitedWithCache) -> JSONResponse:
    """MP-07: Serve cached data with X-Rate-Limited header when rate limit is hit."""
    return JSONResponse(
        content=json.loads(exc.cached_data),
        headers={"X-Rate-Limited": "true"},
        status_code=200,
    )


@app.on_event("startup")
async def startup() -> None:
    await get_redis()
    mgr = socketio.AsyncRedisManager(settings.redis_url)
    sio.manager = mgr


@app.on_event("shutdown")
async def shutdown() -> None:
    await close_redis()


# Mount Socket.IO at /ws
combined_app = socketio.ASGIApp(sio, other_asgi_app=app, socketio_path="/ws")

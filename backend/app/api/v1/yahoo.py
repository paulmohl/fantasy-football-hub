"""Yahoo Fantasy Sports routes — league listing and import."""
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import check_platform_rate_limit
from app.core.redis import get_redis
from app.models.user import User
from app.services.credential_service import CredentialService
from app.services.yahoo_client import YahooAuthExpired, YahooClient
from app.services.yahoo_service import import_yahoo_league

router = APIRouter(prefix="/yahoo", tags=["yahoo"])


async def _get_yahoo_client_for_user(
    user: User, db: AsyncSession
) -> tuple[YahooClient, str, httpx.AsyncClient]:
    """Retrieve stored Yahoo credential, refresh if expired, return YahooClient + game_key."""
    cred_svc = CredentialService()
    cred = await cred_svc.get_credential(user, "yahoo", db)
    if not cred:
        raise HTTPException(
            status_code=401,
            detail="Yahoo account not connected. Please authorize via /auth/yahoo.",
        )

    http = httpx.AsyncClient(timeout=15.0)
    expires_at = cred.get("expires_at", 0)
    if expires_at and time.time() > expires_at - 300:
        try:
            new_tokens = await YahooClient.refresh_access_token(http, cred["refresh_token"])
            cred.update({
                "access_token": new_tokens["access_token"],
                "refresh_token": new_tokens.get("refresh_token", cred["refresh_token"]),
                "expires_at": new_tokens.get("expires_at", 0),
            })
            async with db.begin_nested():
                await cred_svc.store_credential(user, "yahoo", cred, db)
        except YahooAuthExpired:
            async with db.begin_nested():
                await cred_svc.mark_unhealthy(user.id, "yahoo", db)
            raise HTTPException(
                status_code=401,
                detail="Yahoo credentials expired. Please reconnect at /auth/yahoo.",
            )

    yahoo = YahooClient(http, cred["access_token"])
    game_key = await yahoo.get_game_key()
    return yahoo, game_key, http


@router.get("/leagues")
async def list_yahoo_leagues(
    _: None = Depends(check_platform_rate_limit("yahoo")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """MP-01: Return list of user's Yahoo NFL leagues for multi-select import."""
    yahoo, game_key, http = await _get_yahoo_client_for_user(current_user, db)
    try:
        leagues = await yahoo.get_user_leagues()
    except YahooAuthExpired:
        raise HTTPException(
            status_code=401,
            detail="Yahoo credentials expired. Reconnect via /auth/yahoo.",
        )
    finally:
        await http.aclose()
    return {"leagues": leagues, "game_key": game_key}


class YahooImportRequest(BaseModel):
    league_ids: list[str]
    game_key: str


@router.post("/import")
async def import_yahoo_leagues(
    body: YahooImportRequest,
    _: None = Depends(check_platform_rate_limit("yahoo")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """MP-02: Import one or more Yahoo leagues into unified data model."""
    if not body.league_ids:
        raise HTTPException(status_code=422, detail="Select at least one league.")

    yahoo, _, http = await _get_yahoo_client_for_user(current_user, db)
    results, errors = [], []
    try:
        for league_id in body.league_ids:
            try:
                league = await import_yahoo_league(
                    league_id, body.game_key, current_user, db, redis, yahoo
                )
                results.append({"id": str(league.id), "name": league.name, "platform": "yahoo"})
            except Exception as e:
                errors.append({"league_id": league_id, "error": str(e)})
    finally:
        await http.aclose()

    if errors and not results:
        raise HTTPException(status_code=502, detail=f"Import failed: {errors[0]['error']}")
    return {"imported": results, "errors": errors}

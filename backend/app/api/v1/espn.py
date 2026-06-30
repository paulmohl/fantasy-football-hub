"""ESPN Fantasy Football routes — private cookie connect, public league connect, and import."""
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import check_platform_rate_limit
from app.core.redis import get_redis
from app.models.user import User
from app.services.credential_service import CredentialService
from app.services.espn_client import ESPNAuthExpired, ESPNClient, ESPNLeagueNotFound
from app.services.espn_service import import_espn_league

router = APIRouter(prefix="/espn", tags=["espn"])


class ESPNConnectRequest(BaseModel):
    swid: str
    espn_s2: str
    league_id: str


class ESPNPublicRequest(BaseModel):
    league_id: str


@router.post("/connect")
async def espn_connect_private(
    body: ESPNConnectRequest,
    _: None = Depends(check_platform_rate_limit("espn")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """MP-03: Validate ESPN cookies against live API, store encrypted, import league."""
    async with httpx.AsyncClient(timeout=15.0) as http:
        espn = ESPNClient(http, swid=body.swid, espn_s2=body.espn_s2)
        try:
            await espn.get_league(body.league_id, settings.nfl_season_year)
        except ESPNAuthExpired:
            raise HTTPException(
                status_code=401,
                detail=(
                    "ESPN cookies are expired or invalid. "
                    "Re-export SWID and espn_s2 from your browser and try again."
                ),
            )
        except ESPNLeagueNotFound:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"ESPN league {body.league_id} not found. "
                    "Check the league ID and ensure you are a member."
                ),
            )

        cred_svc = CredentialService()
        credential_dict = {"swid": body.swid, "espn_s2": body.espn_s2, "is_public": False}
        async with db.begin_nested():
            await cred_svc.store_credential(current_user, "espn", credential_dict, db)

        league = await import_espn_league(
            body.league_id,
            settings.nfl_season_year,
            is_public=False,
            current_user=current_user,
            db=db,
            redis=redis,
            espn=espn,
        )
    return {"id": str(league.id), "name": league.name, "platform": "espn", "is_public": False}


@router.post("/public")
async def espn_connect_public(
    body: ESPNPublicRequest,
    _: None = Depends(check_platform_rate_limit("espn")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """MP-04: Import a public ESPN league (no cookies required); mark read-only."""
    async with httpx.AsyncClient(timeout=15.0) as http:
        espn = ESPNClient(http)
        try:
            await espn.get_league(body.league_id, settings.nfl_season_year)
        except ESPNAuthExpired:
            raise HTTPException(
                status_code=403,
                detail="This ESPN league requires cookies to access. Use /espn/connect instead.",
            )
        except ESPNLeagueNotFound:
            raise HTTPException(
                status_code=404,
                detail=f"ESPN league {body.league_id} not found. Verify the league ID.",
            )

        cred_svc = CredentialService()
        credential_dict = {"league_id": body.league_id, "is_public": True}
        async with db.begin_nested():
            await cred_svc.store_credential(current_user, "espn", credential_dict, db)

        league = await import_espn_league(
            body.league_id,
            settings.nfl_season_year,
            is_public=True,
            current_user=current_user,
            db=db,
            redis=redis,
            espn=espn,
        )
    return {"id": str(league.id), "name": league.name, "platform": "espn", "is_public": True}

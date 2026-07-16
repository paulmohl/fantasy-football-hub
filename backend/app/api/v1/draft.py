"""Draft REST API — schedule, manage, and recap snake drafts.

DR-01: POST /drafts — commissioner creates draft, sends ICS invites
DR-02: PUT /drafts/{id}/order — update/lock draft order
DR-03: POST /drafts/{id}/rankings — import custom rankings (CSV)
DR-14: GET /drafts/{id}/recap — trigger/get post-draft grades
"""
import json
import time
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheKey
from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, get_draft_for_user
from app.core.redis import get_redis
from app.models.draft import Draft, DraftPick
from app.models.league import League, LeagueMember, Team
from app.models.user import User
from app.services.draft_service import (
    build_draft_ics,
    compute_adp_grades,
    import_csv_rankings,
    record_draft_event,
)

router = APIRouter(prefix="/drafts", tags=["drafts"])


class CreateDraftRequest(BaseModel):
    league_id: UUID
    pick_clock_seconds: int = 90
    num_rounds: int = 15
    scheduled_at: str | None = None  # ISO8601 string
    timezone: str = "America/New_York"
    draft_order_method: str = "randomize"  # randomize|manual|import


class UpdateOrderRequest(BaseModel):
    draft_order: list[str]  # list of team_id strings in pick order
    lock_and_start: bool = False


@router.post("", status_code=201)
async def create_draft(
    body: CreateDraftRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    """DR-01: Commissioner creates a draft and ICS invites are sent to all members."""
    # T-4-04: Verify commissioner role before creating draft
    member_result = await db.execute(
        select(LeagueMember).where(
            LeagueMember.league_id == body.league_id,
            LeagueMember.user_id == current_user.id,
        )
    )
    member = member_result.scalar_one_or_none()
    if not member or member.role not in ("commissioner", "owner"):
        raise HTTPException(status_code=403, detail="Commissioner role required")

    # Load league
    league_result = await db.execute(select(League).where(League.id == body.league_id))
    league = league_result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    # Parse scheduled_at
    from datetime import datetime
    scheduled_at = None
    if body.scheduled_at:
        try:
            scheduled_at = datetime.fromisoformat(body.scheduled_at.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid scheduled_at format")

    async with db.begin_nested():
        draft = Draft(
            league_id=body.league_id,
            commissioner_user_id=current_user.id,
            pick_clock_seconds=body.pick_clock_seconds,
            num_rounds=body.num_rounds,
            scheduled_at=scheduled_at,
            timezone=body.timezone,
            status="pending",
            num_teams=12,  # League model doesn't store num_teams; default 12 per D-12
        )
        db.add(draft)
        await db.flush()
        draft_id = str(draft.id)

    await db.commit()

    # In-app notification for all league members (DR-01)
    background_tasks.add_task(
        _push_draft_notifications,
        draft_id=draft_id,
        league_id=str(body.league_id),
        league_name=league.name,
    )

    # Send ICS invites in background (non-blocking)
    background_tasks.add_task(
        _send_draft_invites,
        draft_id=draft_id,
        draft_name=f"{league.name} Draft",
        scheduled_at=scheduled_at,
        timezone_str=body.timezone,
        num_teams=12,
        clock_seconds=body.pick_clock_seconds,
        num_rounds=body.num_rounds,
        league_id=str(body.league_id),
    )

    return {"id": draft_id, "status": "pending", "league_id": str(body.league_id)}


# NOTE: /league/{league_id} is registered BEFORE /{draft_id} to prevent FastAPI from
# matching the literal "league" path segment as a UUID draft_id (would cause 422).
@router.get("/league/{league_id}")
async def list_drafts_for_league(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all drafts for a league the current user is a member of (most recent first)."""
    result = await db.execute(
        select(Draft)
        .join(LeagueMember, LeagueMember.league_id == Draft.league_id)
        .where(LeagueMember.user_id == current_user.id, Draft.league_id == league_id)
        .order_by(Draft.created_at.desc())
    )
    return [
        {
            "id": str(d.id),
            "status": d.status,
            "scheduled_at": d.scheduled_at.isoformat() if d.scheduled_at else None,
        }
        for d in result.scalars()
    ]


@router.get("/{draft_id}")
async def get_draft(
    draft=Depends(get_draft_for_user),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get draft details including current status, order, and pick count."""
    picks_result = await db.execute(
        select(DraftPick).where(DraftPick.draft_id == draft.id).order_by(DraftPick.pick_num)
    )
    picks = [
        {
            "pick_num": p.pick_num,
            "round": p.round,
            "player_id": p.player_id,
            "team_id": str(p.team_id),
            "is_auto_pick": p.is_auto_pick,
            "reactions": p.reactions,
        }
        for p in picks_result.scalars()
    ]

    team_result = await db.execute(
        select(Team).where(
            Team.league_id == draft.league_id,
            Team.owner_user_id == current_user.id,
        )
    )
    my_team = team_result.scalar_one_or_none()
    my_team_id = str(my_team.id) if my_team else ""

    return {
        "id": str(draft.id),
        "status": draft.status,
        "pick_clock_seconds": draft.pick_clock_seconds,
        "num_rounds": draft.num_rounds,
        "num_teams": draft.num_teams,
        "current_pick_num": draft.current_pick_num,
        "scheduled_at": draft.scheduled_at.isoformat() if draft.scheduled_at else None,
        "timezone": draft.timezone,
        "draft_order": draft.draft_order,
        "picks": picks,
        "my_team_id": my_team_id,
        "commissioner_user_id": str(draft.commissioner_user_id),
    }


@router.get("/{draft_id}/recap")
async def get_recap(
    draft=Depends(get_draft_for_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    """DR-14: Return post-draft grade data (computed after last pick)."""
    if draft.status != "complete":
        raise HTTPException(status_code=400, detail="Draft not yet complete")

    picks_result = await db.execute(
        select(DraftPick).where(DraftPick.draft_id == draft.id).order_by(DraftPick.pick_num)
    )
    all_picks = list(picks_result.scalars())

    # Group picks by team
    picks_by_team: dict[str, list[dict]] = {}
    for pick in all_picks:
        tid = str(pick.team_id)
        if tid not in picks_by_team:
            picks_by_team[tid] = []
        picks_by_team[tid].append({"player_id": pick.player_id, "pick_num": pick.pick_num})

    # Use FantasyCalc overallRank as ADP lookup
    adp_lookup: dict[str, float] = {}
    adp_raw = await redis.get(CacheKey.fantasycalc_values(False))
    if adp_raw:
        try:
            fc_data = json.loads(adp_raw.decode() if isinstance(adp_raw, bytes) else adp_raw)
            for entry in fc_data:
                pid = str(
                    entry.get("player", {}).get("sleeperId", "")
                    or entry.get("sleeperId", "")
                )
                rank = entry.get("overallRank", 9999)
                if pid:
                    adp_lookup[pid] = float(rank)
        except Exception:
            pass

    grades = compute_adp_grades(picks_by_team, adp_lookup)

    pick_list = [
        {
            "pick_num": p.pick_num,
            "round": p.round,
            "player_id": p.player_id,
            "team_id": str(p.team_id),
            "is_auto_pick": p.is_auto_pick,
        }
        for p in all_picks
    ]

    # D-13 LOCKED: value picks (taken >2 rounds later than ADP); reaches (taken >2 rounds earlier)
    round_pick_threshold = draft.num_teams * 2
    value_picks = [
        p for p in all_picks
        if adp_lookup.get(p.player_id, p.pick_num) - p.pick_num > round_pick_threshold
    ]
    reaches = [
        p for p in all_picks
        if p.pick_num - adp_lookup.get(p.player_id, p.pick_num) > round_pick_threshold
    ]

    return {
        "draft_id": str(draft.id),
        "grades": grades,
        "picks": pick_list,
        "value_picks": [
            {
                "pick_num": p.pick_num,
                "round": p.round,
                "player_id": p.player_id,
                "team_id": str(p.team_id),
                "is_auto_pick": p.is_auto_pick,
            }
            for p in value_picks
        ],
        "reaches": [
            {
                "pick_num": p.pick_num,
                "round": p.round,
                "player_id": p.player_id,
                "team_id": str(p.team_id),
                "is_auto_pick": p.is_auto_pick,
            }
            for p in reaches
        ],
    }


@router.get("/{draft_id}/players")
async def get_draft_players(
    draft=Depends(get_draft_for_user),
    redis: Redis = Depends(get_redis),
) -> list[dict]:
    """Return enriched player data for BestAvailable panel.

    Joins Sleeper player pool (names, positions, teams) with FantasyCalc
    redraft rankings (overall_rank). Returns only active draftable positions
    sorted by overall_rank ascending (lower = better).

    SC-3: Called by DraftPage on mount to populate availablePlayers in store.
    """
    sleeper_raw = await redis.get(CacheKey.sleeper_players_nfl())
    sleeper_players: dict = {}
    if sleeper_raw:
        try:
            sleeper_players = json.loads(
                sleeper_raw.decode() if isinstance(sleeper_raw, bytes) else sleeper_raw
            )
        except Exception:
            pass

    fc_raw = await redis.get(CacheKey.fantasycalc_values(False))
    fc_rank: dict[str, int] = {}
    if fc_raw:
        try:
            fc_data = json.loads(
                fc_raw.decode() if isinstance(fc_raw, bytes) else fc_raw
            )
            for entry in fc_data:
                pid = str(
                    entry.get("player", {}).get("sleeperId", "")
                    or entry.get("sleeperId", "")
                )
                if pid:
                    fc_rank[pid] = int(entry.get("overallRank", 9999))
        except Exception:
            pass

    DRAFTABLE = {"QB", "RB", "WR", "TE", "K", "DEF"}
    players = []
    for pid, p in sleeper_players.items():
        if p.get("position") not in DRAFTABLE:
            continue
        if not p.get("active", False):
            continue
        first = p.get("first_name", "")
        last = p.get("last_name", "")
        name = f"{first} {last}".strip() if first or last else p.get("full_name", pid)
        overall_rank = fc_rank.get(pid, 9999)
        players.append({
            "player_id": pid,
            "name": name,
            "position": p.get("position", ""),
            "nfl_team": p.get("team", "FA"),
            "bye_week": p.get("bye_week"),
            "overall_rank": overall_rank,
        })

    players.sort(key=lambda x: x["overall_rank"])

    return players


@router.put("/{draft_id}/order")
async def update_draft_order(
    body: UpdateOrderRequest,
    draft=Depends(get_draft_for_user),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    """DR-02: Commissioner sets draft order; optional lock-and-start.

    W4/OQ1: Import-from-host mode (draft_order_method='import') is deferred to post-Phase-4.
    PreDraftLobby.tsx must render a DISABLED button with tooltip:
      'Import draft order from [Platform] — coming in a future update'
    Backend accepts the method value but treats it identically to 'manual'.
    This is the stub per B7/OQ1 resolution.
    """
    if str(draft.commissioner_user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Commissioner only")
    if draft.status not in ("pending",):
        raise HTTPException(status_code=400, detail="Can only set order before draft starts")

    async with db.begin_nested():
        draft.draft_order = body.draft_order
        if body.lock_and_start:
            draft.status = "live"
            draft.current_pick_num = 0
            # Set first pick deadline
            deadline = time.time() + draft.pick_clock_seconds
            await redis.set(
                CacheKey.draft_deadline(str(draft.id)),
                str(deadline),
                ex=draft.pick_clock_seconds + 30,
            )
            await redis.set(CacheKey.draft_state(str(draft.id)), "live")
            await record_draft_event(redis, str(draft.id), "draft_started", {
                "pick_num": "1",
                "deadline": str(deadline),
            })
            # Initialize available player SET (B6/OQ3): draftable positions QB/RB/WR/TE/K/DEF
            # Check Redis cache first; fall back to direct Sleeper API call via httpx
            import httpx as _httpx
            draft_id_str = str(draft.id)
            sleeper_raw = await redis.get(CacheKey.sleeper_players_nfl())
            if sleeper_raw:
                all_players: dict = json.loads(
                    sleeper_raw.decode() if isinstance(sleeper_raw, bytes) else sleeper_raw
                )
            else:
                async with _httpx.AsyncClient(timeout=20.0) as http:
                    r = await http.get(f"{settings.sleeper_api_base}/players/nfl")
                    all_players = r.json() if r.status_code == 200 else {}
            draftable = [
                pid for pid, p in all_players.items()
                if p.get("position") in {"QB", "RB", "WR", "TE", "K", "DEF"}
                and p.get("active", False)
            ]
            await redis.delete(CacheKey.draft_available(draft_id_str))
            if draftable:
                await redis.sadd(CacheKey.draft_available(draft_id_str), *draftable)
        await db.flush()
    await db.commit()

    return {"ok": True, "status": draft.status, "draft_order": draft.draft_order}


@router.post("/{draft_id}/rankings")
async def import_rankings(
    draft=Depends(get_draft_for_user),
    current_user: User = Depends(get_current_user),
    file: UploadFile | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """DR-03: Import custom CSV rankings for the current user."""
    if not file:
        raise HTTPException(status_code=422, detail="CSV file required")
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=422, detail="Must be a .csv file")

    content = await file.read()
    try:
        csv_text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=422, detail="CSV must be UTF-8 encoded")

    rows = await import_csv_rankings(csv_text, draft.id, current_user.id, db)
    return {"ok": True, "imported": len(rows)}


async def _send_draft_invites(
    draft_id: str,
    draft_name: str,
    scheduled_at,
    timezone_str: str,
    num_teams: int,
    clock_seconds: int,
    num_rounds: int,
    league_id: str,
) -> None:
    """Background: generate ICS and email all league members (DR-01)."""
    if not scheduled_at:
        return
    try:
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

        engine = create_async_engine(settings.database_url)
        SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with SessionLocal() as db:
            members_result = await db.execute(
                select(LeagueMember).where(LeagueMember.league_id == UUID(league_id))
            )
            user_ids = [m.user_id for m in members_result.scalars()]
            users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
            users = list(users_result.scalars())
        await engine.dispose()

        ics_bytes = build_draft_ics(
            draft_name=draft_name,
            scheduled_at=scheduled_at,
            timezone_str=timezone_str,
            num_teams=num_teams,
            clock_seconds=clock_seconds,
            num_rounds=num_rounds,
        )

        from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
        conf = ConnectionConfig(
            MAIL_USERNAME=settings.mail_username,
            MAIL_PASSWORD=settings.mail_password,
            MAIL_FROM=settings.mail_from,
            MAIL_PORT=settings.mail_port,
            MAIL_SERVER=settings.mail_server,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
        )
        fm = FastMail(conf)
        for user in users:
            if not user.email:
                continue
            msg = MessageSchema(
                subject=f"You're invited: {draft_name}",
                recipients=[user.email],
                body=(
                    f"Your fantasy draft is scheduled. "
                    f"See attachment for calendar invite.\n\nDraft: {draft_name}"
                ),
                subtype=MessageType.plain,
                attachments=[{
                    "file": ics_bytes,
                    "filename": "draft_invite.ics",
                    "mime_type": "text/calendar",
                }],
            )
            await fm.send_message(msg)

    except Exception as exc:
        from app.core.logging import logger
        logger.error("draft.invite.send_failed", draft_id=draft_id, error=str(exc))


async def _push_draft_notifications(
    draft_id: str,
    league_id: str,
    league_name: str,
) -> None:
    """Push in-app notification to all league members when draft is scheduled (DR-01)."""
    import json
    from datetime import UTC as _UTC, datetime
    from uuid import UUID

    try:
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

        engine = create_async_engine(settings.database_url)
        SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with SessionLocal() as db:
            members_result = await db.execute(
                select(LeagueMember).where(LeagueMember.league_id == UUID(league_id))
            )
            user_ids = [str(m.user_id) for m in members_result.scalars()]
        await engine.dispose()

        from app.core.redis import get_redis as _get_redis
        redis = await _get_redis()

        notification = json.dumps({
            "type": "draft_scheduled",
            "draft_id": draft_id,
            "league_name": league_name,
            "message": f"A draft has been scheduled for {league_name}",
            "created_at": datetime.now(_UTC).isoformat(),
        })

        for uid in user_ids:
            key = f"notifications:{uid}"
            await redis.rpush(key, notification)
            await redis.expire(key, 604800)  # 7 days

    except Exception as exc:
        from app.core.logging import logger
        logger.error("draft.notification.push_failed", draft_id=draft_id, error=str(exc))

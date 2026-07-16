"""Draft service: pure business logic for Phase 4 snake draft.

CRITICAL ORDERING RULE: Validate player availability in Redis (SISMEMBER) BEFORE
opening the DB transaction for DraftPick insert. If Redis and DB diverge, Redis wins
for availability checks — the DB UniqueConstraint is the final guard.
"""
import csv
import io
import time
from datetime import datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheKey
from app.core.logging import logger
from app.models.draft import UserDraftRanking


def snake_pick_to_slot(pick_num: int, num_teams: int) -> tuple[int, int]:
    """Return (round_num, team_slot_0indexed) for pick_num (1-indexed).

    Odd rounds go left-to-right (slot 0 to N-1).
    Even rounds go right-to-left (slot N-1 to 0) — the snake.
    """
    round_num = (pick_num - 1) // num_teams + 1
    pos_in_round = (pick_num - 1) % num_teams
    if round_num % 2 == 1:  # odd: left-to-right
        team_slot = pos_in_round
    else:                   # even: right-to-left (snake back)
        team_slot = num_teams - 1 - pos_in_round
    return round_num, team_slot


def build_draft_ics(
    draft_name: str,
    scheduled_at: datetime,
    timezone_str: str,
    num_teams: int,
    clock_seconds: int,
    num_rounds: int = 15,
) -> bytes:
    """Generate RFC 5545-compliant ICS bytes for a draft calendar invite."""
    tz = ZoneInfo(timezone_str)
    start = scheduled_at.replace(tzinfo=tz) if scheduled_at.tzinfo is None else scheduled_at
    estimated_seconds = num_teams * num_rounds * clock_seconds
    duration = timedelta(seconds=max(7200, estimated_seconds))
    event = Event.new(
        summary=f"Fantasy Draft: {draft_name}",
        start=start,
        end=start + duration,
        location="Fantasy Football Hub",
        description="Draft room opens 15 minutes before scheduled start.",
    )
    cal = Calendar.new(subcomponents=[event])
    cal.add_missing_timezones()
    return cal.to_ical()


def compute_tier_boundaries(players: list[dict], threshold: int = 15) -> list[int]:
    """Return 0-indexed positions in players list where a new tier begins.

    A tier break occurs when the rank delta between consecutive players exceeds threshold.
    Example: players[2].overall_rank=3, players[3].overall_rank=20 → delta=17 → boundary at index 3.
    """
    boundaries: list[int] = []
    for i in range(1, len(players)):
        prev_rank = players[i - 1].get("overall_rank", i)
        curr_rank = players[i].get("overall_rank", i + 1)
        if (curr_rank - prev_rank) > threshold:
            boundaries.append(i)
    return boundaries


def positional_need_bonus(
    drafted_positions: list[str],
    position: str,
    roster_format: dict,
) -> float:
    """Return a bonus score biasing auto-draft toward unfilled starting slots.

    Each unfilled starter slot earns 5.0 rank positions of bonus.
    drafted_positions: list of position strings already on the team (e.g. ["QB", "RB", "WR"]).
    roster_format: dict mapping position -> {"slots": N}.
    """
    pos_count = sum(1 for p in drafted_positions if p == position)
    starter_slots = roster_format.get(position, {}).get("slots", 0)
    unfilled = max(0, starter_slots - pos_count)
    return float(unfilled * 5.0)


def compute_adp_grades(
    picks_by_team: dict[str, list[dict]],
    adp_lookup: dict[str, float],
) -> dict[str, str]:
    """Assign letter grade A+/A/B/C/D/F to each team based on ADP value over expected.

    Positive delta = picked better than ADP (value steal).
    Negative delta = overdrafted (reach).
    Grade is assigned by percentile rank within this draft.
    """
    team_scores: dict[str, float] = {}
    for team_id, picks in picks_by_team.items():
        total = sum(
            adp_lookup.get(p["player_id"], float(p["pick_num"])) - p["pick_num"]
            for p in picks
        )
        team_scores[team_id] = total

    if not team_scores:
        return {}

    sorted_scores = sorted(team_scores.values(), reverse=True)
    n = len(sorted_scores)

    def to_grade(score: float) -> str:
        rank = sorted_scores.index(score)
        pct = rank / n
        if pct < 0.15:
            return "A+"
        if pct < 0.30:
            return "A"
        if pct < 0.45:
            return "B"
        if pct < 0.60:
            return "C"
        if pct < 0.80:
            return "D"
        return "F"

    return {team_id: to_grade(score) for team_id, score in team_scores.items()}


async def record_draft_event(
    redis: Redis,
    draft_id: str,
    event_type: str,
    fields: dict,
) -> str:
    """Write a draft event to the Redis Stream. Returns the event ID (bytes decoded to str).

    Uses MAXLEN ~ 5000 (approximate) to cap stream size.
    All values must be strings — encode before calling.
    """
    stream_key = CacheKey.draft_events_stream(draft_id)
    payload: dict[str, str] = {"type": event_type, "ts": str(time.time())}
    payload.update({k: str(v) for k, v in fields.items()})
    event_id = await redis.xadd(stream_key, payload, maxlen=5000, approximate=True)
    return event_id.decode() if isinstance(event_id, bytes) else str(event_id)


async def replay_since(
    redis: Redis,
    draft_id: str,
    last_event_id: str,
) -> list[tuple[str, dict]]:
    """Return all stream events after last_event_id (EXCLUSIVE lower bound).

    Uses '(' prefix for exclusive boundary — avoids re-delivering the boundary event.
    Returns list of (event_id_str, fields_dict) tuples with string keys/values.
    """
    stream_key = CacheKey.draft_events_stream(draft_id)
    exclusive_start = f"({last_event_id}"
    raw_events = await redis.xrange(stream_key, min=exclusive_start, max="+")
    result: list[tuple[str, dict]] = []
    for event_id, fields in raw_events:
        eid = event_id.decode() if isinstance(event_id, bytes) else str(event_id)
        decoded = {
            (k.decode() if isinstance(k, bytes) else k): (v.decode() if isinstance(v, bytes) else v)
            for k, v in fields.items()
        }
        result.append((eid, decoded))
    return result


async def select_auto_draft_player(
    redis: Redis,
    draft_id: str,
    user_queue: list[str],
    adp_ranked_players: list[dict],
    team_positions: list[str],
    roster_format: dict,
) -> str | None:
    """Select the best available player for auto-draft.

    Priority:
    1. First available player in user_queue (if queue non-empty)
    2. Highest-scoring player by ADP rank + positional need bonus

    adp_ranked_players: list of dicts sorted by overall_rank ascending,
        each with keys: player_id, overall_rank, position
    team_positions: list of positions already drafted by this team (e.g. ["QB", "RB"])
    roster_format: {position: {"slots": N}}
    """
    available_key = CacheKey.draft_available(draft_id)

    # Priority 1: personal queue
    for player_id in user_queue:
        is_available = await redis.sismember(available_key, player_id)
        if is_available:
            logger.info("draft.auto_draft.queue", draft_id=draft_id, player_id=player_id)
            return player_id

    # Priority 2: ADP + positional need
    best_player_id: str | None = None
    best_score: float = float("-inf")

    for player in adp_ranked_players:
        pid = str(player.get("player_id", ""))
        if not pid:
            continue
        is_available = await redis.sismember(available_key, pid)
        if not is_available:
            continue
        position = str(player.get("position", ""))
        # Lower rank = better; convert to descending score: negate rank
        adp_score = -(player.get("overall_rank", 9999))
        need_bonus = positional_need_bonus(team_positions, position, roster_format)
        total_score = adp_score + need_bonus
        if total_score > best_score:
            best_score = total_score
            best_player_id = pid

    if best_player_id:
        logger.info("draft.auto_draft.adp", draft_id=draft_id, player_id=best_player_id)
    return best_player_id


async def arm_auto_draft_timer(
    redis_pool,
    draft_id: str,
    pick_num: int,
    deadline_epoch: float,
) -> None:
    """Enqueue arq auto_draft_pick job to fire at deadline_epoch.

    Uses _job_id=f"autodraft:{draft_id}:{pick_num}" for uniqueness per pick.
    Non-critical: wrapped in try/except so test environments without arq don't break.
    """
    try:
        from datetime import UTC
        deadline_dt = datetime.fromtimestamp(deadline_epoch, tz=UTC)
        await redis_pool.enqueue_job(
            "auto_draft_pick",
            draft_id=str(draft_id),
            pick_num=pick_num,
            _defer_until=deadline_dt,
            _job_id=f"autodraft:{draft_id}:{pick_num}",
            _expires=deadline_dt,
        )
    except Exception as exc:
        logger.warning("draft.arm_timer.failed", draft_id=draft_id, pick_num=pick_num, error=str(exc))


async def import_csv_rankings(
    csv_content: str,
    draft_id: UUID,
    user_id: UUID,
    db: AsyncSession,
) -> list[UserDraftRanking]:
    """Parse CSV rankings and upsert into user_draft_rankings.

    CSV format: player_name,rank  (header row required)
    Matches player names via exact player_id match (CSV must include player_id column)
    or fuzzy name lookup. Returns list of upserted UserDraftRanking rows.

    CSV format accepted:
      player_id,rank         <- preferred: direct player_id
      player_name,rank       <- fallback: name-based match (best effort)
    """
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)
    if not rows:
        return []

    rankings: list[UserDraftRanking] = []
    async with db.begin_nested():
        # Delete existing rankings for this user+draft before re-importing
        existing = await db.execute(
            select(UserDraftRanking).where(
                UserDraftRanking.draft_id == draft_id,
                UserDraftRanking.user_id == user_id,
            )
        )
        for existing_row in existing.scalars():
            await db.delete(existing_row)
        await db.flush()

        for i, row in enumerate(rows, start=1):
            player_id = row.get("player_id", "").strip()
            rank_str = row.get("rank", str(i)).strip()
            if not player_id:
                continue
            try:
                rank = int(rank_str)
            except ValueError:
                rank = i
            ranking = UserDraftRanking(
                draft_id=draft_id,
                user_id=user_id,
                player_id=player_id,
                rank=rank,
                source="csv",
            )
            db.add(ranking)
            rankings.append(ranking)

        await db.flush()

    logger.info("draft.rankings.imported", draft_id=str(draft_id), user_id=str(user_id), count=len(rankings))
    return rankings

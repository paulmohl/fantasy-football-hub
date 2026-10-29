from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.league import League, LeagueMember, Team
from app.models.user import User


async def claim_team(
    db: AsyncSession,
    user: User,
    league: League,
    member: LeagueMember | None,
    host_team_id: str | None,
) -> None:
    """Record which of the league's teams belongs to the connecting user.

    Every /team/* route finds the user's team via Team.owner_user_id, so an import
    that skips this leaves the league connected but empty.
    """
    if host_team_id is None:
        return

    owned = await db.execute(
        select(Team).where(Team.league_id == league.id, Team.owner_user_id == user.id)
    )
    for team in owned.scalars():
        if team.host_team_id != host_team_id:
            team.owner_user_id = None

    result = await db.execute(
        select(Team).where(Team.league_id == league.id, Team.host_team_id == host_team_id)
    )
    team = result.scalar_one_or_none()
    if team is not None:
        team.owner_user_id = user.id
    if member is not None:
        member.host_team_id = host_team_id

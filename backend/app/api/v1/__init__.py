from fastapi import APIRouter

from app.api.v1 import auth, draft, espn, health, leagues, oauth, sleeper, team, users, yahoo

router = APIRouter(prefix="/api/v1")
router.include_router(health.router, tags=["health"])
router.include_router(auth.router)
router.include_router(oauth.router)
router.include_router(users.router)
router.include_router(sleeper.router)
router.include_router(leagues.router)
router.include_router(team.router)
router.include_router(yahoo.router)
router.include_router(espn.router)
router.include_router(draft.router)

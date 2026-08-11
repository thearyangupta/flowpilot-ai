from app.api.routers import auth, executions, projects, system, users,reply_drafts
from fastapi import APIRouter
router = APIRouter()

router.include_router(system.router)
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(projects.router)
router.include_router(executions.router)
router.include_router(reply_drafts.router)
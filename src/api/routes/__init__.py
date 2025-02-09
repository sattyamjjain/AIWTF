from fastapi import APIRouter
from .research import router as research_router
from .code_assistant import router as code_assistant_router

# Create the main API router with the /api/v1 prefix
router = APIRouter()

# Include the sub-routers
router.include_router(
    research_router, 
    prefix="/api/v1/research", 
    tags=["research"]
)
router.include_router(
    code_assistant_router, 
    prefix="/api/v1/code-assistant", 
    tags=["code-assistant"]
) 
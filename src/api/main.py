from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import get_settings
from src.api.routes import research
import logging
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """Create FastAPI application"""
    # Load environment variables
    load_dotenv(override=True)

    # Verify required environment variables
    required_vars = ["OPENAI_API_KEY", "SERPAPI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )

    # Set up CORS
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Add routes
    app.include_router(research.router, prefix=settings.API_V1_STR, tags=["research"])

    return app


app = create_application()


# Add startup event handler
@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("Starting up application...")
    logger.info(f"SERPAPI_API_KEY found: {bool(os.getenv('SERPAPI_API_KEY'))}")
    logger.info(f"OPENAI_API_KEY found: {bool(os.getenv('OPENAI_API_KEY'))}")

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers.analyze import AnalyzeController
from app.routers.health import HealthController
from app.services.go2.transcriber import load_models
from app.services.go3.cv_detector import load_models as load_cv_models


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Loads WhisperX + MediaPipe models at startup — once, not per request."""
    load_models()
    load_cv_models()
    yield


def create_app() -> FastAPI:
    """App factory — creates and configures the FastAPI instance."""
    settings = get_settings()
    app = FastAPI(title="ReadRight GO2 API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(AnalyzeController().router)
    app.include_router(HealthController().router)

    return app


app = create_app()

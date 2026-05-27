import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers.analyze import AnalyzeController
from app.routers.health import HealthController
from app.services.db.supabase_client import init_supabase_client
from app.services.go2.transcriber import load_models
from app.services.go3.cv_detector import load_models as load_cv_models


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Loads WhisperX, MediaPipe, and Supabase client at startup — once, not per request."""
    load_models()
    load_cv_models()
    await asyncio.to_thread(init_supabase_client)
    yield


async def _pipeline_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Return pipeline errors as raw {"error", "code"} — not wrapped in {"detail": ...}."""
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


def create_app() -> FastAPI:
    """App factory — creates and configures the FastAPI instance."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,
    )

    settings = get_settings()
    app = FastAPI(title="ReadRight GO2 API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(HTTPException, _pipeline_error_handler)  # type: ignore[arg-type]
    app.include_router(AnalyzeController().router)
    app.include_router(HealthController().router)

    return app


app = create_app()

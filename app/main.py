from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.analyze import AnalyzeController


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # RR-021: WhisperX model pre-load goes here (load_models())
    yield


def create_app() -> FastAPI:
    """App factory — creates ug configures ang FastAPI instance."""
    app = FastAPI(title="ReadRight GO2 API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    controller = AnalyzeController()
    app.include_router(controller.router)

    return app


app = create_app()

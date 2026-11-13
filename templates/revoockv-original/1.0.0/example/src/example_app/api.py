"""Second entry point (FastAPI). Run: uv run uvicorn example_app.api:app --reload."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from example_app.di import register_and_init
from example_app.features.notes.presentation.api.notes_router import router as notes_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Register dependencies and run initiations before serving requests."""
    await register_and_init()
    yield


def create_app() -> FastAPI:
    """Build the FastAPI application and include every feature router."""
    app = FastAPI(lifespan=lifespan)
    # <routers>
    app.include_router(notes_router)
    # </routers>
    return app


app = create_app()

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.analysis.llm import LLMClient
from app.automation import AutomationEngine
from app.collector.fixture import FixtureCollector
from app.collector.wegame import WeGameCollector
from app.config import FIXTURE_DIR, load_settings
from app.db import init_db
from app.routes import analysis, coaching, matches
from app.routes import notifications as notifications_route
from app.routes import settings as settings_route
from app.routes import training as training_route


def create_app() -> FastAPI:
    init_db()
    settings = load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.automation.enabled:
            app.state.automation.start(app)
        yield
        app.state.automation.stop()

    app = FastAPI(title="无畏契约 AI 对局教练", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=["*"],
                       allow_methods=["*"], allow_headers=["*"])

    if os.environ.get("COLLECTOR", "fixture") == "wegame":
        app.state.collector = WeGameCollector(settings.wegame)
    else:
        app.state.collector = FixtureCollector(FIXTURE_DIR)
    app.state.llm = LLMClient(settings.llm.base_url,
                              settings.llm.api_key, settings.llm.model)
    app.state.automation = AutomationEngine(settings.automation.poll_interval_min)

    app.include_router(matches.router)
    app.include_router(analysis.router)
    app.include_router(coaching.router)
    app.include_router(settings_route.router)
    app.include_router(notifications_route.router)
    app.include_router(training_route.router)

    dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if dist.exists():
        app.mount("/", StaticFiles(directory=dist, html=True), name="static")
    return app


app = create_app()

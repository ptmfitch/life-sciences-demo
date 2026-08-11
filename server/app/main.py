from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import SessionLocal, apply_migrations
from app.etl.router import router as etl_router
from app.dashboards.router import router as dash_router
from app.runs.events import broker
from app.runs.manager import RunManager
from app.runs.router import router as runs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.telemetry_path.mkdir(parents=True, exist_ok=True)
    await apply_migrations()
    manager = RunManager(broker=broker)
    app.state.manager = manager
    async with SessionLocal() as session:
        await manager.startup(session)
    yield
    await manager.shutdown()


app = FastAPI(
    title="AstraLume BioTest Demo",
    description="Synthetic biotesting telemetry demo — illustrative only, not clinically validated.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runs_router, prefix="/api")
app.include_router(etl_router, prefix="/api")
app.include_router(dash_router, prefix="/api")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "demo": "AstraLume BioTest Station",
        "disclaimer": "Synthetic illustrative data only — not scientific or clinical evidence.",
        "telemetry_dir": str(settings.telemetry_path),
        "demo_speed": settings.demo_speed,
    }
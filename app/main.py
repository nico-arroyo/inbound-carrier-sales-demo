from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from fastapi import FastAPI

from app.core.config import settings
from app.core.state import init_state
from app.routers.health import router as health_router
from app.routers.webhooks import router as webhooks_router
from app.routers.carriers import router as carriers_router
from app.routers.loads import router as loads_router
from app.routers.negotiations import router as negotiations_router
from app.routers.metrics import router as metrics_router
from app.db import init_db

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Inbound Carrier Sales POC", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.on_event("startup")
def _startup() -> None:
    init_state()
    init_db()

@app.get("/dashboard")
def dashboard():
    return FileResponse(str(STATIC_DIR / "dashboard.html"))

# Public
app.include_router(health_router)

# Secured
app.include_router(webhooks_router)
app.include_router(carriers_router)
app.include_router(loads_router)
app.include_router(negotiations_router)
app.include_router(metrics_router)

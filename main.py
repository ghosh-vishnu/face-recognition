import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from .routers import (
    upload,
    charts,
    insights,
    forecast,
    anomalies,
    actions,
    auth,
    simulate,
    voice,
)
from .services.auto_action_engine import action_stream_broker

# -------------------------------------------------------------------
# LOGGING
# -------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("auto_explain_dashboard")

# -------------------------------------------------------------------
# PATHS
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# -------------------------------------------------------------------
# LIFESPAN (REPLACES on_event)
# -------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Auto-Explain Dashboard API starting")
    await action_stream_broker.connect()
    yield
    logger.info("Auto-Explain Dashboard API shutting down")
    await action_stream_broker.disconnect()

# -------------------------------------------------------------------
# APP INIT
# -------------------------------------------------------------------

app = FastAPI(
    title="Auto-Explain Dashboard API",
    description="Enterprise AI platform for automated business analytics",
    version="1.0.0",
    lifespan=lifespan,
)

# -------------------------------------------------------------------
# CORS (SAFE)
# -------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://dashboard.yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# -------------------------------------------------------------------
# STATIC FILES
# -------------------------------------------------------------------

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# -------------------------------------------------------------------
# ROUTERS
# -------------------------------------------------------------------

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(upload.router, prefix="/upload", tags=["upload"])
app.include_router(charts.router, prefix="/charts", tags=["charts"])
app.include_router(insights.router, prefix="/insights", tags=["insights"])
app.include_router(forecast.router, prefix="/forecast", tags=["forecast"])
app.include_router(anomalies.router, prefix="/anomalies", tags=["anomalies"])
app.include_router(actions.router, prefix="/actions", tags=["actions"])
app.include_router(simulate.router, prefix="/simulate", tags=["simulate"])
app.include_router(voice.router, prefix="/voice", tags=["voice"])

# -------------------------------------------------------------------
# HEALTHCHECK
# -------------------------------------------------------------------

@app.get("/health", tags=["system"])
async def healthcheck():
    return {"status": "ok"}

# -------------------------------------------------------------------
# WEBSOCKET ALERTS
# -------------------------------------------------------------------

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await websocket.accept()
    subscriber = action_stream_broker.subscribe()

    try:
        async for alert in subscriber:
            try:
                await websocket.send_json(alert)
            except Exception:
                logger.exception("Failed to send websocket alert")
                break

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")

    finally:
        await action_stream_broker.unsubscribe(subscriber)

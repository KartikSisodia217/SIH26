"""
OceanEmbed FastAPI Main Application Server.
Serves 3D subsurface ocean temperature reconstruction endpoints and metrics for the frontend dashboard.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.schemas import HealthResponse
from api.routers import predict
from src.inference.engine import get_inference_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI server lifecycle manager: Initializes PyTorch inference engine on boot."""
    print("[Lifecycle] Server starting up - Initializing ConvFormer Inference Engine...")
    get_inference_engine()
    yield
    print("[Lifecycle] Server shutting down.")


app = FastAPI(
    title="OceanEmbed API",
    description=(
        "REST API serving ConvFormer 3D Subsurface Ocean Temperature Reconstructions "
        "and D26 Isotherm / TCHP derivations for the North Indian Ocean domain (5°N–30°N, 45°E–105°E)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS for React/Leaflet frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(predict.router)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System Health"],
    summary="Health Check Endpoint",
    description="Returns backend API status and model state info."
)
def health_check():
    engine = get_inference_engine()
    return HealthResponse(
        status="ok",
        version="1.0.0",
        model_loaded=engine.is_real_model,
        mode=engine.mode
    )


@app.get("/", tags=["System Health"], include_in_schema=False)
def root():
    engine = get_inference_engine()
    return {
        "title": "OceanEmbed REST API Server",
        "status": "running",
        "mode": engine.mode,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)

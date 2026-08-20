from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from .routes import router
from .schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Shell Commands AI Skill API...")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="Shell Commands AI Skill API",
    description="Structured reference for Unix/Linux shell commands with natural language search",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1")


@app.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(
        status="ok",
        version="1.0.0",
        commands_indexed=0,
        index_updated_at="2026-01-01T00:00:00Z"
    )


if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
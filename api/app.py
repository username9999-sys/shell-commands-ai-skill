from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import time
from collections import defaultdict

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

# Rate limiting storage
rate_limit_storage: dict = defaultdict(list)
RATE_LIMIT_REQUESTS = 60  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for health checks
    if request.url.path in ["/", "/api/v1/health"]:
        return await call_next(request)
    
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()
    
    # Clean old entries
    rate_limit_storage[client_ip] = [
        timestamp for timestamp in rate_limit_storage[client_ip]
        if current_time - timestamp < RATE_LIMIT_WINDOW
    ]
    
    # Check rate limit
    if len(rate_limit_storage[client_ip]) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 60 requests per minute."
        )
    
    # Add current request
    rate_limit_storage[client_ip].append(current_time)
    
    # Process request
    response = await call_next(request)
    return response

# Include routes
app.include_router(router, prefix="/api/v1")

# CORS (after rate limiting)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
"""FastAPI application main entry point"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app import __version__
from app.cache.redis_client import close_redis_client
from app.config import settings
from app.db.session import close_db, init_db
from app.routes import health, profile, search
from app.utils.errors import AroundMeException, create_problem_detail
from app.utils.logging import get_logger, get_trace_id, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("application_startup", version=__version__)
    await init_db()
    
    yield
    
    # Shutdown
    logger.info("application_shutdown")
    await close_redis_client()
    await close_db()


# Create FastAPI app
app = FastAPI(
    title="Around Me API",
    description="Local Discovery Agent with Agentic AI",
    version=__version__,
    lifespan=lifespan,
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(AroundMeException)
async def aroundme_exception_handler(request: Request, exc: AroundMeException):
    """Handle custom exceptions"""
    trace_id = get_trace_id()
    problem_detail = create_problem_detail(exc, trace_id)
    
    logger.error(
        "exception_handled",
        error_type=exc.error_type,
        status_code=exc.status_code,
        message=exc.message,
        trace_id=trace_id,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=problem_detail.model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions"""
    trace_id = get_trace_id()
    
    logger.error(
        "unhandled_exception",
        error=str(exc),
        trace_id=trace_id,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "type": "internal-error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred",
            "trace_id": trace_id,
        },
    )


# Include routers
app.include_router(search.router)
app.include_router(health.router)
app.include_router(profile.router)


# Root endpoint
@app.get("/")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def root(request: Request):
    """Root endpoint"""
    return {
        "name": "Around Me API",
        "version": __version__,
        "docs": "/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
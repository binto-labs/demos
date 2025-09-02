"""
Earthquake Claim Accelerator - FastAPI Backend Application
Main entry point for the FastAPI application with proper middleware and routing setup.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import uvicorn

from core.config import settings
from database.connection import engine
from api.routers import property_router, policy_router, claim_router, document_router
from middleware.auth import AuthMiddleware
from middleware.logging import LoggingMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Earthquake Claim Accelerator API",
    description="Backend API for processing and managing earthquake insurance claims",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(AuthMiddleware)
app.add_middleware(LoggingMiddleware)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": time.time()
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "timestamp": time.time()
            }
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancing"""
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e)
            }
        )

# API version prefix
api_prefix = "/api/v1"

# Include routers
app.include_router(
    property_router.router,
    prefix=f"{api_prefix}/properties",
    tags=["Properties"]
)
app.include_router(
    policy_router.router,
    prefix=f"{api_prefix}/policies",
    tags=["Policies"]
)
app.include_router(
    claim_router.router,
    prefix=f"{api_prefix}/claims",
    tags=["Claims"]
)
app.include_router(
    document_router.router,
    prefix=f"{api_prefix}/documents",
    tags=["Documents"]
)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Earthquake Claim Accelerator API",
        "version": "1.0.0",
        "description": "Backend API for processing earthquake insurance claims",
        "docs": "/api/docs",
        "health": "/health"
    }

# Application startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Earthquake Claim Accelerator API")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'Not configured'}")

# Application shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down Earthquake Claim Accelerator API")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )
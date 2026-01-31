from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.api.verify import router as verify_router

# Create FastAPI application
app = FastAPI(
    title="Face Verification API",
    description="Production-ready face verification system for 3-image comparison",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include verification router
app.include_router(verify_router, prefix="/api", tags=["verification"])


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Face Verification API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "verify": "/api/verify (POST)",
            "health": "/api/health (GET)"
        }
    }


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("\n" + "="*60)
    print("Starting Face Verification API")
    print("="*60)
    print("Loading InsightFace models...")
    print("This may take a moment on first run...")
    print("="*60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("\n" + "="*60)
    print("Shutting down Face Verification API")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Set to False in production
        log_level="info"
    )

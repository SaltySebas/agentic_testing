"""
FastAPI application for the agentic test generator web UI.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agentic Test Generator API",
    description="AI-powered test generation with multi-agent orchestration",
    version="1.0.0"
)

# CORS - allow all origins in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


# Import and include routers
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from api.routes import router as api_router
from api.websocket import router as ws_router

app.include_router(api_router, prefix="/api")
app.include_router(ws_router)

# Serve React static files (will be used after building frontend)
# frontend_build = Path(__file__).parent.parent.parent / "frontend" / "build"
# if frontend_build.exists():
#     app.mount("/", StaticFiles(directory=str(frontend_build), html=True), name="static")


@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info("Agentic Test Generator API starting up...")
    logger.info("API documentation available at /docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Agentic Test Generator API shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)


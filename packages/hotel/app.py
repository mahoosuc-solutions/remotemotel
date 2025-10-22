"""
Hotel Management Application

Main FastAPI application that combines all hotel management functionality.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from packages.hotel.api import router as hotel_router
from packages.hotel.admin import router as admin_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="West Bethel Motel Management System",
    description="Comprehensive hotel management system with rates, availability, and booking management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(hotel_router)
app.include_router(admin_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "West Bethel Motel Management System",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to West Bethel Motel Management System",
        "docs": "/docs",
        "admin": "/admin",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

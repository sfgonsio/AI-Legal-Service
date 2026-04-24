"""
FastAPI main application with CORS, routes, startup events
Render.com + Vercel deployment ready
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from database import init_db
from routes import cases, weapons, strategies, coas, documents, deposition, case_authority, actors, interviews, legal_library
from seed_data import seed_initial_data

# Frontend URL — set via Render env var, defaults to localhost for dev
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager
    Handles startup and shutdown events
    """
    # Startup: create tables and seed data
    await init_db()
    await seed_initial_data()
    print("CaseCore backend initialized")

    yield

    # Shutdown
    print("CaseCore backend shutting down")


# Create FastAPI app with lifespan
app = FastAPI(
    title="CaseCore API",
    description="Legal case management and strategy platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(cases.router)
app.include_router(weapons.router)
app.include_router(strategies.router)
app.include_router(coas.router)
app.include_router(documents.router)
app.include_router(deposition.router)
app.include_router(case_authority.router)
app.include_router(actors.router)
app.include_router(interviews.router)
app.include_router(legal_library.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "CaseCore API",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CaseCore API",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

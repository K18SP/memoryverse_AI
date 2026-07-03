"""
MemoryVerse AI — FastAPI entry point
Run:  uvicorn backend.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.config import get_settings
from backend.vector_store.qdrant_client import init_qdrant_collection
from backend.api.routes import router as api_router


# ── Lifespan: runs once on startup & shutdown ──────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    print(f"🚀  MemoryVerse starting in [{settings.app_env}] mode")

    try:
        await init_qdrant_collection()
        print("✅  Qdrant collection ready")
    except Exception as e:
        print(f"⚠️   Qdrant not running — vector storage disabled for now")
        print(f"⚠️   Install Docker and run: docker run -d -p 6333:6333 qdrant/qdrant")

    yield

    print("🛑  MemoryVerse shutting down")


# ── App factory ────────────────────────────────────────────────────────────
app = FastAPI(
    title="MemoryVerse AI",
    description="AI-powered Digital Identity System — MemoryVerse AI '26",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the React frontend (localhost:3000) to call this API during dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount all routes ───────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "MemoryVerse AI",
        "version": "1.0.0",
    }

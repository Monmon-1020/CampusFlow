import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import assignments, auth, events, lost_items, profile, streams

# .envファイルを読み込み
load_dotenv()
# ルートディレクトリの.envも読み込み
load_dotenv("/workspaces/CampusFlow/.env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="CampusFlow API",
    description="A comprehensive school management system API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(assignments.router)
app.include_router(events.router)
app.include_router(streams.router)
app.include_router(profile.router)
app.include_router(lost_items.router)


@app.get("/")
async def root():
    return {"message": "Welcome to CampusFlow API", "docs": "/docs", "redoc": "/redoc"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

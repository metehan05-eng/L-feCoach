from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sys
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

sys.path.append(os.path.dirname(__file__))

from auth import router as auth_router
from chat import router as chat_router
from journal import router as journal_router
from goals import router as goals_router
from database import engine, Base
import asyncio

# Create all tables on startup
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all database tables on startup"""
    await create_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(chat_router, tags=["chat"])
app.include_router(journal_router, tags=["journal"])
app.include_router(goals_router, tags=["goals"])

# Serve frontend files (index.html, script.js, style.css) from project root.
# Mount this after API routers so API endpoints like /chat, /auth take precedence.
project_root = Path(__file__).parent.parent
app.mount("/", StaticFiles(directory=str(project_root), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port)
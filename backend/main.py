import logging
import os
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agent.coach_agent import run_coach_session
from analysis.jobs import create_ingest_job, get_ingest_job, run_ingest_job, serialize_job
from analysis.stockfish_worker import stockfish_pool
from db.database import get_db
from db.models import Game, Position, WeaknessProfile

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await stockfish_pool.close()


app = FastAPI(lifespan=lifespan)

_default_origins = "http://localhost:5173,http://localhost:5174"
_cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=os.getenv("CORS_ORIGIN_REGEX", r"https://.*\.vercel\.app"),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CoachRequest(BaseModel):
    username: str
    message: str


@app.get("/")
async def root():
    return {
        "name": "Morphy API",
        "status": "ok",
        "docs": "/docs",
        "endpoints": {
            "coach": "POST /coach",
            "ingest": "POST /ingest/{username}",
            "job_status": "GET /jobs/{job_id}",
            "profile": "GET /profile/{username}",
        },
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/coach")
async def coach(req: CoachRequest, db: Session = Depends(get_db)):
    response = await run_coach_session(req.username, req.message, db)
    return {"response": response}


@app.post("/ingest/{username}")
async def ingest(
    username: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Enqueue a background ingestion + analysis job for a user."""
    job = create_ingest_job(username, db)
    background_tasks.add_task(run_ingest_job, job.id)
    logger.info("Queued ingest job %s for %s", job.id, username)
    return serialize_job(job)


@app.get("/jobs/{job_id}")
async def job_status(job_id: str, db: Session = Depends(get_db)):
    job = get_ingest_job(job_id, db)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return serialize_job(job)


@app.get("/profile/{username}")
async def get_profile(username: str, db: Session = Depends(get_db)):
    """Return weakness profile + summary stats for the dashboard."""
    username = username.lower()
    profiles = (
        db.query(WeaknessProfile)
        .filter_by(username=username)
        .order_by(WeaknessProfile.severity.desc())
        .all()
    )

    games_analyzed = (
        db.query(Game).filter_by(username=username, analyzed=True).count()
    )
    blunders = (
        db.query(Position)
        .join(Game)
        .filter(
            Game.username == username,
            Position.is_your_move.is_(True),
            Position.classification == "blunder",
        )
        .count()
    )

    return {
        "profile": [
            {
                "theme": profile.theme,
                "frequency": profile.frequency,
                "severity": profile.severity,
                "last_seen": profile.last_seen.isoformat() if profile.last_seen else None,
                "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
            }
            for profile in profiles
        ],
        "stats": {
            "games_analyzed": games_analyzed,
            "blunder_rate": round(blunders / games_analyzed, 2) if games_analyzed else 0,
            "total_blunders": blunders,
        },
    }

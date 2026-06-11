import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agent.coach_agent import run_coach_session
from analysis.jobs import create_ingest_job, get_ingest_job, run_ingest_job, serialize_job
from analysis.stockfish_worker import stockfish_pool
from db.database import get_db
from db.models import WeaknessProfile


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await stockfish_pool.close()


app = FastAPI(lifespan=lifespan)


class CoachRequest(BaseModel):
    username: str
    message: str


@app.post("/coach")
async def coach(req: CoachRequest, db: Session = Depends(get_db)):
    response = await run_coach_session(req.username, req.message, db)
    return {"response": response}


@app.post("/ingest/{username}")
async def ingest(username: str, db: Session = Depends(get_db)):
    """Enqueue a background ingestion + analysis job for a user."""
    job = create_ingest_job(username, db)
    asyncio.create_task(run_ingest_job(job.id))
    return serialize_job(job)


@app.get("/jobs/{job_id}")
async def job_status(job_id: str, db: Session = Depends(get_db)):
    job = get_ingest_job(job_id, db)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return serialize_job(job)


@app.get("/profile/{username}")
async def get_profile(username: str, db: Session = Depends(get_db)):
    """Return weakness profile + stats for the dashboard."""
    profiles = (
        db.query(WeaknessProfile)
        .filter_by(username=username)
        .order_by(WeaknessProfile.severity.desc())
        .all()
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
        ]
    }

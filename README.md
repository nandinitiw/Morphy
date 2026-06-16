# Morphy

Chess coaching app — ingests your Chess.com games, runs Stockfish analysis, and surfaces tactical weaknesses.

## Local development

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
brew install stockfish   # required for analysis

uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env     # set VITE_API_URL=http://localhost:8000
npm run dev
```

Open [http://localhost:5173](http://localhost:5173), enter your Chess.com username, and click **Analyze my games**.

---

## Deploy to Vercel (frontend)

The **frontend** deploys to Vercel. The **backend** must be hosted separately (Railway, Render, Fly.io, etc.) because it needs Stockfish, a persistent database, and long-running analysis jobs.

### 1. Deploy the backend first

Example: [Railway](https://railway.app) or [Render](https://render.com)

- Root directory: `backend`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Install Stockfish in your build (e.g. `apt-get install stockfish` on Render/Railway)
- Set environment variables:
  - `DATABASE_URL` — Postgres connection string (recommended for production; SQLite won't persist on serverless)
  - `CORS_ORIGINS` — your Vercel URL, e.g. `https://morphy.vercel.app`
  - `STOCKFISH_PATH` — path to stockfish binary if not on PATH
  - `ANTHROPIC_API_KEY` — for the coach agent (optional)

Note your backend URL, e.g. `https://morphy-api.onrender.com`

### 2. Deploy the frontend to Vercel

1. Push this repo to GitHub
2. Import the project in [vercel.com](https://vercel.com)
3. Set **Root Directory** to `frontend`
4. Add environment variable:
   - `VITE_API_URL` = your backend URL (e.g. `https://morphy-api.onrender.com`)
5. Deploy

Vercel will run `npm run build` and serve the Vite app. The username is entered in the UI — no need to set `VITE_USERNAME`.

### 3. Verify

- Visit your Vercel URL
- Enter a Chess.com username
- Click **Analyze my games**
- Dashboard and Weaknesses should populate when the backend job completes

---

## Architecture

```
Chess.com API  →  backend (FastAPI + Stockfish)  →  morphy.db / Postgres
                              ↑
                    frontend (Vercel / Vite)
```

Users enter their Chess.com username in the browser. The frontend calls `POST /ingest/{username}` on your backend, polls job status, then loads `/profile/{username}` for weakness data.

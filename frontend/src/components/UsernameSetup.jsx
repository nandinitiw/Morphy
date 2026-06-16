import { useEffect, useState } from "react";

import { checkBackendHealth, getApiBase } from "../api/client.js";
import { useUsername } from "../context/UsernameContext.jsx";
import { useIngest } from "../context/IngestContext.jsx";

export default function UsernameSetup() {
  const { setUsername, normalizeUsername } = useUsername();
  const { startIngest, job, error: ingestError, isRunning } = useIngest();
  const [input, setInput] = useState("");
  const [validationError, setValidationError] = useState("");
  const [backendOk, setBackendOk] = useState(null);

  useEffect(() => {
    checkBackendHealth()
      .then(() => setBackendOk(true))
      .catch(() => setBackendOk(false));
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    const normalized = normalizeUsername(input);
    if (normalized.length < 3) {
      setValidationError("Enter a valid Chess.com username (at least 3 characters).");
      return;
    }
    setValidationError("");
    setUsername(normalized);
    await startIngest(normalized);
  }

  return (
    <div className="setup-screen">
      <div className="setup-card">
        <div className="setup-logo">Morphy</div>
        <p className="setup-tagline">Your chess coach agent</p>

        <form className="setup-form" onSubmit={handleSubmit}>
          <label className="setup-label" htmlFor="chess-username">
            Chess.com username
          </label>
          <input
            id="chess-username"
            className="setup-input"
            type="text"
            placeholder="e.g. hikaru"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            autoComplete="username"
            autoFocus
            disabled={isRunning}
          />
          {(validationError || ingestError) && (
            <p className="setup-error">{validationError || ingestError}</p>
          )}
          <button className="setup-btn" type="submit" disabled={isRunning || !input.trim()}>
            {isRunning ? "Analyzing your games…" : "Analyze my games"}
          </button>
        </form>

        {job && (
          <div className="setup-progress">
            <div className="setup-progress-status">
              Status: <strong>{job.status}</strong>
            </div>
            {job.status === "ingesting" && (
              <p className="setup-progress-detail">Fetching games from Chess.com…</p>
            )}
            {job.status === "analyzing" && (
              <p className="setup-progress-detail">
                Analyzed {job.games_analyzed} / {job.games_total} games
              </p>
            )}
            {job.status === "completed" && (
              <p className="setup-progress-detail setup-success">
                Done — {job.games_analyzed} games analyzed, {job.weakness_themes} weakness themes found.
              </p>
            )}
            {job.status === "failed" && (
              <p className="setup-progress-detail setup-error">{job.error}</p>
            )}
          </div>
        )}

        <p className="setup-footnote">
          We pull your public Chess.com games and run Stockfish analysis to find tactical blind spots.
        </p>

        {backendOk === false && (
          <div className="setup-backend-warning">
            <strong>Backend not reachable</strong> at {getApiBase()}
            <br />
            Run locally: <code>cd backend && uvicorn main:app --reload --port 8000</code>
            <br />
            On Vercel: set <code>VITE_API_URL</code> to your hosted backend URL and redeploy.
          </div>
        )}
        {backendOk === true && (
          <p className="setup-backend-ok">Connected to backend</p>
        )}
      </div>
    </div>
  );
}

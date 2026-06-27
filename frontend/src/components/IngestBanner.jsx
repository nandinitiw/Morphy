import { useIngest } from "../context/IngestContext.jsx";

const STATUS_LABELS = {
  pending: "Queued",
  ingesting: "Fetching games from Chess.com",
  analyzing: "Running Stockfish analysis",
  profiling: "Building weakness profile",
  completed: "Analysis complete",
  failed: "Analysis failed",
};

export default function IngestBanner({ username, onComplete }) {
  const { job, error, isRunning, startIngest } = useIngest();

  if (username === "demo") {
    return (
      <div className="ingest-banner ingest-banner-demo">
        <div className="ingest-banner-text">
          <strong>Demo mode</strong> — pre-loaded with 30 rapid games and 6 weakness themes.
          Enter your Chess.com username on the home screen to analyze your own games.
        </div>
      </div>
    );
  }

  async function handleRefresh() {
    try {
      const finalJob = await startIngest(username);
      if (finalJob?.status === "completed") {
        onComplete?.();
      }
    } catch {
      // error surfaced via context
    }
  }

  if (!job && !isRunning && !error) {
    return (
      <div className="ingest-banner">
        <div className="ingest-banner-text">
          Analyzing <strong>{username}</strong> on Chess.com
        </div>
        <button type="button" className="ingest-banner-btn" onClick={handleRefresh}>
          Refresh games
        </button>
      </div>
    );
  }

  return (
    <div className={`ingest-banner ${job?.status === "failed" ? "ingest-banner-error" : ""}`}>
      <div className="ingest-banner-text">
        {isRunning || job ? (
          <>
            <strong>{STATUS_LABELS[job?.status] ?? "Working…"}</strong>
            {job?.status === "analyzing" && (
              <span className="ingest-banner-detail">
                {" "}
                — {job.games_analyzed} / {job.games_total} games
              </span>
            )}
            {job?.status === "ingesting" && job.games_ingested > 0 && (
              <span className="ingest-banner-detail"> — {job.games_ingested} new games</span>
            )}
            {job?.status === "completed" && (
              <span className="ingest-banner-detail">
                {" "}
                — {job.games_analyzed} games, {job.weakness_themes} themes
              </span>
            )}
            {(error || job?.error) && (
              <span className="ingest-banner-detail ingest-error"> — {error || job.error}</span>
            )}
          </>
        ) : null}
      </div>
      {!isRunning && (
        <button type="button" className="ingest-banner-btn" onClick={handleRefresh}>
          Refresh games
        </button>
      )}
    </div>
  );
}

import { useEffect, useRef, useState } from "react";
import { fetchWeaknessProfile, themeLabel } from "../api/client";
import Chart from "chart.js/auto";

export default function Dashboard({ username, refreshKey = 0 }) {
  const [stats, setStats] = useState(null);
  const [weaknesses, setWeaknesses] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const accuracyRef = useRef(null);
  const accuracyChart = useRef(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchWeaknessProfile(username)
      .then((data) => {
        setStats(data.stats);
        setWeaknesses(data.weaknesses);
      })
      .catch(setError)
      .finally(() => setLoading(false));
  }, [username, refreshKey]);

  useEffect(() => {
    if (!stats || !accuracyRef.current || weaknesses.length === 0) return;

    const isDark = matchMedia("(prefers-color-scheme: dark)").matches;
    const textColor = isDark ? "rgba(232,227,213,0.4)" : "rgba(0,0,0,0.4)";
    const gridColor = isDark ? "rgba(255,255,255,0.07)" : "rgba(0,0,0,0.07)";

    const top = weaknesses.slice(0, 6);
    if (accuracyChart.current) accuracyChart.current.destroy();
    accuracyChart.current = new Chart(accuracyRef.current, {
      type: "bar",
      data: {
        labels: top.map((w) => themeLabel(w.theme)),
        datasets: [{
          data: top.map((w) => w.severity),
          backgroundColor: "#C0392B",
          borderRadius: 4,
        }],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: textColor, font: { size: 11, family: "DM Mono" } }, grid: { color: gridColor } },
          y: { ticks: { color: textColor, font: { size: 11, family: "DM Mono" } }, grid: { display: false } },
        },
      },
    });

    return () => accuracyChart.current?.destroy();
  }, [stats, weaknesses]);

  if (error) return <div className="error">Failed to load profile: {error.message}</div>;
  if (loading) return <div className="loading">Loading your analysis…</div>;

  const maxFreq = Math.max(...weaknesses.map((w) => w.frequency), 1);
  const gamesAnalyzed = stats?.games_analyzed ?? 0;

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-title">Performance overview</div>
        <div className="page-sub">
          {gamesAnalyzed > 0
            ? `${gamesAnalyzed} games analyzed for ${username}`
            : `No analyzed games yet — click Refresh games above`}
        </div>
      </div>

      <div className="metrics-row">
        <div className="metric-card">
          <div className="metric-label">Games analyzed</div>
          <div className="metric-value">{gamesAnalyzed}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Blunders / game</div>
          <div className="metric-value">{stats?.blunder_rate?.toFixed(1) ?? "0.0"}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Total blunders</div>
          <div className="metric-value">{stats?.total_blunders ?? 0}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Weakness themes</div>
          <div className="metric-value">{weaknesses.length}</div>
        </div>
      </div>

      {weaknesses.length === 0 ? (
        <div className="card">
          <div className="card-title">No weakness data yet</div>
          <p className="empty-copy">
            Run an analysis from the banner above. Once Stockfish finishes, your tactical blind spots will show up here.
          </p>
        </div>
      ) : (
        <div className="three-col">
          <div className="card">
            <div className="card-title">Severity by theme</div>
            <div className="chart-wrap" style={{ height: 200 }}>
              <canvas ref={accuracyRef} role="img" aria-label="Bar chart of weakness severity by theme" />
            </div>
          </div>
          <div className="card">
            <div className="card-title">Top weaknesses</div>
            <div className="weakness-list">
              {weaknesses.slice(0, 6).map((w) => (
                <div className="weakness-item" key={w.theme}>
                  <div className="weakness-header">
                    <span className="weakness-name">{w.display}</span>
                    <span className="weakness-count">{w.frequency}×</span>
                  </div>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{ width: `${(w.frequency / maxFreq) * 100}%`, background: "#C0392B" }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

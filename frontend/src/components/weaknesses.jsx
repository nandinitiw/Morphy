import { useEffect, useState } from "react";
import { fetchWeaknessProfile } from "../api/client";

const severityColor = (s) => {
  if (s >= 200) return "#C0392B";
  if (s >= 130) return "#BA7517";
  return "rgba(255,255,255,0.3)";
};

export default function Weaknesses({ username, refreshKey = 0 }) {
  const [weaknesses, setWeaknesses] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchWeaknessProfile(username)
      .then((data) => setWeaknesses(data.weaknesses))
      .catch(setError)
      .finally(() => setLoading(false));
  }, [username, refreshKey]);

  if (error) return <div className="error">Failed to load weaknesses: {error.message}</div>;
  if (loading) return <div className="loading">Loading weakness profile…</div>;

  const maxFreq = Math.max(...weaknesses.map((w) => w.frequency), 1);

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-title">Weakness fingerprint</div>
        <div className="page-sub">built from analyzed games for {username}</div>
      </div>

      {weaknesses.length === 0 ? (
        <div className="card">
          <div className="card-title">No blunders clustered yet</div>
          <p className="empty-copy">
            Analyze more games to build your weakness fingerprint. Blunders are grouped by tactical theme
            (forks, pins, back rank, etc.).
          </p>
        </div>
      ) : (
        <div className="card">
          <div className="card-title">Tactical blind spots</div>
          <div className="weakness-list" style={{ gap: 14 }}>
            {weaknesses.map((w) => (
              <div className="weakness-item" key={w.theme}>
                <div className="weakness-header">
                  <span className="weakness-name">{w.display}</span>
                  <span className="weakness-count">{w.frequency}× · avg {w.severity}cp loss</span>
                </div>
                <div className="bar-track" style={{ height: 6 }}>
                  <div
                    className="bar-fill"
                    style={{
                      width: `${(w.frequency / maxFreq) * 100}%`,
                      background: severityColor(w.severity),
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

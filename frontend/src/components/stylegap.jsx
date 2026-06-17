import { useEffect, useRef, useState } from "react";
import { fetchStyleGap, sendCoachMessage } from "../api/client";
import AiTooltip from "./AiTooltip";
import RecommendButton from "./RecommendButton";
import Chart from "chart.js/auto";

const MOCK_STYLE = {
  you: { development: 72, open_files: 61, king_attack: 18, sacrifice_rate: 14, aggression: 40 },
  morphy: { development: 95, open_files: 88, king_attack: 67, sacrifice_rate: 70, aggression: 90 },
  stats: {
    you: { avg_game_length: 38, sacrifice_rate: "2%", open_file_control: "61%", king_attack_freq: "18%", development_speed: "move 8.2" },
    morphy: { avg_game_length: 28, sacrifice_rate: "14%", open_file_control: "88%", king_attack_freq: "67%", development_speed: "move 5.1" },
  },
};

const STAT_LABELS = {
  avg_game_length: "Avg game length",
  sacrifice_rate: "Piece sacrifice rate",
  open_file_control: "Open file control",
  king_attack_freq: "King attack frequency",
  development_speed: "Development speed",
};

const AXIS_HELP = {
  Development: "How quickly you get pieces off the back rank and into the game.",
  "Open files": "How often you contest or occupy open files with rooks.",
  "King attack": "Frequency of kingside attacks and direct threats to the enemy king.",
  Sacrifices: "Willingness to give material for initiative or attack.",
  Aggression: "Overall tendency toward forcing, active play vs. quiet maneuvering.",
};

const BOARD_SAGE = "#E0D6C2";
const SIGNAL_GREEN = "#22C55E";

function isGoodForYou(key, youVal, morphyVal) {
  const youNum = parseFloat(youVal);
  const morphyNum = parseFloat(morphyVal);
  if (Number.isNaN(youNum) || Number.isNaN(morphyNum)) return null;
  return Math.abs(youNum - morphyNum) < Math.abs(morphyNum * 0.3) ? "good" : "bad";
}

export default function StyleGap({ username, onNavigateCoach }) {
  const [style, setStyle] = useState(null);
  const [error, setError] = useState(null);
  const [recoLoading, setRecoLoading] = useState(false);
  const [reco, setReco] = useState(null);
  const radarRef = useRef(null);
  const radarChart = useRef(null);

  useEffect(() => {
    fetchStyleGap(username)
      .then(setStyle)
      .catch(() => setStyle(MOCK_STYLE));
  }, [username]);

  useEffect(() => {
    if (!style || !radarRef.current) return;

    const labels = ["Development", "Open files", "King attack", "Sacrifices", "Aggression"];
    const youData = [style.you.development, style.you.open_files, style.you.king_attack, style.you.sacrifice_rate, style.you.aggression];
    const morphyData = [style.morphy.development, style.morphy.open_files, style.morphy.king_attack, style.morphy.sacrifice_rate, style.morphy.aggression];

    if (radarChart.current) radarChart.current.destroy();
    radarChart.current = new Chart(radarRef.current, {
      type: "radar",
      data: {
        labels,
        datasets: [
          {
            label: "You",
            data: youData,
            borderColor: BOARD_SAGE,
            backgroundColor: "rgba(224,214,194,0.12)",
            borderWidth: 2,
            pointBackgroundColor: BOARD_SAGE,
            pointRadius: 4,
          },
          {
            label: "Morphy",
            data: morphyData,
            borderColor: SIGNAL_GREEN,
            backgroundColor: "rgba(34,197,94,0.08)",
            borderWidth: 2,
            borderDash: [4, 3],
            pointBackgroundColor: SIGNAL_GREEN,
            pointRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              afterLabel: (ctx) => AXIS_HELP[ctx.label] ?? "",
            },
          },
        },
        scales: {
          r: {
            min: 0,
            max: 100,
            ticks: { display: false },
            pointLabels: { color: "rgba(250,250,250,0.55)", font: { size: 11, family: "DM Mono" } },
            grid: { color: "rgba(255,255,255,0.08)" },
            angleLines: { color: "rgba(255,255,255,0.08)" },
          },
        },
      },
    });

    return () => radarChart.current?.destroy();
  }, [style]);

  async function askRecommendations() {
    if (!style) return;
    setRecoLoading(true);
    setReco(null);
    const gaps = ["Development", "Open files", "King attack", "Sacrifices", "Aggression"]
      .map((label, i) => {
        const keys = ["development", "open_files", "king_attack", "sacrifice_rate", "aggression"];
        const you = style.you[keys[i]];
        const ref = style.morphy[keys[i]];
        return `${label}: you ${you} vs Morphy ${ref}`;
      })
      .join("; ");
    try {
      const text = await sendCoachMessage(
        username,
        `Compare my style to Paul Morphy. Radar gaps: ${gaps}. ` +
        `In 3 bullet points, tell me what to practice to close the biggest style gaps. Be specific.`,
      );
      setReco(text);
    } catch (err) {
      setReco(`Coach unavailable: ${err.message}`);
    } finally {
      setRecoLoading(false);
    }
  }

  if (error) return <div className="error">Failed to load style data: {error.message}</div>;
  if (!style) return <div className="loading">Loading style comparison…</div>;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-title">Style gap — Paul Morphy</div>
          <div className="page-sub">your play vs. Morphy&apos;s historical fingerprint</div>
        </div>
        <RecommendButton onClick={askRecommendations} loading={recoLoading} label="Give me recommendations" />
      </div>

      {reco && (
        <div className="card ai-insight-card">
          <span className="ai-tip-badge">AI insight</span>
          <p className="ai-summary-text">{reco}</p>
          {onNavigateCoach && (
            <button type="button" className="link-btn" onClick={() => onNavigateCoach(reco)}>
              Continue in Coach →
            </button>
          )}
        </div>
      )}

      <div className="card">
        <div className="card-title">Style comparison</div>
        <div className="gm-compare">
          <div className="gm-col">
            <div className="gm-header">You ({username})</div>
            {Object.entries(style.stats.you).map(([key, val]) => (
              <div className="stat-row" key={key}>
                <span className="stat-name">{STAT_LABELS[key] ?? key}</span>
                <span className={`stat-val ${isGoodForYou(key, val, style.stats.morphy[key]) ?? ""}`}>{val}</span>
              </div>
            ))}
          </div>
          <div className="gm-col">
            <div className="gm-header">Paul Morphy (historical)</div>
            {Object.entries(style.stats.morphy).map(([key, val]) => (
              <div className="stat-row" key={key}>
                <span className="stat-name">{STAT_LABELS[key] ?? key}</span>
                <span className="stat-val good">{val}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card radar-card">
        <div className="card-title">
          Style radar
          <div className="radar-legend">
            <span><i className="legend-swatch" style={{ background: BOARD_SAGE }} /> You</span>
            <span><i className="legend-swatch legend-swatch-dashed" style={{ background: SIGNAL_GREEN }} /> Morphy</span>
          </div>
        </div>
        <p className="radar-hint">
          Hover each axis for what it measures.{" "}
          <AiTooltip label="Why Morphy?">
            Paul Morphy is the namesake — a 19th-century genius known for rapid development, open games, and ruthless attacks.
            This radar is illustrative until full GM corpus analysis ships.
          </AiTooltip>
        </p>
        <div className="chart-wrap" style={{ height: 280 }}>
          <canvas ref={radarRef} role="img" aria-label="Radar chart comparing your chess style to Paul Morphy" />
        </div>
      </div>
    </div>
  );
}

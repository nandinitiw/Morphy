const OPTIONS = [
  { id: "all", label: "All", sub: "every time control" },
  { id: "bullet", label: "Bullet", sub: "< 3 min" },
  { id: "blitz", label: "Blitz", sub: "3–10 min" },
  { id: "rapid", label: "Rapid", sub: "10–30 min" },
  { id: "classical", label: "Classical", sub: "30+ min" },
];

export default function TimeControlFilter({ value, onChange, counts = {} }) {
  return (
    <div className="tc-filter" role="group" aria-label="Filter by time control">
      {OPTIONS.map((opt) => {
        const count = opt.id === "all"
          ? Object.values(counts).reduce((sum, n) => sum + n, 0)
          : counts[opt.id] ?? 0;
        return (
          <button
            key={opt.id}
            type="button"
            className={`tc-chip ${value === opt.id ? "active" : ""}`}
            onClick={() => onChange(opt.id)}
          >
            <span className="tc-chip-label">{opt.label}</span>
            <span className="tc-chip-sub">{opt.sub}</span>
            {count > 0 && <span className="tc-chip-count">{count}</span>}
          </button>
        );
      })}
    </div>
  );
}

export default function RecommendButton({ onClick, loading, label = "Give me recommendations" }) {
  return (
    <button type="button" className="ai-recommend-btn" onClick={onClick} disabled={loading}>
      <i className="ti ti-sparkles" aria-hidden="true" />
      {loading ? "Asking coach…" : label}
    </button>
  );
}

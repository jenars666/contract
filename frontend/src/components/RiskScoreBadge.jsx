export default function RiskScoreBadge({ score, label = "Risk Score" }) {
  const normalized = Math.max(0, Math.min(100, score));
  const circumference = 2 * Math.PI * 52;
  const offset = circumference - (normalized / 100) * circumference;

  const color = normalized > 70 ? "#f85149" : normalized > 40 ? "#d29922" : "#3fb950";

  return (
    <div className="card gauge-card fade-in">
      <svg className="gauge" viewBox="0 0 140 140" role="img" aria-label={`${label}: ${normalized}`}>
        <circle className="gauge-bg" cx="70" cy="70" r="52" />
        <circle
          className="gauge-fg"
          cx="70"
          cy="70"
          r="52"
          stroke={color}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="gauge-center">
        <div className="gauge-score" style={{ color }}>
          {normalized}
        </div>
        <div className="gauge-sub">/100</div>
      </div>
      <div className="gauge-label">{label}</div>
    </div>
  );
}

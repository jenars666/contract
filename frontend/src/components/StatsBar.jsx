export default function StatsBar({
  analysisTime,
  vulnerabilityCount,
  criticalCount,
  highCount,
  mediumCount,
  lowCount,
}) {
  if (!vulnerabilityCount) return null;

  return (
    <div className="card stats-bar fade-in">
      <span>Analyzed in {analysisTime.toFixed(2)}s</span>
      <span>|</span>
      <span>{vulnerabilityCount} vulnerabilities</span>
      <span>|</span>
      <span className="c-critical">{criticalCount} CRITICAL</span>
      <span className="c-high">{highCount} HIGH</span>
      <span className="c-medium">{mediumCount} MEDIUM</span>
      <span className="c-low">{lowCount} LOW</span>
    </div>
  );
}

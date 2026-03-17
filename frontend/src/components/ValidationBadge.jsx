export default function ValidationBadge({ validation }) {
  if (!validation) return null;

  const maps = {
    VERIFIED_SAFE: {
      icon: "✔",
      title: "VERIFIED SAFE",
      text: "All vulnerabilities patched. Safe to deploy.",
      cls: "valid-ok",
    },
    IMPROVED: {
      icon: "✓",
      title: "PARTIALLY FIXED",
      text: `${Math.max(validation.original_count - validation.patched_count, 0)} of ${validation.original_count} vulnerabilities fixed.`,
      cls: "valid-warn",
    },
    FAILED: {
      icon: "✖",
      title: "PATCH FAILED",
      text: "Vulnerabilities remain. Manual review needed.",
      cls: "valid-bad",
    },
    NEW_ISSUES: {
      icon: "⚠",
      title: "NEW ISSUES FOUND",
      text: "Patch introduced new vulnerabilities.",
      cls: "valid-bad",
    },
  };

  const current = maps[validation.status] || maps.FAILED;

  return (
    <section className={`card validation ${current.cls} fade-in`}>
      <div className="validation-title">
        <span>{current.icon}</span>
        <strong>{current.title}</strong>
      </div>
      <p>{current.text}</p>
      <p>
        Risk score: <span className="risk-before">{validation.risk_score_before}</span> →{" "}
        <span className="risk-after">{validation.risk_score_after}</span>
      </p>
    </section>
  );
}

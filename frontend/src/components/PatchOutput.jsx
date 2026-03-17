import { useState } from "react";

export default function PatchOutput({ patchedCode, isLoading, githubPushed, githubUrl }) {
  const [copied, setCopied] = useState(false);

  const lineCount = patchedCode ? patchedCode.split("\n").length : 0;
  const wordCount = patchedCode ? patchedCode.trim().split(/\s+/).filter(Boolean).length : 0;

  async function handleCopy() {
    if (!patchedCode) return;
    await navigator.clipboard.writeText(patchedCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleExport() {
    if (!patchedCode) return;
    const blob = new Blob([patchedCode], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "patched_contract.sol";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className={`panel-card${githubPushed ? " panel-pushed" : ""}`}>
      {/* Header */}
      <div className="panel-header">
        <div className="panel-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="panel-icon accent">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
          <span className="panel-label">Patched Output</span>
          <span className="word-count">{wordCount} words</span>
        </div>
        {githubPushed && (
          <a
            href={githubUrl}
            target="_blank"
            rel="noreferrer"
            className="github-pushed-badge"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            Pushed to GitHub
          </a>
        )}
      </div>

      {/* Output area */}
      <div className="output-area">
        {isLoading ? (
          <div className="output-loading">
            <div className="pulse-dots">
              <span /><span /><span />
            </div>
            <p>Deep Semantic Audit in progress…</p>
          </div>
        ) : patchedCode ? (
          <pre className="output-code">{patchedCode}</pre>
        ) : (
          <p className="output-placeholder">Patched output will appear here…</p>
        )}
      </div>

      {/* Footer actions */}
      <div className="panel-footer">
        <span className="char-info">
          {patchedCode ? `${lineCount} lines` : ""}
        </span>
        <div className="action-buttons">
          <button
            className="action-btn"
            onClick={handleExport}
            disabled={!patchedCode}
            title="Export as .sol file"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Export
          </button>
          <button
            className="action-btn"
            onClick={handleCopy}
            disabled={!patchedCode}
            title="Copy to clipboard"
          >
            {copied ? (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                Copied!
              </>
            ) : (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                </svg>
                Copy Text
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

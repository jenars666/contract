import { useMemo, useState } from "react";

function makeRows(originalCode, patchedCode) {
  const original = originalCode.split("\n");
  const patched = patchedCode.split("\n");
  const len = Math.max(original.length, patched.length);
  const rows = [];

  for (let index = 0; index < len; index += 1) {
    const left = original[index] ?? "";
    const right = patched[index] ?? "";

    let leftState = "same";
    let rightState = "same";

    if (left && !right) {
      leftState = "removed";
    } else if (!left && right) {
      rightState = "added";
    } else if (left !== right) {
      leftState = "removed";
      rightState = "added";
    }

    rows.push({ line: index + 1, left, right, leftState, rightState });
  }

  return rows;
}

export default function DiffViewer({ originalCode, patchedCode, isVisible }) {
  const [copied, setCopied] = useState("");
  const rows = useMemo(() => makeRows(originalCode, patchedCode), [originalCode, patchedCode]);

  const changes = rows.filter((r) => r.leftState !== "same" || r.rightState !== "same").length;
  if (!isVisible) return null;

  async function copyText(code, key) {
    await navigator.clipboard.writeText(code);
    setCopied(key);
    setTimeout(() => setCopied(""), 2000);
  }

  function downloadPatched() {
    const blob = new Blob([patchedCode], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "contract_patched.sol";
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <section className="card diff-viewer fade-slide-in">
      <div className="diff-grid">
        <div className="diff-panel">
          <div className="diff-header">
            <span className="dot red" /> Original (Vulnerable)
            <button className="btn-ghost" onClick={() => copyText(originalCode, "left")}>
              {copied === "left" ? "Copied!" : "Copy"}
            </button>
          </div>
          <div className="code-table">
            {rows.map((row) => (
              <div key={`left-${row.line}`} className={`code-row ${row.leftState}`}>
                <span className="ln">{row.line}</span>
                <span className="code">{row.left || " "}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="diff-panel">
          <div className="diff-header">
            <span className="dot green" /> Patched (Secure)
            <button className="btn-ghost" onClick={() => copyText(patchedCode, "right")}>
              {copied === "right" ? "Copied!" : "Copy"}
            </button>
          </div>
          <div className="code-table">
            {rows.map((row) => (
              <div key={`right-${row.line}`} className={`code-row ${row.rightState}`}>
                <span className="ln">{row.line}</span>
                <span className="code">{row.right || " "}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="diff-footer">
        <span>{changes} lines changed</span>
        <button className="btn-primary" onClick={downloadPatched}>
          Download Patched Contract
        </button>
      </div>
    </section>
  );
}

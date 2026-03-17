import { useState } from "react";
import { analyzeContract, generatePatch } from "./api/client";
import Navbar from "./components/Navbar";
import PatchOutput from "./components/PatchOutput";
import ProgressStepper from "./components/ProgressStepper";
import VulnerabilityList from "./components/VulnerabilityList";
import Editor from "@monaco-editor/react";

const REENTRANCY_DEMO = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract VulnerableBank {
    mapping(address => uint256) public balances;
    address public admin;

    constructor() {
        admin = msg.sender;
    }

    function deposit() external payable {
        require(msg.value > 0, "zero value");
        balances[msg.sender] += msg.value;
    }

    function withdraw(uint256 amount) external {
        require(amount > 0, "amount is zero");
        require(balances[msg.sender] >= amount, "insufficient balance");

        // VULNERABILITY: external interaction before effects
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok, "transfer failed");

        balances[msg.sender] -= amount;
    }

    receive() external payable {}
}`;

const OVERFLOW_DEMO = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract VulnerableToken {
    uint256 public totalSupply;
    mapping(address => uint256) private balances;

    constructor(uint256 supply) {
        totalSupply = supply;
        balances[msg.sender] = supply;
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        unchecked {
            balances[msg.sender] = balances[msg.sender] - amount;
            balances[to] = balances[to] + amount;
        }
        return true;
    }

    function mint(address to, uint256 amount) external {
        unchecked {
            totalSupply += amount;
            balances[to] += amount;
        }
    }
}`;

const TXORIGIN_DEMO = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract VulnerableWallet {
    address public owner;

    constructor() payable {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(tx.origin == owner, "only owner");
        _;
    }

    function withdraw(uint256 amount) external onlyOwner {
        require(amount <= address(this).balance, "low balance");
        (bool ok, ) = payable(msg.sender).call{value: amount}("");
        require(ok, "withdraw failed");
    }

    receive() external payable {}
}`;

export default function App() {
  const [code, setCode] = useState("");
  const [patchedCode, setPatchedCode] = useState("");
  const [vulnerabilities, setVulnerabilities] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState("");
  const [currentStep, setCurrentStep] = useState(1);
  const [githubPushed, setGithubPushed] = useState(false);
  const [githubUrl, setGithubUrl] = useState("");

  const wordCount = code.trim() ? code.trim().split(/\s+/).length : 0;

  async function handleAnalyse() {
    if (!code.trim() || isProcessing) return;
    setIsProcessing(true);
    setError("");
    setPatchedCode("");
    setCurrentStep(2);

    try {
      const analysisResult = await analyzeContract(code);
      const vulns = analysisResult.vulnerabilities || [];
      setVulnerabilities(vulns);

      setCurrentStep(3);

      const patchResult = await generatePatch(code, vulns);
      const newPatchedCode = patchResult.patched_code || "// No changes needed.";
      setPatchedCode(newPatchedCode);
      setGithubPushed(patchResult.github_pushed || false);
      setGithubUrl(patchResult.github_url || "");
      setCurrentStep(patchResult.github_pushed ? 7 : 5);
    } catch (err) {
      setError(err.message || "Analysis failed. Please try again.");
      setCurrentStep(1);
    } finally {
      setIsProcessing(false);
    }
  }

  function handleClear() {
    setCode("");
    setPatchedCode("");
    setVulnerabilities([]);
    setError("");
    setCurrentStep(1);
    setGithubPushed(false);
    setGithubUrl("");
  }

  return (
    <div className="app-shell">
      <Navbar />
      
      <ProgressStepper currentStep={currentStep} />

      {error && (
        <div className="error-banner">
          <span>⚠ {error}</span>
          <button className="dismiss-btn" onClick={() => setError("")}>✕</button>
        </div>
      )}

      <main className="converter-grid">
        {/* ── LEFT: INPUT PANEL ── */}
        <div className="panel-card">
          <div className="panel-header">
            <div className="panel-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="panel-icon">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <line x1="10" y1="9" x2="8" y2="9"/>
              </svg>
              <span className="panel-label">Buggy Contract</span>
              <span className="word-count">{wordCount} words</span>
            </div>
            <button className="clear-btn" onClick={handleClear} title="Clear input">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6l-1 14H6L5 6"/>
                <path d="M10 11v6M14 11v6"/>
                <path d="M9 6V4h6v2"/>
              </svg>
              Clear
            </button>
          </div>

          <div className="editor-wrapper">
            <Editor
              language="sol"
              theme="vs-dark"
              value={code}
              onChange={(val) => setCode(val || "")}
              options={{
                fontSize: 13,
                minimap: { enabled: false },
                wordWrap: "on",
                lineNumbers: "on",
                scrollBeyondLastLine: false,
                padding: { top: 12, bottom: 12 },
              }}
            />
          </div>

          <div className="panel-footer">
            <button
              id="analyse-btn"
              className={`analyse-btn${isProcessing ? " loading" : ""}`}
              disabled={!code.trim() || isProcessing}
              onClick={handleAnalyse}
            >
              {isProcessing ? (
                <>
                  <span className="spinner" />
                  Deep Scanning…
                </>
              ) : (
                <>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="11" cy="11" r="8"/>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  </svg>
                  Analyse
                </>
              )}
            </button>
          </div>
        </div>

        {/* ── RIGHT: OUTPUT PANEL ── */}
        <PatchOutput 
          patchedCode={patchedCode} 
          isLoading={isProcessing}
          githubPushed={githubPushed}
          githubUrl={githubUrl}
        />
      </main>

      {vulnerabilities.length > 0 && (
        <VulnerabilityList 
          vulnerabilities={vulnerabilities} 
          onPatchAll={() => {}} 
          isPatching={isProcessing} 
        />
      )}
    </div>
  );
}

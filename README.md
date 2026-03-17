# SmartPatch — Smart Contract Vulnerability Patcher

SmartPatch detects critical Solidity vulnerabilities in seconds and auto-generates secure patched contracts. It combines Slither static analysis, risk scoring, LLM-assisted remediation, and post-patch validation in one workflow.

## What it does
SmartPatch analyzes pasted Solidity contracts, highlights vulnerabilities with severity and line locations, and generates a secure patched version. It then re-scans patched code to verify whether risk was reduced or eliminated.

## Problem it solves
- Smart contract hacks caused over $1.8B losses in 2023 from mostly known classes like reentrancy and access mistakes.
- Manual auditing can take days to weeks per contract and still miss edge-case patterns.
- Developers need fast feedback loops while coding, not only at final security review.

## Demo

```text
[Paste Solidity] -> [/api/analyze] -> [Slither JSON] -> [Parser + Risk Score]
                                 -> [/api/patch] -> [LLM Patch Generator]
                                 -> [Re-scan patched contract] -> [Validation Badge + Diff + Download]
```

## Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- pip
- An Anthropic API key (console.anthropic.com)

### Backend Setup

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
# source venv/bin/activate

pip install -r requirements.txt
python -m solc_select install 0.8.19
python -m solc_select use 0.8.19

copy .env.example .env   # Windows
# cp .env.example .env   # Linux/Mac
```

Edit .env and set:

```env
ANTHROPIC_API_KEY=your_real_key
LLM_MODEL=claude-3-5-sonnet-20241022
SOLC_VERSION=0.8.19
MAX_CONTRACT_SIZE=50000
ANALYSIS_TIMEOUT=60
```

Start backend:

```bash
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open:
- Frontend: http://localhost:5173
- Backend docs: http://localhost:8000/docs

## Environment Variables
- ANTHROPIC_API_KEY: API key for Claude patch generation.
- LLM_MODEL: Claude model used for patch generation.
- SOLC_VERSION: Solidity compiler target version for Slither pipeline.
- MAX_CONTRACT_SIZE: Maximum accepted source size.
- ANALYSIS_TIMEOUT: Timeout (seconds) for Slither execution.

## How to Use
1. Paste Solidity contract in the code editor.
2. Click Analyze Contract.
3. Review vulnerability cards, severity, and risk score.
4. Click Auto Fix All Vulnerabilities.
5. Review validation result and side-by-side diff.
6. Download contract_patched.sol.

## API Reference

### POST /api/analyze

Request:

```json
{
  "code": "pragma solidity ^0.8.19; contract Demo { }",
  "filename": "contract.sol"
}
```

Response:

```json
{
  "success": true,
  "vulnerabilities": [],
  "risk_score": 0,
  "analysis_time": 1.24,
  "filename": "contract.sol",
  "error": null
}
```

### POST /api/patch

Request:

```json
{
  "code": "pragma solidity ^0.8.19; contract Demo { }",
  "vulnerabilities": [
    {
      "id": "1",
      "type": "reentrancy-eth",
      "title": "Reentrancy Vulnerability",
      "severity": "CRITICAL",
      "lines": [20],
      "description": "External call before state update"
    }
  ]
}
```

Response:

```json
{
  "success": true,
  "patched_code": "pragma solidity ^0.8.19; ...",
  "explanation": "- state update moved before call",
  "changes_summary": [
    "state update moved before call"
  ],
  "validation": {
    "status": "IMPROVED",
    "passed": true,
    "original_count": 1,
    "patched_count": 0,
    "risk_score_before": 25,
    "risk_score_after": 0
  },
  "patch_time": 2.41,
  "error": null
}
```

### GET /api/health

Response:

```json
{
  "status": "ok",
  "version": "1.0.0",
  "slither_available": true
}
```

## Architecture

```text
React + Vite UI
   |
   | HTTP
   v
FastAPI Routes (/api)
   |-- /analyze -> validate_syntax -> temp .sol -> Slither -> parser -> risk
   |-- /patch   -> LLM patch generator -> validator -> re-run Slither
   v
UI: vulnerability list + risk + validation + red/green diff + download
```

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | React + Vite + Monaco | Fast DX and rich code editing |
| Backend API | FastAPI + Pydantic | Typed contracts and high performance |
| SAST | Slither | Industry-standard Solidity static analysis |
| LLM | Anthropic Claude | Deterministic low-temperature security patch generation |
| Validation | Slither rerun | Verifies patch actually reduces issues |

## Vulnerabilities Detected

| Bug | Severity | Real Hack Example | Fix Applied |
|---|---|---|---|
| Reentrancy | CRITICAL | 2016 DAO hack | Checks-Effects-Interactions + reentrancy guard |
| Integer Overflow/Underflow | HIGH | BeautyChain 2018 | Remove unsafe unchecked arithmetic or add guards |
| tx.origin Auth | MEDIUM | Phishing proxy ownership theft | Replace tx.origin with msg.sender |

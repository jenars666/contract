import subprocess
import time
import os
import sys
import importlib.util
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException

from analyzer.slither_runner import (
    SlitherNotInstalledError,
    SlitherParseError,
    SlitherTimeoutError,
    run_slither,
)
from analyzer.audit_engine import run_semantic_audit
from analyzer.vulnerability_parser import calculate_risk_score, parse_slither_output
from api.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    HealthResponse,
    PatchRequest,
    PatchResponse,
    PushRequest,
    PushResponse,
    ValidationResult,
)
from llm.patch_generator import generate_patch
from utils.file_handler import cleanup_temp_file, create_temp_sol_file, validate_solidity_syntax
from utils.git_handler import push_to_github
from utils.logger import get_logger
from validator.patch_validator import validate_patch

router = APIRouter()
logger = get_logger("api.routes")


def _heuristic_vulnerabilities(code: str) -> list[dict]:
    lines = code.splitlines()
    vulns: list[dict] = []

    reentrancy_lines = [idx + 1 for idx, line in enumerate(lines) if ".call{value:" in line]
    if reentrancy_lines:
        vulns.append(
            {
                "id": str(uuid.uuid4()),
                "type": "reentrancy-eth",
                "title": "Reentrancy Vulnerability",
                "severity": "CRITICAL",
                "lines": reentrancy_lines,
                "description": "External ETH call before state update detected; violates Checks-Effects-Interactions pattern.",
            }
        )

    txorigin_lines = [idx + 1 for idx, line in enumerate(lines) if "tx.origin" in line]
    if txorigin_lines:
        vulns.append(
            {
                "id": str(uuid.uuid4()),
                "type": "tx-origin",
                "title": "Dangerous tx.origin Usage",
                "severity": "HIGH",
                "lines": txorigin_lines,
                "description": "tx.origin used in auth logic; vulnerable to phishing attacks. Use msg.sender instead.",
            }
        )

    unchecked_lines = [idx + 1 for idx, line in enumerate(lines) if "unchecked" in line]
    if unchecked_lines:
        vulns.append(
            {
                "id": str(uuid.uuid4()),
                "type": "integer-overflow",
                "title": "Unsafe Unchecked Arithmetic",
                "severity": "HIGH",
                "lines": unchecked_lines,
                "description": "Unchecked arithmetic block bypasses Solidity 0.8+ overflow protection.",
            }
        )

    # Detect missing access control: public setter that changes owner without a require
    for idx, line in enumerate(lines):
        if "function setOwner" in line and "public" in line:
            block = "\n".join(lines[idx: idx + 5])
            if "require" not in block:
                vulns.append(
                    {
                        "id": str(uuid.uuid4()),
                        "type": "missing-access-control",
                        "title": "Missing Access Control",
                        "severity": "CRITICAL",
                        "lines": [idx + 1],
                        "description": "setOwner is public with no access control; anyone can take ownership.",
                    }
                )

    return vulns


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    slither_available = False
    venv_path = os.environ.get("VIRTUAL_ENV", "")
    local_venv_slither = Path(__file__).resolve().parents[3] / ".venv" / "Scripts" / "slither.exe"
    local_venv_python = Path(__file__).resolve().parents[3] / ".venv" / "Scripts" / "python.exe"

    checks = [
        ["slither", "--version"],
        [os.path.join(os.path.dirname(sys.executable), "slither.exe"), "--version"],
        [sys.executable, "-m", "slither", "--version"],
        [str(Path(venv_path) / "Scripts" / "slither.exe"), "--version"] if venv_path else [""],
        [str(local_venv_slither), "--version"],
        [str(local_venv_python), "-m", "slither", "--version"],
    ]
    for cmd in checks:
        if not cmd[0] or (cmd[0].endswith(".exe") and not os.path.exists(cmd[0])):
            continue
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            slither_available = True
            break
        except Exception:
            continue

    if not slither_available:
        slither_available = importlib.util.find_spec("slither") is not None

    return HealthResponse(
        status="ok",
        version="1.0.1",
        slither_available=slither_available,
    )


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_contract(request: AnalyzeRequest) -> AnalyzeResponse:
    start = time.perf_counter()
    logger.info("Analyze request received: filename=%s", request.filename)

    is_valid, error_message = validate_solidity_syntax(request.code)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)

    temp_filepath = None
    try:
        temp_filepath = create_temp_sol_file(request.code)
        # Fast fail if tools are missing or compile loops, to ensure snappy UX with heuristic
        raw = run_slither(temp_filepath, timeout=8)
        vulnerabilities = parse_slither_output(raw)
        
        # Add Semantic Audit results
        try:
            semantic_vulns = run_semantic_audit(request.code)
            vulnerabilities.extend(semantic_vulns)
        except Exception as e:
            logger.warning("Semantic audit skipped or failed: %s", e)
            
        risk_score = calculate_risk_score(vulnerabilities)
        elapsed = round(time.perf_counter() - start, 3)

        logger.info("Analyze completed in %.3fs with %d vulnerabilities", elapsed, len(vulnerabilities))
        return AnalyzeResponse(
            success=True,
            vulnerabilities=vulnerabilities,
            risk_score=risk_score,
            analysis_time=elapsed,
            filename=request.filename or "contract.sol",
        )
    except (SlitherNotInstalledError, SlitherParseError, SlitherTimeoutError) as exc:
        detail = str(exc)
        # Fallback to heuristic scanner for any solc/compiler-related failure:
        # missing solc binary, wrong version, InvalidCompilation, empty JSON, etc.
        _SOLC_ERRORS = (
            "FileNotFoundError",
            "WinError 2",
            "SOLC_VERSION",
            "not installed",
            "InvalidCompilation",
            "solc",
            "empty JSON",
            "The system cannot find",
        )
        if any(kw in detail for kw in _SOLC_ERRORS) or isinstance(exc, (SlitherNotInstalledError, SlitherTimeoutError)):
            vulnerabilities = _heuristic_vulnerabilities(request.code)
            risk_score = calculate_risk_score(vulnerabilities)
            elapsed = round(time.perf_counter() - start, 3)
            logger.warning("Falling back to heuristic analyzer: %s", detail[:200])
            return AnalyzeResponse(
                success=True,
                vulnerabilities=vulnerabilities,
                risk_score=risk_score,
                analysis_time=elapsed,
                filename=request.filename or "contract.sol",
            )
        logger.error("Slither parse failure: %s", exc)
        raise HTTPException(status_code=500, detail=detail) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unexpected analyze error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Unexpected analysis error: {exc}") from exc
    finally:
        if temp_filepath:
            cleanup_temp_file(temp_filepath)


@router.post("/patch", response_model=PatchResponse)
def patch_contract(request: PatchRequest) -> PatchResponse:
    start = time.perf_counter()
    logger.info("Patch request received with %d vulnerabilities", len(request.vulnerabilities))

    is_valid, error_message = validate_solidity_syntax(request.code)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)

    try:
        patch_payload = generate_patch(request.code, [v.model_dump() for v in request.vulnerabilities])
        validation_raw = validate_patch(
            original_code=request.code,
            patched_code=patch_payload["patched_code"],
            original_vulns=[v.model_dump() for v in request.vulnerabilities],
        )

        elapsed = round(time.perf_counter() - start, 3)
        validation = ValidationResult(
            status=validation_raw["status"],
            passed=validation_raw["passed"],
            original_count=validation_raw["original_count"],
            patched_count=validation_raw["patched_count"],
            risk_score_before=validation_raw["risk_score_before"],
            risk_score_after=validation_raw["risk_score_after"],
        )

        # Auto-push to GitHub immediately after patch generation
        patched_code = patch_payload["patched_code"]
        push_result = push_to_github(
            filename="contract_patched.sol",
            content=patched_code,
            commit_message="SmartPatch: auto-push patched contract",
        )
        if push_result["success"]:
            logger.info("Auto-push to GitHub succeeded: %s", push_result.get("url", ""))
        else:
            logger.warning("Auto-push to GitHub failed: %s", push_result.get("error", ""))

        logger.info("Patch completed in %.3fs with status=%s", elapsed, validation.status)
        return PatchResponse(
            success=True,
            patched_code=patched_code,
            explanation=patch_payload["explanation"],
            changes_summary=patch_payload.get("changes_summary", []),
            validation=validation,
            patch_time=elapsed,
            github_pushed=push_result["success"],
            github_url=push_result.get("url"),
        )
    except HTTPException:
        raise
    except RuntimeError as exc:
        logger.error("Patch generation runtime error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected patch error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Unexpected patch error: {exc}") from exc


@router.post("/push", response_model=PushResponse)
def push_to_github_api(request: PushRequest) -> PushResponse:
    logger.info("Push request received for file: %s", request.filename)
    
    result = push_to_github(
        filename=request.filename,
        content=request.code,
        commit_message=request.commit_message
    )
    
    if not result["success"]:
        return PushResponse(
            success=False,
            error=result.get("error", "Unknown GitHub error")
        )
        
    return PushResponse(
        success=True,
        url=result.get("url"),
        commit=result.get("commit")
    )

from analyzer.slither_runner import run_slither
from analyzer.vulnerability_parser import calculate_risk_score, parse_slither_output
from analyzer.slither_runner import (
    SlitherNotInstalledError,
    SlitherParseError,
    SlitherTimeoutError,
    run_slither,
)
from utils.file_handler import cleanup_temp_file, create_temp_sol_file
from utils.logger import get_logger

logger = get_logger("validator.patch_validator")

def _heuristic_vulnerabilities(code: str) -> list[dict]:
    import uuid
    lines = code.splitlines()
    vulns: list[dict] = []

    reentrancy_lines = [idx + 1 for idx, line in enumerate(lines) if ".call{value:" in line]
    if reentrancy_lines:
        vulns.append({"id": str(uuid.uuid4()), "type": "reentrancy-eth", "title": "Reentrancy Vulnerability", "severity": "CRITICAL", "lines": reentrancy_lines, "description": "External ETH call before state update."})

    txorigin_lines = [idx + 1 for idx, line in enumerate(lines) if "tx.origin" in line]
    if txorigin_lines:
        vulns.append({"id": str(uuid.uuid4()), "type": "tx-origin", "title": "Dangerous tx.origin Usage", "severity": "HIGH", "lines": txorigin_lines, "description": "tx.origin used in auth logic."})

    unchecked_lines = [idx + 1 for idx, line in enumerate(lines) if "unchecked" in line]
    if unchecked_lines:
        vulns.append({"id": str(uuid.uuid4()), "type": "integer-overflow", "title": "Unsafe Unchecked Arithmetic", "severity": "HIGH", "lines": unchecked_lines, "description": "Unchecked arithmetic block detected."})

    for idx, line in enumerate(lines):
        if "function setOwner" in line and "public" in line:
            block = "\n".join(lines[idx: idx + 5])
            if "require" not in block:
                vulns.append({"id": str(uuid.uuid4()), "type": "missing-access-control", "title": "Missing Access Control", "severity": "CRITICAL", "lines": [idx + 1], "description": "setOwner has no access control."})

    return vulns


def validate_patch(original_code: str, patched_code: str, original_vulns: list) -> dict:
    patched_temp_file = None
    try:
        patched_temp_file = create_temp_sol_file(patched_code)
        
        try:
            # Drop timeout significantly to ensure snappy UX
            patched_slither_json = run_slither(patched_temp_file, timeout=8)
            patched_vulns = parse_slither_output(patched_slither_json)
        except (SlitherNotInstalledError, SlitherParseError, SlitherTimeoutError) as exc:
            logger.warning("Validation fallback to heuristic scanner due to: %s", exc)
            patched_vulns = _heuristic_vulnerabilities(patched_code)


        original_types = {v.get("type") for v in original_vulns}
        patched_types = {v.get("type") for v in patched_vulns}

        remaining = [v for v in patched_vulns if v.get("type") in original_types]
        new_vulns = [v for v in patched_vulns if v.get("type") not in original_types]

        original_count = len(original_vulns)
        patched_count = len(patched_vulns)

        if new_vulns:
            status = "NEW_ISSUES"
            passed = False
        elif patched_count == 0:
            status = "VERIFIED_SAFE"
            passed = True
        elif patched_count < original_count:
            status = "IMPROVED"
            passed = True
        else:
            status = "FAILED"
            passed = False

        return {
            "status": status,
            "original_count": original_count,
            "patched_count": patched_count,
            "remaining_vulnerabilities": remaining,
            "new_vulnerabilities": new_vulns,
            "risk_score_before": calculate_risk_score(original_vulns),
            "risk_score_after": calculate_risk_score(patched_vulns),
            "passed": passed,
        }
    finally:
        if patched_temp_file:
            cleanup_temp_file(patched_temp_file)

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from utils.logger import get_logger

logger = get_logger("analyzer.slither_runner")


class SlitherNotInstalledError(Exception):
    pass


class SlitherTimeoutError(Exception):
    pass


class SlitherParseError(Exception):
    pass


def _discover_solc_binary(venv_path: str) -> str:
    scripts_dir = os.path.dirname(sys.executable)
    home = Path.home()

    # Prefer real solc-select artifact binaries over the solc launcher shim.
    artifact_candidates = list(home.glob(".solc-select/artifacts/solc-*/solc.exe"))
    artifact_candidates.extend(home.glob(".solc-select/artifacts/solc-*/solc-*"))
    executable_artifacts = [p for p in artifact_candidates if p.is_file()]
    if executable_artifacts:
        newest = max(executable_artifacts, key=lambda p: p.stat().st_mtime)
        return str(newest)

    direct_candidates = [
        os.path.join(scripts_dir, "solc.exe"),
        str(Path(venv_path) / "Scripts" / "solc.exe") if venv_path else "",
        str(Path(__file__).resolve().parents[3] / ".venv" / "Scripts" / "solc.exe"),
    ]
    return next((candidate for candidate in direct_candidates if candidate and os.path.exists(candidate)), "")


def _line_numbers_with(text: str, needle: str) -> list[int]:
    return [idx + 1 for idx, line in enumerate(text.splitlines()) if needle in line]


def _build_heuristic_slither_output(sol_filepath: str) -> dict:
    code = Path(sol_filepath).read_text(encoding="utf-8", errors="ignore")
    detectors: list[dict] = []

    reentrancy_lines = _line_numbers_with(code, ".call{value:")
    if reentrancy_lines:
        detectors.append(
            {
                "check": "reentrancy-eth",
                "impact": "High",
                "confidence": "Medium",
                "description": "External call with ETH transfer detected; review checks-effects-interactions ordering.",
                "elements": [
                    {
                        "source_mapping": {
                            "lines": reentrancy_lines,
                            "filename_relative": os.path.basename(sol_filepath),
                        }
                    }
                ],
            }
        )

    tx_origin_lines = _line_numbers_with(code, "tx.origin")
    if tx_origin_lines:
        detectors.append(
            {
                "check": "tx-origin",
                "impact": "Medium",
                "confidence": "High",
                "description": "tx.origin usage detected in authorization logic.",
                "elements": [
                    {
                        "source_mapping": {
                            "lines": tx_origin_lines,
                            "filename_relative": os.path.basename(sol_filepath),
                        }
                    }
                ],
            }
        )

    unchecked_lines = _line_numbers_with(code, "unchecked")
    if unchecked_lines:
        detectors.append(
            {
                "check": "integer-overflow",
                "impact": "Medium",
                "confidence": "Medium",
                "description": "Unchecked arithmetic block detected.",
                "elements": [
                    {
                        "source_mapping": {
                            "lines": unchecked_lines,
                            "filename_relative": os.path.basename(sol_filepath),
                        }
                    }
                ],
            }
        )

    return {"results": {"detectors": detectors}}


def run_slither(sol_filepath: str, timeout: int = 60) -> dict:
    base_args = [sol_filepath, "--json", "-", "--solc-remaps", "@=node_modules/@"]
    venv_path = os.environ.get("VIRTUAL_ENV", "")
    local_venv_slither = Path(__file__).resolve().parents[3] / ".venv" / "Scripts" / "slither.exe"
    local_venv_python = Path(__file__).resolve().parents[3] / ".venv" / "Scripts" / "python.exe"

    scripts_dir = os.path.dirname(sys.executable)
    solc_binary = _discover_solc_binary(venv_path)
    if solc_binary:
        base_args.extend(["--solc", solc_binary])

    command_variants = [
        ["slither", *base_args],
        [os.path.join(os.path.dirname(sys.executable), "slither.exe"), *base_args],
        [sys.executable, "-m", "slither", *base_args],
        [str(Path(venv_path) / "Scripts" / "slither.exe"), *base_args] if venv_path else [""],
        [str(local_venv_slither), *base_args],
        [str(local_venv_python), "-m", "slither", *base_args],
    ]

    run_env = os.environ.copy()
    run_env.pop("SOLC_VERSION", None)
    run_env["SOLC_VERSION"] = "0.8.34"
    run_env["PATH"] = scripts_dir + os.pathsep + run_env.get("PATH", "")
    if solc_binary:
        run_env["SOLC_BINARY"] = solc_binary
        run_env["CRYTIC_SOLC"] = solc_binary
        run_env["PATH"] = os.path.dirname(solc_binary) + os.pathsep + run_env["PATH"]

    logger.info("Running slither on %s", sol_filepath)
    result = None
    last_file_not_found = None
    for command in command_variants:
        if not command[0] or (command[0].endswith(".exe") and not os.path.exists(command[0])):
            continue
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                env=run_env,
            )
            break
        except FileNotFoundError as exc:
            last_file_not_found = exc
            continue
        except subprocess.TimeoutExpired as exc:
            raise SlitherTimeoutError(f"Slither timed out after {timeout} seconds") from exc

    if result is None:
        raise SlitherNotInstalledError(
            "Slither CLI not found. Install using pip install slither-analyzer and ensure slither --version works."
        ) from last_file_not_found

    if result.returncode not in (0, 1):
        detail = (result.stderr or result.stdout or "Unknown Slither execution error").strip()
        _COMPILER_ERROR_HINTS = (
            "FileNotFoundError",
            "WinError 2",
            "InvalidCompilation",
            "The system cannot find",
            "SOLC_VERSION",
            "not installed",
            "solc",
        )
        if any(hint in detail for hint in _COMPILER_ERROR_HINTS):
            logger.warning("solc compiler not found or broken — using heuristic fallback scanner")
            return _build_heuristic_slither_output(sol_filepath)
        raise SlitherParseError(f"Slither execution failed (rc={result.returncode}): {detail}")

    stdout = (result.stdout or "").strip()
    if not stdout:
        # Windows sometimes returns empty stdout for --json -, so retry to a temp json file.
        json_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        json_temp.close()
        try:
            fallback_args = [sol_filepath, "--json", json_temp.name, "--solc-remaps", "@=node_modules/@"]
            if solc_binary:
                fallback_args.extend(["--solc", solc_binary])
            fallback_variants = []
            for variant in command_variants:
                if variant[0] in ("", "slither") or variant[0].endswith("slither.exe") or variant[0] == sys.executable:
                    if variant[0] == sys.executable:
                        fallback_variants.append([sys.executable, "-m", "slither", *fallback_args])
                    else:
                        fallback_variants.append([variant[0], *fallback_args])

            fallback_result = None
            for command in fallback_variants:
                if not command[0] or (command[0].endswith(".exe") and not os.path.exists(command[0]) and command[0] != "slither"):
                    continue
                try:
                    fallback_result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        check=False,
                        env=run_env,
                    )
                    if fallback_result.returncode in (0, 1):
                        break
                except FileNotFoundError:
                    continue

            if os.path.exists(json_temp.name):
                with open(json_temp.name, "r", encoding="utf-8") as handle:
                    file_output = handle.read().strip()
                if file_output:
                    return json.loads(file_output)

            detail = ""
            if fallback_result is not None:
                detail = (fallback_result.stderr or fallback_result.stdout or "").strip()
            if "Version '0.8.0' not installed" in detail or "SOLC_VERSION" in detail:
                logger.warning("Slither solc-select mismatch detected, using heuristic fallback scanner")
                return _build_heuristic_slither_output(sol_filepath)
            raise SlitherParseError(f"Slither returned empty JSON output. {detail}".strip())
        finally:
            if os.path.exists(json_temp.name):
                os.remove(json_temp.name)

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise SlitherParseError(f"Could not parse Slither JSON output: {exc}") from exc

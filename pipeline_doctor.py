import sys
import os
import argparse
import time
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.append(backend_path)

from analyzer.slither_runner import run_slither
from analyzer.vulnerability_parser import parse_slither_output
from llm.patch_generator import generate_patch
from validator.patch_validator import validate_patch
from utils.git_handler import create_branch, push_to_github, create_pull_request
from utils.logger import get_logger

logger = get_logger("pipeline_doctor")

def main():
    parser = argparse.ArgumentParser(description="SmartPatch Pipeline Doctor: Automated Security Healer")
    parser.add_argument("file", help="Path to the Solidity file to analyze and heal")
    parser.add_argument("--branch", help="Base branch for the PR", default="main")
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)

    original_code = file_path.read_text(encoding="utf-8", errors="ignore")
    filename = file_path.name

    logger.info(f"🩺 Pipeline Doctor starting for {filename}...")

    # 1. Analyze
    try:
        slither_json = run_slither(str(file_path))
        vulnerabilities = parse_slither_output(slither_json)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

    if not vulnerabilities:
        logger.info("✅ No vulnerabilities detected. Your code is healthy!")
        return

    logger.info(f"❌ Detected {len(vulnerabilities)} vulnerabilities. Generating patch...")

    # 2. Patch
    try:
        patch_result = generate_patch(original_code, vulnerabilities)
        patched_code = patch_result.get("patched_code")
    except Exception as e:
        logger.error(f"Patch generation failed: {e}")
        sys.exit(1)

    if not patched_code or patched_code == original_code:
        logger.info("⚠️ Could not generate a meaningful patch.")
        return

    # 3. Validate
    logger.info("🔍 Validating patch...")
    validation = validate_patch(original_code, patched_code, vulnerabilities)
    
    if not validation.get("passed"):
        logger.error(f"🚫 Patch validation failed: {validation.get('status')}. Remaining issues: {validation.get('patched_count')}")
        sys.exit(1)

    logger.info(f"✨ Patch verified! Status: {validation.get('status')}. Risk score reduced from {validation.get('risk_score_before')}/100 to {validation.get('risk_score_after')}/100.")

    # 4. Automate Fix (Branch & PR)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    fix_branch = f"fix/vulnerability-{timestamp}"
    
    logger.info(f"🚀 Creating fix branch: {fix_branch}")
    if not create_branch(fix_branch, base_branch=args.branch):
        logger.error("Failed to create branch. Check GitHub permissions.")
        sys.exit(1)

    logger.info(f"📤 Pushing fix to {fix_branch}...")
    push_result = push_to_github(filename, patched_code, target_branch=fix_branch)
    
    if not push_result.get("success"):
        logger.error(f"Failed to push code: {push_result.get('error')}")
        sys.exit(1)

    logger.info("📬 Opening Pull Request...")
    pr_body = f"""## 🩺 SmartPatch Pipeline Doctor: Automated Security Fix

Detected and fixed {len(vulnerabilities)} vulnerabilities in `{filename}`.

### Audit Summary
- **Original Vulnerabilities**: {validation.get('original_count')}
- **Remaining After Patch**: {validation.get('patched_count')}
- **Risk Score Improvement**: {validation.get('risk_score_before')} → {validation.get('risk_score_after')}
- **Status**: {validation.get('status')}

*This PR was generated automatically by the SmartPatch Pipeline Doctor.*
"""
    pr_result = create_pull_request(
        title=f"Security: Automated fix for {filename}",
        body=pr_body,
        head_branch=fix_branch,
        base_branch=args.branch
    )

    if pr_result.get("success"):
        logger.info(f"🥳 Successfully healed! Pull Request opened: {pr_result.get('url')}")
    else:
        logger.error(f"Failed to open PR: {pr_result.get('error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()

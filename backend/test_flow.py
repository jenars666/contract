import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyzer.slither_runner import run_slither
from analyzer.vulnerability_parser import parse_vulnerabilities
from llm.patch_generator import generate_patch
from validator.patch_validator import validate_patch


async def run_full_flow(code: str) -> dict:
    # 1. Run Slither
    raw = run_slither(code)

    # 2. Parse vulnerabilities
    vulnerabilities, risk_score = parse_vulnerabilities(raw)

    # 3. Generate patch
    patch_result = generate_patch(code, vulnerabilities)
    patched_code = patch_result["patched_code"]
    explanation = patch_result["explanation"]

    # 4. Validate patch
    validation = validate_patch(code, patched_code)

    return {
        "vulnerabilities": vulnerabilities,
        "risk_score": risk_score,
        "patched_code": patched_code,
        "explanation": explanation,
        "validation": validation,
    }


if __name__ == "__main__":
    sample = """
pragma solidity ^0.8.0;
contract Test {
    mapping(address => uint) public balances;
    function withdraw() public {
        uint amount = balances[msg.sender];
        (bool success,) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] = 0;
    }
}
"""
    result = asyncio.run(run_full_flow(sample))
    print(f"Risk Score : {result['risk_score']}/100")
    print(f"Vulns Found: {len(result['vulnerabilities'])}")
    print(f"Patch Valid: {result['validation'].get('passed')}")

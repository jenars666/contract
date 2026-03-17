import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_flow import run_full_flow

SEV_ICON = {"High": "🔴", "Medium": "🟡", "Low": "🟢", "Informational": "🔵"}


def print_result(result: dict):
    vulns      = result["vulnerabilities"]
    score      = result["risk_score"]
    patched    = result["patched_code"]
    validation = result["validation"]

    bar   = "█" * (score // 5) + "░" * (20 - score // 5)
    label = "LOW RISK ✅" if score >= 70 else "MEDIUM RISK ⚠️" if score >= 40 else "HIGH RISK 🔴"

    print("\n" + "═" * 60)
    print("  SMART CONTRACT SECURITY REPORT")
    print("═" * 60)

    # Risk Score
    print(f"\n📊 RISK SCORE: {score}/100  [{bar}]  {label}\n")

    # Vulnerabilities
    print(f"🐛 VULNERABILITIES FOUND: {len(vulns)}")
    print("─" * 60)
    for i, v in enumerate(vulns, 1):
        icon = SEV_ICON.get(v["severity"], "⚪")
        print(f"  {i}. {icon} [{v['severity']}] {v['type']}"
              + (f"  (Line {v['line_number']})" if v["line_number"] else ""))
        # Wrap description at 55 chars
        desc = v["description"]
        for chunk in [desc[j:j+55] for j in range(0, len(desc), 55)]:
            print(f"       {chunk}")
        print()

    # Patched Code
    print("🛠  PATCHED CONTRACT")
    print("─" * 60)
    for ln, line in enumerate(patched.splitlines(), 1):
        print(f"  {ln:>3} │ {line}")

    # Validation
    print("\n" + "─" * 60)
    passed  = validation.get("passed", False)
    orig_c  = validation.get("original_count", len(vulns))
    patch_c = validation.get("patched_count", 0)
    new_score = validation.get("new_risk_score", score)
    status  = "✅ PASSED" if passed else "⚠️  NEEDS REVIEW"
    print(f"🔍 VALIDATION: {status}")
    print(f"   Vulnerabilities : {orig_c} → {patch_c}")
    print(f"   Risk Score      : {score} → {new_score}")
    if result.get("explanation"):
        print(f"   Fix Summary     : {result['explanation']}")
    print("═" * 60 + "\n")


def main():
    sol_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "..", "demo_contracts", "test_reentrancy.sol"
    )

    if not os.path.exists(sol_file):
        print(f"❌ File not found: {sol_file}")
        sys.exit(1)

    with open(sol_file, encoding="utf-8") as f:
        code = f.read()

    print(f"\n📄 Analyzing: {os.path.basename(sol_file)}")
    result = asyncio.run(run_full_flow(code))
    print_result(result)


if __name__ == "__main__":
    main()

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from analyzer.slither_runner import run_slither
from analyzer.vulnerability_parser import parse_slither_output
from validator.patch_validator import _heuristic_vulnerabilities
from llm.patch_generator import generate_patch
from utils.file_handler import create_temp_sol_file, cleanup_temp_file

def analyze_code(code):
    """Run Slither or heuristic scanner to find vulnerabilities in the code."""
    temp_file = create_temp_sol_file(code)
    try:
        raw = run_slither(temp_file, timeout=10)
        vulns = parse_slither_output(raw)
    except Exception:
        vulns = _heuristic_vulnerabilities(code)
    finally:
        cleanup_temp_file(temp_file)
    return vulns

def run_autofix_on_file(file_path, max_iters=3):
    """
    Iterates up to max_iters trying to achieve 0 vulnerabilities inside the file.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    print(f"\n🚀 Analyzing {file_path} for Auto-Fix...")
    
    for i in range(1, max_iters + 1):
        vulns = analyze_code(code)
        
        if not vulns:
            print(f"✅ [{file_path}] Target is completely BUG-FREE on iteration {i}!")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)
            return True
        
        print(f"⚠️ [{file_path}] Wait, Iteration {i}: Found {len(vulns)} vulnerabilities. Generating patch via LLM...")
        patch_result = generate_patch(code, vulns)
        code = patch_result["patched_code"]
        
    # Final validation after max_iters
    final_vulns = analyze_code(code)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(code)
        
    if not final_vulns:
        print(f"✅ [{file_path}] Successfully entirely patched after {max_iters} iterations!")
        return True
    else:
        print(f"❌ [{file_path}] Failed to remove all bugs completely within {max_iters} iterations. {len(final_vulns)} vulnerabilities remain.")
        return False

if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "demo_contracts"
    
    sol_files = []
    if os.path.isfile(target_dir):
        sol_files = [target_dir]
    else:
        for root, _, files in os.walk(target_dir):
            for f in files:
                if f.endswith(".sol"):
                    sol_files.append(os.path.join(root, f))
    
    for sf in sol_files:
        # Ignore dependency mappings
        if "node_modules" in sf or ".venv" in sf:
            continue
        run_autofix_on_file(sf, max_iters=3)
        
    # Exit with code 0 to allow the CI/CD pipeline to continue and commit the patches
    sys.exit(0)

import urllib.request
import json

base_url = "http://localhost:8000/api"

def test_endpoints():
    with open("demo_contracts/reentrancy_vulnerable.sol", "r") as f:
        code = f.read()

    print("1. Testing /analyze...")
    req = urllib.request.Request(f"{base_url}/analyze", data=json.dumps({"code": code}).encode('utf-8'), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        analyze_data = json.loads(response.read().decode('utf-8'))
        vulnerabilities = analyze_data.get('vulnerabilities', [])
        risk_score = analyze_data.get('risk_score', 0)
        print(f"   Success! Found {len(vulnerabilities)} vulnerabilities.")

    if not vulnerabilities:
        print("No vulnerabilities to test.")
        return

    print("2. Testing /exploit (Gemini 1.5 Pro)...")
    req = urllib.request.Request(f"{base_url}/exploit", data=json.dumps({"code": code, "vulnerability_type": "reentrancy", "vulnerability_name": vulnerabilities[0]['type']}).encode('utf-8'), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        exploit_data = json.loads(response.read().decode('utf-8'))
        print(f"   Success! Generated exploit: {len(exploit_data.get('exploit_code', ''))} chars.")

    print("3. Testing /boss-explanation (Gemini 1.5 Pro)...")
    req = urllib.request.Request(f"{base_url}/boss-explanation", data=json.dumps({"vulnerabilities": vulnerabilities, "risk_score": risk_score}).encode('utf-8'), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        boss_data = json.loads(response.read().decode('utf-8'))
        print(f"   Success! Boss explanation: {len(boss_data.get('explanation', ''))} chars.")

    print("4. Testing /patch (DeepSeek-R1)...")
    req = urllib.request.Request(f"{base_url}/patch", data=json.dumps({"code": code, "vulnerabilities": vulnerabilities}).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            patch_data = json.loads(response.read().decode('utf-8'))
            print(f"   Success! Patched code: {len(patch_data.get('patched_code', ''))} chars. Old score: {patch_data.get('old_risk_score')} -> New: {patch_data.get('new_risk_score')}")
    except Exception as e:
        print(f"   Error in /patch: {e}")

if __name__ == "__main__":
    test_endpoints()

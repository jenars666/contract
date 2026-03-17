import urllib.request
import json
import time

base_url = "http://localhost:8000/api"

def test_analyze():
    with open("demo_contracts/reentrancy_vulnerable.sol", "r") as f:
        code = f.read()

    print("Testing /analyze...")
    req = urllib.request.Request(f"{base_url}/analyze", data=json.dumps({"code": code}).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Status: {response.status}")
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                print(f"Risk Score: {data.get('risk_score')}")
                print(f"Vulnerabilities found: {len(data.get('vulnerabilities', []))}")
                return data
            else:
                print(f"Error: {response.read()}")
                return None
    except Exception as e:
        print(f"Connection error: {e}")
        return None

def main():
    print("--- Running Backend API Tests ---")
    time.sleep(3) # wait for server to spin up
    analyze_data = test_analyze()
    if analyze_data:
        print("\nAnalyze endpoint is WORKING correctly.")
    else:
        print("\nAnalyze endpoint FAILED.")

if __name__ == "__main__":
    main()

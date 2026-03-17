import urllib.request
import json
import time

def test_patch_api():
    base_url = "http://localhost:8000/api"
    sample_code = """
pragma solidity ^0.8.0;
contract Bank {
    mapping(address => uint) public balances;
    function withdraw(uint amount) public {
        if (balances[msg.sender] >= amount) {
            (bool success, ) = msg.sender.call{value: amount}("");
            require(success);
            balances[msg.sender] -= amount;
        }
    }
}
"""
    # Simple heuristic-like vuln for testing
    vulnerabilities = [
        {
            "id": "1",
            "type": "reentrancy-eth",
            "title": "Reentrancy Vulnerability",
            "severity": "CRITICAL",
            "lines": [7],
            "description": "External call before state update."
        }
    ]

    payload = {
        "code": sample_code,
        "vulnerabilities": vulnerabilities,
        "filename": "Bank.sol"
    }

    print("Sending patch request to server...")
    req = urllib.request.Request(
        f"{base_url}/patch",
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    try:
        # Give server time to boot if called immediately after run_command
        max_retries = 5
        for i in range(max_retries):
            try:
                with urllib.request.urlopen(req, timeout=60) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    print("\n--- Claude 3.5 Sonnet Response ---")
                    print(f"Success: {data.get('success')}")
                    print(f"Explanation: {data.get('explanation')}")
                    print("\nPatched Code Snippet:")
                    print("\n".join(data.get('patched_code', '').splitlines()[:20]))
                    return
            except urllib.error.URLError:
                if i < max_retries - 1:
                    print(f"Waiting for server... (attempt {i+1})")
                    time.sleep(2)
                else:
                    raise
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_patch_api()

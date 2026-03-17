import urllib.request
import json

def test_push_api():
    base_url = "http://localhost:8000/api"
    payload = {
        "filename": "test_push.sol",
        "code": "pragma solidity ^0.8.0; contract Test {}",
        "commit_message": "Test push from verification script"
    }

    print("Sending push request to server (expecting error due to placeholder credentials)...")
    req = urllib.request.Request(
        f"{base_url}/push",
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            print("\n--- Push Response ---")
            print(f"Success: {data.get('success')}")
            print(f"URL: {data.get('url')}")
    except urllib.error.HTTPError as e:
        # Pydantic/FastAPI might return 200 with success=False or throw error
        # In our case, the router returns a PushResponse even on success=False
        # But if there's a serious crash, it might be 500
        print(f"HTTP Error: {e.code} - {e.reason}")
        try:
            error_data = json.loads(e.read().decode('utf-8'))
            print(f"Detail: {error_data}")
        except:
            pass
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_push_api()

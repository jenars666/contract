import os
import requests
from dotenv import load_dotenv

def test_token():
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN", "").strip()
    
    if not token:
        print("ERROR: GITHUB_TOKEN not found in .env")
        return

    print(f"Testing token starting with: {token[:8]}...")
    
    # Test using 'token' scheme
    headers_token = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Test using 'Bearer' scheme
    headers_bearer = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    url = "https://api.github.com/user"

    print("\n--- Trying 'token' scheme ---")
    try:
        r1 = requests.get(url, headers=headers_token)
        print(f"Status Code: {r1.status_code}")
        if r1.status_code == 200:
            print(f"SUCCESS! Logged in as: {r1.json().get('login')}")
        else:
            print(f"FAILED: {r1.json().get('message')}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- Trying 'Bearer' scheme ---")
    try:
        r2 = requests.get(url, headers=headers_bearer)
        print(f"Status Code: {r2.status_code}")
        if r2.status_code == 200:
            print(f"SUCCESS! Logged in as: {r2.json().get('login')}")
        else:
            print(f"FAILED: {r2.json().get('message')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_token()

import requests
import json

try:
    print("Testing backend health...")
    r = requests.get("http://127.0.0.1:8000/")
    print(f"Root status: {r.status_code}")
    print(f"Root body: {r.text}")

    print("\nTesting Login Endpoint...")
    payload = {"email": "host@example.com", "password": "password"}
    r = requests.post("http://127.0.0.1:8000/auth/login", json=payload)
    print(f"Login status: {r.status_code}")
    print(f"Login body: {r.text}")

except Exception as e:
    print(f"Connection failed: {e}")

import requests
import time

payload = {"message": "Test: Show portfolio for CLT-001", "client_name": "Test"}

print("Sending request...")
start = time.time()

try:
    r = requests.post("http://127.0.0.1:8000/main/chat", json=payload, timeout=90)
    elapsed = time.time() - start
    
    print(f"\n✅ Response received in {elapsed:.1f}s")
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        print(f"\nAnswer (first 300 chars):\n{data['answer'][:300]}\n")
        print(f"Tools Used: {data['tools_used']}")
        print(f"Sources: {data['sources']}")
    else:
        print(f"Error: {r.text}")
        
except requests.Timeout:
    print("❌ Request timed out after 90 seconds")
except Exception as e:
    print(f"❌ Exception: {e}")

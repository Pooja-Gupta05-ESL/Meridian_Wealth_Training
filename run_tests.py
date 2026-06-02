import requests
import json

BASE_URL = "http://127.0.0.1:8000"

tests = [
    {
        "name": "T1: Portfolio Lookup",
        "query": "Show portfolio for CLT-001 with holdings breakdown and risk assessment"
    },
    {
        "name": "T2: Policy Check",
        "query": "What are the concentration limits for CLT-001 given his Moderate-Aggressive profile?"
    },
    {
        "name": "T3: IT Sector Comparison",
        "query": "Compare IT sector exposure between CLT-001 and CLT-002"
    },
    {
        "name": "T4: Rebalancing Advice",
        "query": "Analyze CLT-005 portfolio and recommend rebalancing actions"
    },
    {
        "name": "T5: Web Search",
        "query": "What's the latest market outlook for banking sector in India?"
    }
]

print("🧪 Running Lab 6.4 Test Suite\n")
print("=" * 80)

for i, test in enumerate(tests, 1):
    print(f"\n{test['name']}")
    print(f"Query: {test['query']}")
    print("-" * 80)
    
    try:
        payload = {
            "message": test['query'],
            "client_name": "Meridian"
        }
        
        response = requests.post(
            f"{BASE_URL}/main/chat",
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', 'No response')
            tools = data.get('tools_used', [])
            
            # Print first 300 chars of answer
            print(f"✅ Answer (first 300 chars):\n{answer[:300]}...\n")
            print(f"📊 Tools Used: {', '.join(tools)}")
            print(f"✅ Status: PASSED")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   {response.text}")
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    print()

print("\n" + "=" * 80)
print("✅ All tests completed!")

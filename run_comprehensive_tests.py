#!/usr/bin/env python3
"""
Meridian Wealth Financial Analyst - Comprehensive System Test
Tests all endpoints and functionality
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def test_health():
    """Test health endpoint"""
    print("✅ Testing /health endpoint...")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.json()}")

def test_agent_info():
    """Test agent info endpoint"""
    print("\n✅ Testing /agentinfo endpoint...")
    r = requests.get(f"{BASE_URL}/agentinfo")
    assert r.status_code == 200
    info = r.json()
    print(f"   Agent Name: {info['name']}")
    print(f"   Version: {info['version']}")
    print(f"   Status: {info['status']}")
    print(f"   Tools: {info['tools']}")

def test_diagnostic():
    """Test diagnostic endpoint"""
    print("\n✅ Testing /diagnostic endpoint...")
    r = requests.get(f"{BASE_URL}/diagnostic")
    assert r.status_code == 200
    diag = r.json()
    print(f"   Overall Status: {diag['status']}")
    print(f"   API Keys: {diag['api_keys']}")
    print(f"   Database: {diag['database']}")
    print(f"   Policy PDFs: {diag['policy_pdfs']}")

def test_portfolio_query():
    """Test portfolio lookup"""
    print("\n✅ Testing portfolio query...")
    payload = {
        "message": "Show portfolio for CLT-001 with holdings breakdown and risk assessment",
        "client_name": "Rajesh Mehta"
    }
    
    start = time.time()
    print(f"   Query: {payload['message']}")
    print(f"   Processing... (this may take 30-60 seconds)")
    
    r = requests.post(f"{BASE_URL}/main/chat", json=payload, timeout=120)
    elapsed = time.time() - start
    
    assert r.status_code == 200
    result = r.json()
    
    print(f"   ✅ Response received in {elapsed:.1f}s")
    print(f"   Status Code: {r.status_code}")
    print(f"   Tools Used: {result['tools_used']}")
    print(f"   Sources: {result['sources']}")
    print(f"\n   📄 Answer Preview (first 500 chars):")
    print(f"   " + "-"*66)
    print(f"   {result['answer'][:500]}...")
    print(f"   " + "-"*66)

def test_policy_query():
    """Test policy compliance check"""
    print("\n✅ Testing policy compliance query...")
    payload = {
        "message": "What are the concentration limits for CLT-001 given his Moderate-Aggressive profile?",
        "client_name": "Policy Check"
    }
    
    start = time.time()
    print(f"   Query: {payload['message']}")
    print(f"   Processing... (this may take 30-60 seconds)")
    
    r = requests.post(f"{BASE_URL}/main/chat", json=payload, timeout=120)
    elapsed = time.time() - start
    
    assert r.status_code == 200
    result = r.json()
    
    print(f"   ✅ Response received in {elapsed:.1f}s")
    print(f"   Tools Used: {result['tools_used']}")
    print(f"\n   📄 Answer Preview:")
    print(f"   " + "-"*66)
    print(f"   {result['answer'][:500]}...")
    print(f"   " + "-"*66)

def test_market_search():
    """Test market data search"""
    print("\n✅ Testing market search query...")
    payload = {
        "message": "Compare IT sector stocks in the current market",
        "client_name": "Market Analysis"
    }
    
    start = time.time()
    print(f"   Query: {payload['message']}")
    print(f"   Processing... (this may take 30-60 seconds)")
    
    r = requests.post(f"{BASE_URL}/main/chat", json=payload, timeout=120)
    elapsed = time.time() - start
    
    assert r.status_code == 200
    result = r.json()
    
    print(f"   ✅ Response received in {elapsed:.1f}s")
    print(f"   Tools Used: {result['tools_used']}")
    print(f"\n   📄 Answer Preview:")
    print(f"   " + "-"*66)
    print(f"   {result['answer'][:500]}...")
    print(f"   " + "-"*66)

def main():
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "MERIDIAN WEALTH FINANCIAL ANALYST" + " "*20 + "║")
    print("║" + " "*20 + "COMPREHENSIVE SYSTEM TEST" + " "*24 + "║")
    print("╚" + "="*68 + "╝")
    
    try:
        print_section("1. DIAGNOSTIC ENDPOINTS")
        test_health()
        test_agent_info()
        test_diagnostic()
        
        print_section("2. FUNCTIONAL TESTS")
        test_portfolio_query()
        test_policy_query()
        test_market_search()
        
        print_section("✅ ALL TESTS PASSED")
        print("System is fully operational and ready for use!\n")
        
        return True
    
    except Exception as e:
        print_section("❌ TEST FAILED")
        print(f"Error: {e}\n")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

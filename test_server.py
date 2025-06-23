#!/usr/bin/env python3
"""
Quick test script for Salasblog2 FastAPI server
"""
import requests
import time
import subprocess
import sys
from pathlib import Path

def test_endpoints():
    base_url = "http://localhost:8003"
    
    print("🧪 Testing Salasblog2 FastAPI Server")
    print("=" * 50)
    
    # Test 1: Home page
    print("1. Testing home page...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200 and "SALAS BLOG" in response.text:
            print("   ✅ Home page loads correctly")
        else:
            print(f"   ❌ Home page issue: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Home page error: {e}")
    
    # Test 2: Admin page
    print("2. Testing admin page...")
    try:
        response = requests.get(f"{base_url}/admin", timeout=5)
        if response.status_code == 200 and "Salasblog2 Admin" in response.text:
            print("   ✅ Admin page loads correctly")
        else:
            print(f"   ❌ Admin page issue: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Admin page error: {e}")
    
    # Test 3: API regenerate endpoint
    print("3. Testing regenerate API...")
    try:
        response = requests.get(f"{base_url}/api/regenerate", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Regenerate API works: {data.get('message', 'OK')}")
        else:
            print(f"   ❌ Regenerate API issue: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Regenerate API error: {e}")
    
    # Test 4: Static files
    print("4. Testing static files...")
    try:
        response = requests.get(f"{base_url}/static/css/style.css", timeout=5)
        if response.status_code == 200:
            print("   ✅ Static files serve correctly")
        else:
            print(f"   ❌ Static files issue: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Static files error: {e}")
    
    # Test 5: Individual page
    print("5. Testing individual page...")
    try:
        response = requests.get(f"{base_url}/about.html", timeout=5)
        if response.status_code == 200 and "About Me" in response.text:
            print("   ✅ Individual pages work correctly")
        else:
            print(f"   ❌ Individual page issue: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Individual page error: {e}")
    
    print("\n🎉 Test complete!")

if __name__ == "__main__":
    test_endpoints()
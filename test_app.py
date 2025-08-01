#!/usr/bin/env python3
"""
Simple test script for Medical Price Comparator API
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_main_page():
    """Test main page"""
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200 and "Medical Price Comparator" in response.text:
            print("✅ Main page working")
            return True
        else:
            print(f"❌ Main page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Main page error: {e}")
        return False

def test_admin_page():
    """Test admin page"""
    try:
        response = requests.get(f"{BASE_URL}/admin")
        if response.status_code == 200 and "Admin Panel" in response.text:
            print("✅ Admin page working")
            return True
        else:
            print(f"❌ Admin page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Admin page error: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    try:
        # Test providers endpoint
        response = requests.get(f"{BASE_URL}/api/v1/providers/")
        if response.status_code == 200:
            print("✅ Providers API working")
            providers_ok = True
        else:
            print(f"❌ Providers API failed: {response.status_code}")
            providers_ok = False
        
        # Test analyses search endpoint
        response = requests.get(f"{BASE_URL}/api/v1/analyses/search?query=test&limit=5")
        if response.status_code == 200:
            print("✅ Analyses search API working")
            analyses_ok = True
        else:
            print(f"❌ Analyses search API failed: {response.status_code}")
            analyses_ok = False
        
        return providers_ok and analyses_ok
        
    except Exception as e:
        print(f"❌ API endpoints error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Medical Price Comparator...")
    print()
    
    tests = [
        test_health,
        test_main_page,
        test_admin_page,
        test_api_endpoints
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print()
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All tests passed! ({passed}/{total})")
        print()
        print("🚀 Application is ready to use!")
        print(f"📱 Main interface: {BASE_URL}")
        print(f"🛠️  Admin panel: {BASE_URL}/admin")
        print(f"📊 API docs: {BASE_URL}/docs")
        sys.exit(0)
    else:
        print(f"⚠️  Some tests failed ({passed}/{total})")
        print("Please check the application logs and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
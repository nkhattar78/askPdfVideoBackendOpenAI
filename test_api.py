"""
Test script for PDF and YouTube Video Query API

This script tests all major endpoints of the FastAPI application.
Run this after starting the server to verify everything works correctly.

Usage:
    python test_api.py

Requirements:
    - FastAPI server running on http://localhost:8000
    - requests library: pip install requests
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_endpoint(method: str, endpoint: str, data: Dict[Any, Any] = None, files=None) -> Dict[Any, Any]:
    """Test a single API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            if files:
                response = requests.post(url, files=files, data=data)
            else:
                response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return {
            "status_code": response.status_code,
            "success": response.status_code < 400,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        }
    except requests.exceptions.RequestException as e:
        return {
            "status_code": 0,
            "success": False,
            "error": str(e)
        }

def run_tests():
    """Run comprehensive API tests"""
    print("🧪 Starting API Tests for PDF and YouTube Video Query System")
    print("=" * 60)
    
    tests = [
        # Health and Configuration Tests
        {
            "name": "Health Check",
            "method": "GET",
            "endpoint": "/"
        },
        {
            "name": "Azure OpenAI Test",
            "method": "GET",
            "endpoint": "/test-azure-openai"
        },
        {
            "name": "YouTube API Status",
            "method": "GET",
            "endpoint": "/youtube-status"
        },
        
        # Document Management Tests
        {
            "name": "List Documents",
            "method": "GET",
            "endpoint": "/documents/"
        },
        {
            "name": "List Videos",
            "method": "GET",
            "endpoint": "/videos/"
        },
        {
            "name": "Content Summary",
            "method": "GET",
            "endpoint": "/content-summary/"
        },
        
        # Query Tests (these will work if documents are already uploaded)
        {
            "name": "General Query",
            "method": "POST",
            "endpoint": "/query/",
            "data": {
                "query": "What is the main topic discussed?",
                "k": 3
            }
        },
        {
            "name": "Smart Query",
            "method": "POST",
            "endpoint": "/smart-query/",
            "data": {
                "query": "Explain the key concepts",
                "k": 3,
                "strategy": "best_match"
            }
        },
        {
            "name": "Smart Query All Content",
            "method": "POST",
            "endpoint": "/smart-query-all/",
            "data": {
                "query": "What are the main points?",
                "k": 3,
                "strategy": "best_match",
                "content_type": "all"
            }
        },
        
        # YouTube Tests (using a sample video)
        {
            "name": "Query YouTube Video (with manual transcript)",
            "method": "POST",
            "endpoint": "/query-youtube/",
            "data": {
                "query": "What is this video about?",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "k": 3,
                "manual_transcript": "This is a sample manual transcript for testing purposes. The video discusses various topics related to technology and innovation."
            }
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"\n🔍 Testing: {test['name']}")
        print(f"   {test['method']} {test['endpoint']}")
        
        result = test_endpoint(
            method=test['method'],
            endpoint=test['endpoint'],
            data=test.get('data')
        )
        
        results.append({
            "name": test['name'],
            "endpoint": test['endpoint'],
            **result
        })
        
        if result['success']:
            print(f"   ✅ Success (Status: {result['status_code']})")
            if 'response' in result and isinstance(result['response'], dict):
                if 'message' in result['response']:
                    print(f"   📝 Message: {result['response']['message'][:100]}...")
                elif 'answer' in result['response']:
                    print(f"   💬 Answer: {result['response']['answer'][:100]}...")
        else:
            print(f"   ❌ Failed (Status: {result['status_code']})")
            if 'error' in result:
                print(f"   🚨 Error: {result['error']}")
            elif 'response' in result:
                print(f"   📄 Response: {str(result['response'])[:200]}...")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All tests passed! Your API is working correctly.")
    else:
        print(f"\n⚠️  Some tests failed. Check the server logs and configuration.")
        print("\nFailed tests:")
        for result in results:
            if not result['success']:
                print(f"   - {result['name']}: {result.get('error', 'Unknown error')}")
    
    return results

def upload_sample_pdf():
    """Helper function to upload a sample PDF for testing"""
    print("\n📄 To test PDF functionality, you can:")
    print("1. Create a sample PDF file")
    print("2. Use the /upload-pdf/ endpoint")
    print("3. Then run the query tests")
    print("\nExample curl command:")
    print('curl -X POST "http://localhost:8000/upload-pdf/" -F "files=@sample.pdf"')

def main():
    """Main test runner"""
    print("🚀 PDF and YouTube Video Query API Test Suite")
    print(f"Testing server at: {BASE_URL}")
    print("\nMake sure your FastAPI server is running!")
    print("Start server with: uvicorn app.main:app --reload")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print(f"❌ Server not responding correctly (Status: {response.status_code})")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server. Make sure it's running on http://localhost:8000")
        return
    
    print("✅ Server is responding!")
    
    # Run tests
    results = run_tests()
    
    # Additional information
    upload_sample_pdf()
    
    print("\n🔗 Useful endpoints to test manually:")
    print("   - Swagger UI: http://localhost:8000/docs")
    print("   - ReDoc: http://localhost:8000/redoc")
    print("   - Health: http://localhost:8000/")

if __name__ == "__main__":
    main()

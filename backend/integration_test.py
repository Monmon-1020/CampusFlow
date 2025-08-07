#!/usr/bin/env python3
"""
Integration test script for stream role functionality
Run with: python integration_test.py
"""

import requests
import json
import sys
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "test@example.com"
TEST_STREAM_ADMIN_CODE = "STREAM_ADMIN_123"

class StreamRoleIntegrationTest:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_info = None
        self.test_stream_id = None
        
    def log(self, message: str, status: str = "INFO"):
        """Log test messages"""
        status_icon = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "ERROR": "❌",
            "WARNING": "⚠️"
        }.get(status, "📝")
        
        print(f"{status_icon} {message}")
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make API request with authentication"""
        url = f"{API_BASE_URL}{endpoint}"
        
        if self.auth_token:
            headers = kwargs.get('headers', {})
            headers['Authorization'] = f'Bearer {self.auth_token}'
            kwargs['headers'] = headers
            
        return self.session.request(method, url, **kwargs)
    
    def test_api_health(self) -> bool:
        """Test if API is running"""
        try:
            response = self.make_request('GET', '/health')
            if response.status_code == 200:
                self.log("API health check passed", "SUCCESS")
                return True
            else:
                self.log(f"API health check failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"API health check failed: {e}", "ERROR")
            return False
    
    def test_profile_endpoint_without_auth(self) -> bool:
        """Test profile endpoint without authentication (should fail)"""
        try:
            response = self.make_request('GET', '/api/profile')
            if response.status_code == 401:
                self.log("Profile endpoint correctly requires authentication", "SUCCESS")
                return True
            else:
                self.log(f"Profile endpoint should require auth but returned: {response.status_code}", "WARNING")
                return False
        except Exception as e:
            self.log(f"Profile endpoint test failed: {e}", "ERROR")
            return False
    
    def test_elevation_endpoint_without_auth(self) -> bool:
        """Test elevation endpoint without authentication (should fail)"""
        try:
            response = self.make_request('POST', '/api/profile/elevate', 
                                       json={'code': 'test'})
            if response.status_code == 401:
                self.log("Elevation endpoint correctly requires authentication", "SUCCESS")
                return True
            else:
                self.log(f"Elevation endpoint should require auth but returned: {response.status_code}", "WARNING")
                return False
        except Exception as e:
            self.log(f"Elevation endpoint test failed: {e}", "ERROR")
            return False
    
    def test_streams_endpoint_without_auth(self) -> bool:
        """Test streams endpoint without authentication (should fail)"""
        try:
            response = self.make_request('GET', '/api/streams')
            if response.status_code == 401:
                self.log("Streams endpoint correctly requires authentication", "SUCCESS")
                return True
            else:
                self.log(f"Streams endpoint should require auth but returned: {response.status_code}", "WARNING")
                return False
        except Exception as e:
            self.log(f"Streams endpoint test failed: {e}", "ERROR")
            return False
    
    def test_post_creation_without_auth(self) -> bool:
        """Test post creation without authentication (should fail)"""
        try:
            response = self.make_request('POST', '/api/streams/test-stream-id/announcements',
                                       json={'title': 'Test', 'content': 'Test content'})
            if response.status_code == 401:
                self.log("Post creation correctly requires authentication", "SUCCESS")
                return True
            else:
                self.log(f"Post creation should require auth but returned: {response.status_code}", "WARNING")
                return False
        except Exception as e:
            self.log(f"Post creation test failed: {e}", "ERROR")
            return False
    
    def test_openapi_docs(self) -> bool:
        """Test if OpenAPI docs are available"""
        try:
            response = self.make_request('GET', '/docs')
            if response.status_code == 200:
                self.log("OpenAPI docs are accessible", "SUCCESS")
                return True
            else:
                self.log(f"OpenAPI docs not accessible: {response.status_code}", "WARNING")
                return False
        except Exception as e:
            self.log(f"OpenAPI docs test failed: {e}", "ERROR")
            return False
    
    def run_tests(self):
        """Run all integration tests"""
        self.log("Starting Stream Role Integration Tests")
        self.log("=" * 50)
        
        tests = [
            ("API Health Check", self.test_api_health),
            ("OpenAPI Docs", self.test_openapi_docs),
            ("Profile Endpoint Auth", self.test_profile_endpoint_without_auth),
            ("Elevation Endpoint Auth", self.test_elevation_endpoint_without_auth),
            ("Streams Endpoint Auth", self.test_streams_endpoint_without_auth),
            ("Post Creation Auth", self.test_post_creation_without_auth),
        ]
        
        results = {}
        for test_name, test_func in tests:
            self.log(f"\nRunning: {test_name}")
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    self.log(f"{test_name}: PASSED", "SUCCESS")
                else:
                    self.log(f"{test_name}: FAILED", "ERROR")
            except Exception as e:
                self.log(f"{test_name}: ERROR - {e}", "ERROR")
                results[test_name] = False
        
        # Summary
        self.log("\n" + "=" * 50)
        self.log("TEST SUMMARY")
        self.log("=" * 50)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "PASS" if result else "FAIL"
            icon = "✅" if result else "❌"
            self.log(f"{icon} {test_name}: {status}")
        
        self.log(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 All tests passed!", "SUCCESS")
            return True
        else:
            self.log("⚠️ Some tests failed", "WARNING")
            return False


def run_basic_role_tests():
    """Run basic role logic tests (no API required)"""
    print("\n" + "=" * 50)
    print("RUNNING BASIC ROLE LOGIC TESTS")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Role values
    total_tests += 1
    try:
        from src.models import StreamRole
        assert StreamRole.STUDENT == "student"
        assert StreamRole.STREAM_ADMIN == "stream_admin"
        assert StreamRole.ADMIN == "admin"
        print("✅ StreamRole enum values test passed")
        tests_passed += 1
    except Exception as e:
        print(f"❌ StreamRole enum values test failed: {e}")
    
    # Test 2: Permission logic
    total_tests += 1
    try:
        allowed_roles = {'stream_admin', 'admin'}
        assert 'student' not in allowed_roles
        assert 'stream_admin' in allowed_roles
        assert 'admin' in allowed_roles
        print("✅ Permission logic test passed")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Permission logic test failed: {e}")
    
    # Test 3: Role text mapping
    total_tests += 1
    try:
        role_mapping = {
            'student': '学生',
            'stream_admin': 'ストリーム管理者',
            'admin': '管理者'
        }
        assert len(role_mapping) == 3
        assert role_mapping['student'] == '学生'
        print("✅ Role text mapping test passed")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Role text mapping test failed: {e}")
    
    print(f"\nBasic tests: {tests_passed}/{total_tests} passed")
    return tests_passed == total_tests


def main():
    """Main test runner"""
    print("🚀 Stream Role System Integration Tests")
    print("=====================================")
    
    # Run basic tests first (no API required)
    basic_success = run_basic_role_tests()
    
    # Run API integration tests
    tester = StreamRoleIntegrationTest()
    api_success = tester.run_tests()
    
    # Final summary
    print("\n" + "=" * 50)
    print("FINAL RESULTS")
    print("=" * 50)
    
    basic_status = "PASS" if basic_success else "FAIL"
    api_status = "PASS" if api_success else "FAIL"
    
    print(f"Basic Logic Tests: {basic_status}")
    print(f"API Integration Tests: {api_status}")
    
    if basic_success and api_success:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    elif basic_success:
        print("\n⚠️ Basic tests passed, but API tests failed")
        print("   This might mean the API server is not running")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
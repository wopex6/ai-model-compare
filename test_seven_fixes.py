#!/usr/bin/env python3
"""
Test script for the 7 issues fixed on Oct 31, 2025
Tests: Assessment, User Management, Bulk Delete, and Error Handling
"""

import requests
import json
import time
from pathlib import Path

class SevenFixesTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.admin_credentials = {
            'username': 'administrator',
            'password': 'admin123'
        }
        
    def log_test(self, test_name, success, message=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
        
    def login_as_admin(self):
        """Login as administrator"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json=self.admin_credentials,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('token')
                self.log_test("Admin Login", True, "Successfully logged in")
                return True
            else:
                self.log_test("Admin Login", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Admin Login", False, f"Error: {str(e)}")
            return False
    
    def test_favicon_not_404(self):
        """Test that favicon doesn't return 404"""
        try:
            response = requests.get(f"{self.base_url}/favicon.ico", timeout=5)
            # Should be 204 No Content, not 404
            success = response.status_code != 404
            self.log_test("Favicon Not 404", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Favicon Not 404", False, f"Error: {str(e)}")
            return False
    
    def test_bulk_delete_endpoint_exists(self):
        """Test that bulk delete endpoint exists"""
        if not self.auth_token:
            self.log_test("Bulk Delete Endpoint", False, "Not logged in")
            return False
            
        try:
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            # POST to the endpoint (will fail if no deleted users, but that's ok)
            response = self.session.post(
                f"{self.base_url}/api/admin/users/bulk-delete-deleted",
                headers=headers,
                timeout=10
            )
            # Should return 200 or 403 (if not admin), not 404
            success = response.status_code != 404
            message = f"Status: {response.status_code}"
            if response.status_code == 200:
                data = response.json()
                message += f" - Deleted {data.get('deleted_count', 0)} users"
            self.log_test("Bulk Delete Endpoint", success, message)
            return success
        except Exception as e:
            self.log_test("Bulk Delete Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_permanent_delete_endpoint_exists(self):
        """Test that permanent delete endpoint exists"""
        if not self.auth_token:
            self.log_test("Permanent Delete Endpoint", False, "Not logged in")
            return False
            
        try:
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            # Try to delete a non-existent user (should fail gracefully, not 404)
            response = self.session.post(
                f"{self.base_url}/api/admin/users/99999/permanent-delete",
                headers=headers,
                timeout=10
            )
            # Should return 400/500 (user not found), not 404 (endpoint not found)
            success = response.status_code != 404
            self.log_test("Permanent Delete Endpoint", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Permanent Delete Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_assessment_questions_count(self):
        """Test that assessment has more than 9 questions"""
        # This would need to check the personality_profiler.py file or API
        # For now, we'll just verify the module exists
        try:
            from ai_compare.personality_profiler import PersonalityProfiler
            profiler = PersonalityProfiler()
            question_count = len(profiler.questions)
            success = question_count >= 17  # Should have at least 17 questions
            self.log_test("Assessment Questions Count", success, f"Found {question_count} questions")
            return success
        except Exception as e:
            self.log_test("Assessment Questions Count", False, f"Error: {str(e)}")
            return False
    
    def test_assessment_no_skip(self):
        """Test that assessment doesn't allow skipping"""
        try:
            from ai_compare.personality_profiler import PersonalityProfiler
            profiler = PersonalityProfiler()
            # Start a test assessment
            session = profiler.start_assessment("test_user")
            question = profiler.get_next_question("test_user")
            if question:
                # Check can_skip is False
                success = question['can_skip'] == False
                self.log_test("Assessment No Skip", success, f"can_skip = {question['can_skip']}")
                return success
            else:
                self.log_test("Assessment No Skip", False, "No questions available")
                return False
        except Exception as e:
            self.log_test("Assessment No Skip", False, f"Error: {str(e)}")
            return False
    
    def test_assessment_pause_available(self):
        """Test that assessment allows pausing"""
        try:
            from ai_compare.personality_profiler import PersonalityProfiler
            profiler = PersonalityProfiler()
            # Start a test assessment
            session = profiler.start_assessment("test_user_pause")
            question = profiler.get_next_question("test_user_pause")
            if question:
                # Check can_pause is True
                success = question['can_pause'] == True
                self.log_test("Assessment Pause Available", success, f"can_pause = {question['can_pause']}")
                return success
            else:
                self.log_test("Assessment Pause Available", False, "No questions available")
                return False
        except Exception as e:
            self.log_test("Assessment Pause Available", False, f"Error: {str(e)}")
            return False
    
    def test_assessment_resume(self):
        """Test that assessment can be resumed"""
        try:
            from ai_compare.personality_profiler import PersonalityProfiler
            profiler = PersonalityProfiler()
            user_id = "test_user_resume"
            
            # Start assessment
            session = profiler.start_assessment(user_id)
            initial_question = profiler.get_next_question(user_id)
            
            # Answer first question
            if initial_question:
                profiler.record_response(user_id, initial_question['question_id'], 0)
            
            # Get next question
            second_question = profiler.get_next_question(user_id)
            
            # Simulate pause (session stays in memory)
            # Now resume - session should still exist
            resumed_session = profiler.assessment_sessions.get(user_id)
            success = resumed_session is not None and resumed_session['current_question'] == 1
            
            self.log_test("Assessment Resume", success, f"Current question: {resumed_session['current_question'] if resumed_session else 'N/A'}")
            return success
        except Exception as e:
            self.log_test("Assessment Resume", False, f"Error: {str(e)}")
            return False
    
    def test_user_management_api(self):
        """Test user management API endpoints"""
        if not self.auth_token:
            self.log_test("User Management API", False, "Not logged in")
            return False
            
        try:
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            response = self.session.get(
                f"{self.base_url}/api/admin/users",
                headers=headers,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                data = response.json()
                user_count = len(data)
                self.log_test("User Management API", True, f"Found {user_count} users")
            else:
                self.log_test("User Management API", False, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("User Management API", False, f"Error: {str(e)}")
            return False
    
    def test_no_500_errors_on_main_pages(self):
        """Test that main pages don't return 500 errors"""
        pages = [
            ('/', 'Home Page'),
            ('/multi-user', 'Multi-User Page'),
        ]
        
        all_success = True
        for path, name in pages:
            try:
                response = requests.get(f"{self.base_url}{path}", timeout=5)
                success = response.status_code != 500
                if not success:
                    all_success = False
                message = f"Status: {response.status_code}"
                self.log_test(f"No 500 Error - {name}", success, message)
            except Exception as e:
                all_success = False
                self.log_test(f"No 500 Error - {name}", False, f"Error: {str(e)}")
        
        return all_success
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "=" * 60)
        print("🧪 Testing Seven Fixes - Oct 31, 2025 19:38")
        print("=" * 60 + "\n")
        
        # Test 1: Server and basic endpoints
        print("📡 Testing Server and Basic Endpoints...")
        self.test_favicon_not_404()
        self.test_no_500_errors_on_main_pages()
        
        # Test 2: Login
        print("\n🔐 Testing Authentication...")
        if self.login_as_admin():
            # Test 3: Admin endpoints
            print("\n👤 Testing Admin Endpoints...")
            self.test_user_management_api()
            self.test_bulk_delete_endpoint_exists()
            self.test_permanent_delete_endpoint_exists()
        
        # Test 4: Assessment
        print("\n📝 Testing Assessment System...")
        self.test_assessment_questions_count()
        self.test_assessment_no_skip()
        self.test_assessment_pause_available()
        self.test_assessment_resume()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r['success'])
        total = len(self.test_results)
        failed = total - passed
        
        print(f"\n✅ Passed: {passed}/{total}")
        if failed > 0:
            print(f"❌ Failed: {failed}/{total}")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
        
        return passed == total

def main():
    """Main test runner"""
    tester = SevenFixesTester()
    
    try:
        success = tester.run_all_tests()
        if success:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print("\n⚠️  Some tests failed. See details above.")
            return 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 2
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")
        return 3

if __name__ == "__main__":
    import sys
    sys.exit(main())

#!/usr/bin/env python3
"""
Test script for the integrated AI chatbot multi-user system
Tests authentication, database operations, and API endpoints
"""

import requests
import json
import time
import sys
from pathlib import Path

class IntegratedSystemTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, message=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
    
    def test_server_running(self):
        """Test if the Flask server is running"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            success = response.status_code == 200
            self.log_test("Server Running", success, f"Status: {response.status_code}")
            return success
        except requests.exceptions.RequestException as e:
            self.log_test("Server Running", False, f"Error: {str(e)}")
            return False
    
    def test_multi_user_interface(self):
        """Test if multi-user interface is accessible"""
        try:
            response = requests.get(f"{self.base_url}/multi-user", timeout=5)
            success = response.status_code == 200 and "Multi-User" in response.text
            self.log_test("Multi-User Interface", success, f"Status: {response.status_code}")
            return success
        except requests.exceptions.RequestException as e:
            self.log_test("Multi-User Interface", False, f"Error: {str(e)}")
            return False
    
    def test_database_creation(self):
        """Test if integrated database is created"""
        db_path = Path("integrated_users.db")
        success = db_path.exists()
        self.log_test("Database Creation", success, f"Database exists: {success}")
        return success
    
    def test_default_user_login(self):
        """Test login with default user 'Wai Tse'"""
        try:
            login_data = {
                "username": "Wai Tse",
                "password": ".//."
            }
            response = requests.post(f"{self.base_url}/api/auth/login", 
                                   json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('token'):
                    self.auth_token = data['token']
                    self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                    self.log_test("Default User Login", True, "Successfully logged in as Wai Tse")
                    return True
            
            self.log_test("Default User Login", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
        except requests.exceptions.RequestException as e:
            self.log_test("Default User Login", False, f"Error: {str(e)}")
            return False
    
    def test_user_profile_access(self):
        """Test accessing user profile"""
        if not self.auth_token:
            self.log_test("User Profile Access", False, "No auth token available")
            return False
        
        try:
            response = self.session.get(f"{self.base_url}/api/user/profile", timeout=10)
            success = response.status_code == 200
            if success:
                profile = response.json()
                self.log_test("User Profile Access", True, f"Profile loaded: {profile.get('first_name', 'N/A')}")
            else:
                self.log_test("User Profile Access", False, f"Status: {response.status_code}")
            return success
        except requests.exceptions.RequestException as e:
            self.log_test("User Profile Access", False, f"Error: {str(e)}")
            return False
    
    def test_psychology_traits_access(self):
        """Test accessing psychology traits"""
        if not self.auth_token:
            self.log_test("Psychology Traits Access", False, "No auth token available")
            return False
        
        try:
            response = self.session.get(f"{self.base_url}/api/user/psychology-traits", timeout=10)
            success = response.status_code == 200
            if success:
                traits = response.json()
                self.log_test("Psychology Traits Access", True, f"Found {len(traits)} traits")
            else:
                self.log_test("Psychology Traits Access", False, f"Status: {response.status_code}")
            return success
        except requests.exceptions.RequestException as e:
            self.log_test("Psychology Traits Access", False, f"Error: {str(e)}")
            return False
    
    def test_conversations_access(self):
        """Test accessing conversations"""
        if not self.auth_token:
            self.log_test("Conversations Access", False, "No auth token available")
            return False
        
        try:
            response = self.session.get(f"{self.base_url}/api/user/conversations", timeout=10)
            success = response.status_code == 200
            if success:
                conversations = response.json()
                self.log_test("Conversations Access", True, f"Found {len(conversations)} conversations")
            else:
                self.log_test("Conversations Access", False, f"Status: {response.status_code}")
            return success
        except requests.exceptions.RequestException as e:
            self.log_test("Conversations Access", False, f"Error: {str(e)}")
            return False
    
    def test_create_conversation(self):
        """Test creating a new conversation"""
        if not self.auth_token:
            self.log_test("Create Conversation", False, "No auth token available")
            return False
        
        try:
            conversation_data = {
                "title": f"Test Conversation {int(time.time())}"
            }
            response = self.session.post(f"{self.base_url}/api/user/conversations", 
                                       json=conversation_data, timeout=10)
            success = response.status_code == 200
            if success:
                data = response.json()
                session_id = data.get('session_id')
                self.log_test("Create Conversation", True, f"Created session: {session_id}")
                return session_id
            else:
                self.log_test("Create Conversation", False, f"Status: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("Create Conversation", False, f"Error: {str(e)}")
            return False
    
    def test_send_message(self, session_id):
        """Test sending a message and getting AI response"""
        if not self.auth_token or not session_id:
            self.log_test("Send Message", False, "No auth token or session ID available")
            return False
        
        try:
            message_data = {
                "senderType": "user",
                "content": "Hello! This is a test message. Can you respond?"
            }
            response = self.session.post(f"{self.base_url}/api/user/conversations/{session_id}/messages", 
                                       json=message_data, timeout=30)
            success = response.status_code == 200
            if success:
                data = response.json()
                ai_response = data.get('ai_response', 'No AI response')
                self.log_test("Send Message", True, f"AI responded: {ai_response[:50]}...")
            else:
                self.log_test("Send Message", False, f"Status: {response.status_code}")
            return success
        except requests.exceptions.RequestException as e:
            self.log_test("Send Message", False, f"Error: {str(e)}")
            return False
    
    def test_new_user_signup(self):
        """Test creating a new user account"""
        try:
            signup_data = {
                "username": f"testuser_{int(time.time())}",
                "email": f"test_{int(time.time())}@example.com",
                "password": "testpassword123"
            }
            response = requests.post(f"{self.base_url}/api/auth/signup", 
                                   json=signup_data, timeout=10)
            success = response.status_code == 200
            if success:
                data = response.json()
                self.log_test("New User Signup", True, f"Created user: {data.get('username')}")
            else:
                self.log_test("New User Signup", False, f"Status: {response.status_code}")
            return success
        except requests.exceptions.RequestException as e:
            self.log_test("New User Signup", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Integrated AI Chatbot System Tests\n")
        
        # Basic connectivity tests
        if not self.test_server_running():
            print("\n❌ Server is not running. Please start the Flask app first:")
            print("   cd C:\\Users\\trabc\\CascadeProjects\\ai-model-compare")
            print("   python app.py")
            return False
        
        self.test_multi_user_interface()
        self.test_database_creation()
        
        # Authentication tests
        if self.test_default_user_login():
            # Authenticated user tests
            self.test_user_profile_access()
            self.test_psychology_traits_access()
            self.test_conversations_access()
            
            # Conversation functionality tests
            session_id = self.test_create_conversation()
            if session_id:
                self.test_send_message(session_id)
        
        # New user tests
        self.test_new_user_signup()
        
        # Summary
        print(f"\n📊 Test Results Summary:")
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        print(f"   Passed: {passed}/{total}")
        
        if passed == total:
            print("🎉 All tests passed! The integrated system is working correctly.")
            print(f"\n🌐 Access your multi-user AI chatbot at: {self.base_url}/multi-user")
            print("   Login with: Username: 'Wai Tse', Password: './/.'")
        else:
            print("⚠️  Some tests failed. Check the error messages above.")
        
        return passed == total

def main():
    """Main test function"""
    print("Integrated AI Chatbot System Tester")
    print("=" * 50)
    
    # Check if server URL is provided
    base_url = "http://localhost:5000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"Testing server at: {base_url}")
    print()
    
    tester = IntegratedSystemTester(base_url)
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 Next Steps:")
        print("1. Open your browser")
        print(f"2. Go to: {base_url}/multi-user")
        print("3. Login with: Username: 'Wai Tse', Password: './/.'")
        print("4. Explore the AI Chat, Profile, Psychology, and Conversations tabs")
        print("5. Try having a conversation with the AI!")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())

"""
Enhanced Security Module for Web Platform
Implements secure API key storage and management
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class SecureKeyManager:
    """Secure API key storage for web platform"""
    
    def __init__(self, encryption_key_file='.encryption_key'):
        self.encryption_key_file = encryption_key_file
        self._encryption_key = None
        self._load_or_create_key()
    
    def _load_or_create_key(self):
        """Load existing encryption key or create new one"""
        try:
            if os.path.exists(self.encryption_key_file):
                with open(self.encryption_key_file, 'rb') as f:
                    self._encryption_key = f.read()
            else:
                self._encryption_key = Fernet.generate_key()
                with open(self.encryption_key_file, 'wb') as f:
                    f.write(self._encryption_key)
                # Set file permissions (read/write for owner only)
                os.chmod(self.encryption_key_file, 0o600)
        except Exception as e:
            print(f"Error managing encryption key: {e}")
            self._encryption_key = Fernet.generate_key()
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API key for storage"""
        try:
            fernet = Fernet(self._encryption_key)
            encrypted_key = fernet.encrypt(api_key.encode())
            return base64.urlsafe_b64encode(encrypted_key).decode()
        except Exception as e:
            print(f"Error encrypting API key: {e}")
            return None
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt API key for use"""
        try:
            fernet = Fernet(self._encryption_key)
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode())
            decrypted_key = fernet.decrypt(encrypted_bytes).decode()
            return decrypted_key
        except Exception as e:
            print(f"Error decrypting API key: {e}")
            return None
    
    def store_api_key(self, provider: str, api_key: str, user_id: str = None):
        """Store encrypted API key with metadata"""
        try:
            encrypted_key = self.encrypt_api_key(api_key)
            if not encrypted_key:
                return False
            
            key_data = {
                'provider': provider,
                'encrypted_key': encrypted_key,
                'user_id': user_id,
                'created_at': datetime.now().isoformat(),
                'last_used': None,
                'usage_count': 0
            }
            
            # Store in secure location (could be database or encrypted file)
            storage_file = f'.secure_keys_{user_id or "default"}.json'
            
            # Load existing keys
            existing_keys = {}
            if os.path.exists(storage_file):
                try:
                    with open(storage_file, 'r') as f:
                        existing_keys = json.load(f)
                except:
                    existing_keys = {}
            
            # Add new key
            existing_keys[provider] = key_data
            
            # Save encrypted
            with open(storage_file, 'w') as f:
                json.dump(existing_keys, f, indent=2)
            
            os.chmod(storage_file, 0o600)
            return True
            
        except Exception as e:
            print(f"Error storing API key: {e}")
            return False
    
    def get_api_key(self, provider: str, user_id: str = None) -> str:
        """Retrieve and decrypt API key"""
        try:
            storage_file = f'.secure_keys_{user_id or "default"}.json'
            
            if not os.path.exists(storage_file):
                return None
            
            with open(storage_file, 'r') as f:
                keys = json.load(f)
            
            if provider not in keys:
                return None
            
            key_data = keys[provider]
            encrypted_key = key_data['encrypted_key']
            
            # Update usage metadata
            key_data['last_used'] = datetime.now().isoformat()
            key_data['usage_count'] += 1
            keys[provider] = key_data
            
            with open(storage_file, 'w') as f:
                json.dump(keys, f, indent=2)
            
            return self.decrypt_api_key(encrypted_key)
            
        except Exception as e:
            print(f"Error retrieving API key: {e}")
            return None
    
    def delete_api_key(self, provider: str, user_id: str = None):
        """Delete stored API key"""
        try:
            storage_file = f'.secure_keys_{user_id or "default"}.json'
            
            if not os.path.exists(storage_file):
                return False
            
            with open(storage_file, 'r') as f:
                keys = json.load(f)
            
            if provider in keys:
                del keys[provider]
                
                with open(storage_file, 'w') as f:
                    json.dump(keys, f, indent=2)
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting API key: {e}")
            return False

# Test the secure key manager
def test_secure_key_manager():
    """Run automatic tests for secure key management"""
    print("🧪 Testing Secure Key Manager...")
    
    key_manager = SecureKeyManager()
    test_results = []
    
    # Test 1: Key encryption/decryption
    try:
        test_key = "sk-test123456789"
        encrypted = key_manager.encrypt_api_key(test_key)
        decrypted = key_manager.decrypt_api_key(encrypted)
        
        success = decrypted == test_key
        test_results.append({
            'test': 'Key Encryption/Decryption',
            'passed': success,
            'details': f"Original: {test_key[:10]}..., Decrypted: {decrypted[:10] if decrypted else 'None'}..."
        })
    except Exception as e:
        test_results.append({
            'test': 'Key Encryption/Decryption',
            'passed': False,
            'details': str(e)
        })
    
    # Test 2: Store and retrieve API key
    try:
        provider = "test_provider"
        api_key = "sk-testkey123456789"
        user_id = "test_user"
        
        # Store key
        store_success = key_manager.store_api_key(provider, api_key, user_id)
        
        # Retrieve key
        retrieved_key = key_manager.get_api_key(provider, user_id)
        
        success = store_success and retrieved_key == api_key
        test_results.append({
            'test': 'Store/Retrieve API Key',
            'passed': success,
            'details': f"Store: {store_success}, Retrieved: {retrieved_key[:10] if retrieved_key else 'None'}..."
        })
        
        # Cleanup
        key_manager.delete_api_key(provider, user_id)
        
    except Exception as e:
        test_results.append({
            'test': 'Store/Retrieve API Key',
            'passed': False,
            'details': str(e)
        })
    
    # Test 3: Key deletion
    try:
        provider = "test_delete"
        api_key = "sk-deletekey123456789"
        user_id = "test_user"
        
        # Store key
        key_manager.store_api_key(provider, api_key, user_id)
        
        # Verify it exists
        retrieved_before = key_manager.get_api_key(provider, user_id)
        
        # Delete key
        delete_success = key_manager.delete_api_key(provider, user_id)
        
        # Verify it's gone
        retrieved_after = key_manager.get_api_key(provider, user_id)
        
        success = delete_success and retrieved_before == api_key and retrieved_after is None
        test_results.append({
            'test': 'Delete API Key',
            'passed': success,
            'details': f"Delete: {delete_success}, Before: {retrieved_before[:10] if retrieved_before else 'None'}..., After: {retrieved_after}"
        })
        
    except Exception as e:
        test_results.append({
            'test': 'Delete API Key',
            'passed': False,
            'details': str(e)
        })
    
    # Print results
    passed = sum(1 for result in test_results if result['passed'])
    total = len(test_results)
    
    print(f"\n📊 Secure Key Manager Test Results:")
    print(f"Passed: {passed}/{total}")
    
    for result in test_results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"{status}: {result['test']}")
        if not result['passed']:
            print(f"   Details: {result['details']}")
    
    return passed == total

if __name__ == "__main__":
    test_secure_key_manager()

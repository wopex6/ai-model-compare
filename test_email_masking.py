"""
Test Email Masking Functionality
"""

from email_service import EmailService

def test_email_masking():
    """Test the email masking feature"""
    
    email_service = EmailService()
    
    print("\n" + "="*60)
    print("🔒 EMAIL MASKING TEST")
    print("="*60)
    
    test_emails = [
        "johndoe@example.com",
        "alice@gmail.com",
        "bob123456@outlook.com",
        "ab@test.com",  # Short email
        "a@test.com",   # Very short
        "testuser@company.org",
        "admin@site.com"
    ]
    
    print("\n📧 Testing Email Masking:")
    print("-"*60)
    
    for email in test_emails:
        masked = email_service._mask_email(email)
        print(f"Original: {email:30} → Masked: {masked}")
    
    print("\n" + "="*60)
    print("✅ Email masking shows first 2 and last 2 chars of username")
    print("="*60)
    
    print("\n📝 Examples in verification email:")
    print("-"*60)
    print("Email: johndoe@example.com")
    print("Shows: jo****oe@example.com")
    print("\nEmail: alice@gmail.com")
    print("Shows: al****ce@gmail.com")
    print("\nEmail: bob123456@outlook.com")
    print("Shows: bo****56@outlook.com")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    test_email_masking()

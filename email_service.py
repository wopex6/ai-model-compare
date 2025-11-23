"""
Email service for sending verification codes
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.sender_email = os.getenv('EMAIL_SENDER')
        self.sender_password = os.getenv('EMAIL_PASSWORD')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
    
    def _mask_email(self, email: str) -> str:
        """Mask email showing only first 2 and last 2 chars of username
        
        Example:
        - johndoe@example.com -> jo****oe@example.com
        - ab@test.com -> ab@test.com (short emails stay visible)
        - a@test.com -> a****@test.com
        """
        if '@' not in email:
            return email
        
        username, domain = email.split('@', 1)
        
        # If username is 4 chars or less, show it all
        if len(username) <= 4:
            return email
        
        # Show first 2 and last 2 chars, mask the middle
        masked_username = username[:2] + '****' + username[-2:]
        return f"{masked_username}@{domain}"
        
    def send_verification_code(self, recipient_email: str, username: str, verification_code: str) -> bool:
        """Send verification code email"""
        
        if not self.sender_email or not self.sender_password:
            print("❌ Email credentials not configured")
            return False
        
        try:
            # Mask email for privacy (show first 2 and last 2 chars of username)
            masked_email = self._mask_email(recipient_email)
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = "Email Verification - AI ChatChat"
            message["From"] = self.sender_email
            message["To"] = recipient_email
            
            # HTML email body
            html = f"""
            <html>
              <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                  <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0;">🤖 AI ChatChat</h1>
                  </div>
                  
                  <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                    <h2 style="color: #333;">Welcome, {username}!</h2>
                    <p>Thank you for signing up. Please verify your email address to start chatting with our AI.</p>
                    
                    <div style="background: white; padding: 20px; margin: 20px 0; border-radius: 8px; text-align: center;">
                      <p style="margin: 0 0 10px 0; color: #666;">Verification code for <strong>{masked_email}</strong>:</p>
                      <h1 style="font-size: 36px; letter-spacing: 8px; color: #667eea; margin: 10px 0;">{verification_code}</h1>
                      <p style="margin: 10px 0 0 0; color: #999; font-size: 14px;">This code will expire in 1 hour</p>
                    </div>
                    
                    <p style="color: #666; font-size: 14px;">If you didn't create an account, you can safely ignore this email.</p>
                  </div>
                  
                  <div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
                    <p>© 2025 AI ChatChat. Powered by AI.</p>
                  </div>
                </div>
              </body>
            </html>
            """
            
            # Plain text version
            text = f"""
            AI ChatChat - Email Verification
            
            Welcome, {username}!
            
            Thank you for signing up. Please verify your email address to start chatting with our AI.
            
            Verification code for {masked_email}: {verification_code}
            
            This code will expire in 1 hour.
            
            If you didn't create an account, you can safely ignore this email.
            
            © 2025 AI ChatChat
            """
            
            # Attach both versions
            part1 = MIMEText(text, "plain")
            part2 = MIMEText(html, "html")
            message.attach(part1)
            message.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient_email, message.as_string())
            
            print(f"✅ Verification email sent to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send verification email: {e}")
            return False

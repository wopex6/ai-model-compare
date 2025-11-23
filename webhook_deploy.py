"""
GitHub Webhook for Auto-Deploy
Add this route to your Flask app for instant deployment
"""
import hmac
import hashlib
import subprocess
from flask import request, jsonify

# Add to your app.py:

@app.route('/deploy-webhook', methods=['POST'])
def deploy_webhook():
    """GitHub webhook endpoint for auto-deployment"""
    
    # Verify GitHub signature (optional but recommended)
    signature = request.headers.get('X-Hub-Signature-256')
    
    if signature:
        secret = os.getenv('GITHUB_WEBHOOK_SECRET', 'your-secret-here')
        expected_signature = 'sha256=' + hmac.new(
            secret.encode(),
            request.data,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return jsonify({'error': 'Invalid signature'}), 401
    
    # Pull latest code
    try:
        # Navigate to project directory and pull
        result = subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            cwd='/home/YOUR_USERNAME/ai-model-compare',
            capture_output=True,
            text=True
        )
        
        # Install dependencies if requirements changed
        if 'requirements.txt' in result.stdout:
            subprocess.run(
                ['pip', 'install', '-r', 'requirements.txt'],
                cwd='/home/YOUR_USERNAME/ai-model-compare'
            )
        
        # Reload by touching WSGI
        subprocess.run([
            'touch',
            '/var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py'
        ])
        
        return jsonify({
            'status': 'success',
            'message': 'Deployment triggered',
            'output': result.stdout
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

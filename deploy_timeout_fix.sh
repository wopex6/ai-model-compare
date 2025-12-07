#!/bin/bash
# Quick deployment script for PythonAnywhere timeout fix

echo "🚀 Deploying 504 Timeout Fix to PythonAnywhere"
echo "=============================================="
echo ""

# Step 1: Check current directory
echo "📂 Step 1: Checking directory..."
if [ ! -f "app.py" ]; then
    echo "❌ Error: Not in ai-model-compare directory!"
    echo "   Please run: cd ~/ai-model-compare"
    exit 1
fi
echo "✅ In correct directory"
echo ""

# Step 2: Pull latest code
echo "📥 Step 2: Pulling latest code from GitHub..."
git pull origin main
if [ $? -ne 0 ]; then
    echo "❌ Git pull failed! Check your git setup."
    exit 1
fi
echo "✅ Code updated"
echo ""

# Step 3: Verify timeout fix is in code
echo "🔍 Step 3: Verifying timeout fix..."
if grep -q "timeout=20.0" ai_compare/simple_models.py; then
    echo "✅ Timeout fix found in code"
else
    echo "⚠️  Warning: Timeout code not found. Make sure to commit and push first!"
fi
echo ""

# Step 4: Install httpx
echo "📦 Step 4: Installing httpx..."
pip3.10 install --user httpx
if [ $? -ne 0 ]; then
    echo "❌ httpx installation failed!"
    exit 1
fi
echo "✅ httpx installed"
echo ""

# Step 5: Verify installation
echo "✅ Step 5: Verifying httpx installation..."
python3.10 -c "import httpx; print(f'httpx version: {httpx.__version__}')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: httpx verification failed"
else
    echo "✅ httpx verified"
fi
echo ""

# Step 6: Reload web app
echo "🔄 Step 6: Reloading web app..."
echo "   Please manually reload your web app:"
echo "   1. Go to PythonAnywhere Web tab"
echo "   2. Click 'Reload trabcd.pythonanywhere.com'"
echo ""

echo "=============================================="
echo "✅ Deployment script complete!"
echo ""
echo "Next steps:"
echo "1. Reload web app in PythonAnywhere Web tab"
echo "2. Test /scientist/chat endpoint"
echo "3. Check error logs for any issues"
echo ""
echo "To check logs:"
echo "  tail -f /var/log/trabcd.pythonanywhere.com.error.log"
echo ""

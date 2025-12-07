# PowerShell script to commit and push the timeout fix

Write-Host "🚀 Committing and Pushing Timeout Fix" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""

# Check if in git repo
if (-not (Test-Path ".git")) {
    Write-Host "❌ Error: Not in a git repository!" -ForegroundColor Red
    Write-Host "   Make sure you're in the ai-model-compare directory" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ In git repository" -ForegroundColor Green
Write-Host ""

# Stage the files
Write-Host "📝 Staging files..." -ForegroundColor Cyan
git add ai_compare/simple_models.py
git add requirements.txt
git add FIX_504_GATEWAY_TIMEOUT.md
git add DEPLOY_TO_PYTHONANYWHERE.md
git add PRODUCTION_DIAGNOSIS_COMPLETE.md
git add PRODUCTION_INVESTIGATION_SUMMARY.md

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Git add failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Files staged" -ForegroundColor Green
Write-Host ""

# Show what's being committed
Write-Host "📋 Files to be committed:" -ForegroundColor Cyan
git diff --cached --name-only
Write-Host ""

# Commit
Write-Host "💾 Committing changes..." -ForegroundColor Cyan
git commit -m "fix: Add 20s timeout to AI clients to prevent 504 errors

- Added httpx library for timeout management
- Set 20s timeout for OpenAI client (simple_models.py:33-40)
- Set 20s timeout for Anthropic client (simple_models.py:73-80)
- Prevents Gateway Timeout on PythonAnywhere
- Falls back to next model if timeout occurs
- Added httpx>=0.25.0 to requirements.txt
- Created deployment documentation"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Git commit failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Changes committed" -ForegroundColor Green
Write-Host ""

# Push
Write-Host "📤 Pushing to GitHub..." -ForegroundColor Cyan
git push origin main

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Git push failed!" -ForegroundColor Red
    Write-Host "   You may need to pull first or resolve conflicts" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Pushed to GitHub" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "====================================" -ForegroundColor Green
Write-Host "✅ All done! Code is on GitHub" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Log into PythonAnywhere" -ForegroundColor White
Write-Host "2. Open a Bash console" -ForegroundColor White
Write-Host "3. Run:" -ForegroundColor White
Write-Host "   cd ~/ai-model-compare" -ForegroundColor Cyan
Write-Host "   git pull origin main" -ForegroundColor Cyan
Write-Host "   pip3.10 install --user httpx" -ForegroundColor Cyan
Write-Host "4. Go to Web tab and reload your web app" -ForegroundColor White
Write-Host ""
Write-Host "Or use the deploy_timeout_fix.sh script on PythonAnywhere" -ForegroundColor Yellow
Write-Host ""

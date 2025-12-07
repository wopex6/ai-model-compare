# PowerShell script to commit the REAL fix (models.py, not simple_models.py)

Write-Host "🚨 Committing REAL Fix - models.py (ACTUALLY USED)" -ForegroundColor Red
Write-Host "================================================" -ForegroundColor Red
Write-Host ""
Write-Host "CRITICAL: We fixed the WRONG file initially!" -ForegroundColor Yellow
Write-Host "  ❌ simple_models.py - NOT used in production" -ForegroundColor Red
Write-Host "  ✅ models.py - ACTUALLY used in production" -ForegroundColor Green
Write-Host ""

# Check if in git repo
if (-not (Test-Path ".git")) {
    Write-Host "❌ Error: Not in a git repository!" -ForegroundColor Red
    exit 1
}

# Stage the files
Write-Host "📝 Staging files..." -ForegroundColor Cyan
git add ai_compare/models.py
git add ai_compare/simple_models.py
git add requirements.txt
git add CRITICAL_DISCOVERY.md
git add REAL_FIX_APPLIED.md
git add commit_REAL_fix.ps1

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

# Show key changes
Write-Host "🔍 Key changes:" -ForegroundColor Cyan
Write-Host "  ✅ models.py: Added timeout to AsyncOpenAI (lines 29-36)" -ForegroundColor Green
Write-Host "  ✅ models.py: Added timeout to AsyncAnthropic (lines 67-74)" -ForegroundColor Green
Write-Host "  ✅ simple_models.py: Also fixed (backup)" -ForegroundColor Green
Write-Host "  ✅ requirements.txt: httpx>=0.25.0 already added" -ForegroundColor Green
Write-Host ""

# Commit
Write-Host "💾 Committing changes..." -ForegroundColor Cyan
git commit -m "fix: Add 20s timeout to ACTUAL models.py file (not simple_models.py)

CRITICAL FIX: Previous fix was to simple_models.py which is unused!

Investigation revealed:
- simple_models.py is NOT imported anywhere (unused code)
- models.py is the actual file used by compare.py
- Production uses: compare.py -> models.py -> AsyncOpenAI/AsyncAnthropic

Changes:
- Added timeout to models.py AsyncOpenAI client (lines 29-36)
- Added timeout to models.py AsyncAnthropic client (lines 67-74)
- Added httpx import to models.py (line 8)
- Kept simple_models.py fix as backup/reference
- Prevents 504 Gateway Timeout on PythonAnywhere
- Falls back to next model if timeout occurs

This is the CORRECT fix for production 504 errors.

Credit: User caught the mistake by asking which file is actually used"

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
Write-Host "================================================" -ForegroundColor Green
Write-Host "✅ REAL FIX DEPLOYED TO GITHUB!" -ForegroundColor Green
Write-Host ""
Write-Host "What was fixed:" -ForegroundColor Yellow
Write-Host "  ✅ models.py (ACTUALLY USED)" -ForegroundColor Green
Write-Host "  ✅ AsyncOpenAI with 20s timeout" -ForegroundColor Green
Write-Host "  ✅ AsyncAnthropic with 20s timeout" -ForegroundColor Green
Write-Host ""
Write-Host "What was wrong before:" -ForegroundColor Yellow
Write-Host "  ❌ Fixed simple_models.py (not used!)" -ForegroundColor Red
Write-Host "  ❌ Production still had no timeout" -ForegroundColor Red
Write-Host "  ❌ 504 errors would have continued" -ForegroundColor Red
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
Write-Host "Great catch asking about which file is actually used" -ForegroundColor Green
Write-Host "That question saved us from deploying a useless fix" -ForegroundColor Green
Write-Host ""

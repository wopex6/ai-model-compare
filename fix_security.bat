@echo off
echo ========================================
echo SECURITY FIX - Remove Exposed API Keys
echo ========================================
echo.

echo Step 1: Remove files with exposed keys from git
git rm --cached test_gpt_direct.py
git rm --cached gpt.py

echo.
echo Step 2: Add files to .gitignore
echo test_gpt_direct.py >> .gitignore
echo gpt.py >> .gitignore

echo.
echo Step 3: Commit the changes
git commit -m "Security: Remove files with exposed API keys"

echo.
echo Step 4: Push to GitHub
git push origin main

echo.
echo ========================================
echo SECURITY FIX COMPLETE
echo ========================================
echo.
echo NEXT STEPS:
echo 1. Regenerate your OpenAI API key at: https://platform.openai.com/api-keys
echo 2. Update your .env file with the new key
echo 3. Delete test_gpt_direct.py and gpt.py from your local machine (optional)
echo 4. Then proceed with deployment
echo.
pause

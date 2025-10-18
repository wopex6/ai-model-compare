# 🤖 Automated UI Testing Guide

## 📋 Overview

This automated testing system uses **Playwright** to control a real browser and test your multi-user AI chatbot application. It can:

- ✅ Open your app automatically
- ✅ Click buttons and fill forms
- ✅ Take screenshots at each step
- ✅ Test all major features
- ✅ Generate detailed test reports
- ✅ (Optional) Use AI vision to analyze screenshots

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Playwright

```bash
pip install playwright
playwright install
```

This downloads the browser engines needed for testing.

### Step 2: Make Sure Your App is Running

```bash
python app.py
```

Your app should be accessible at `http://localhost:5000`

### Step 3: Run the Tests

```bash
python automated_test.py
```

**That's it!** The browser will open automatically and run through all tests.

---

## 📸 What the Tests Do

### Test Suite Includes:

1. **Login Screen Test**
   - Verifies login page loads correctly
   - Checks for username, password fields, and login button

2. **Login Flow Test**
   - Fills in credentials
   - Clicks login button
   - Verifies dashboard appears

3. **Personality Controls Test**
   - Checks if 4 personality buttons are visible
   - Tests clicking and activation

4. **Textarea Expansion Test**
   - Types multiple lines
   - Verifies textarea expands (1→5 lines)
   - Checks scrollbar appears after 5 lines

5. **Enter Key Behavior Test**
   - Tests Shift+Enter (new line)
   - Tests Enter alone (send message)

6. **Tab Navigation Test**
   - Switches between all tabs
   - Verifies content loads

7. **Page Refresh Test**
   - Refreshes page
   - Checks if state is restored

---

## 📊 Test Results

### During Testing:
- Browser opens and performs actions (visible)
- Console shows progress with ✅/❌ indicators
- Screenshots are saved automatically

### After Testing:
```
test_screenshots/
├── 20250109_180500_01_login_screen.png
├── 20250109_180502_02_login_filled.png
├── 20250109_180503_03_dashboard_loaded.png
├── 20250109_180505_04_personality_controls.png
├── 20250109_180506_05_personality_clicked.png
├── ... (more screenshots)
└── test_results.json
```

### Summary Output:
```
📊 TEST SUMMARY
============================================================
Total Tests: 7
✅ Passed: 6
❌ Failed: 1
Success Rate: 85.7%
============================================================
```

---

## 🎯 Advanced Usage

### Enable AI-Powered Analysis

The test script can use Claude or GPT-4V to analyze screenshots and provide insights.

**Setup for Claude:**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

**Setup for OpenAI:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**Enable in script:**
```python
# Edit automated_test.py, line ~527
USE_AI = True
AI_PROVIDER = "claude"  # or "openai"
```

**What AI adds:**
- Detailed visual analysis
- Layout issue detection
- UX feedback
- Accessibility insights

---

## 🔧 Customization

### Change Test Username/Password

Edit `automated_test.py` line ~167:
```python
def test_login_flow(self, page, username="YourUsername", password="YourPassword"):
```

### Change Base URL

Edit `automated_test.py` line ~523:
```python
BASE_URL = "http://localhost:8000"  # or your custom URL
```

### Add Custom Tests

Add new test methods to the `AutomatedTester` class:
```python
def test_my_custom_feature(self, page):
    """Test: Custom feature"""
    try:
        # Your test logic here
        page.click("#my-button")
        screenshot = self.take_screenshot(page, "my_feature")
        
        # Check results
        if some_condition:
            self.log_result("My Feature", True, "It works!", screenshot)
        else:
            self.log_result("My Feature", False, "It failed", screenshot)
    except Exception as e:
        self.log_result("My Feature", False, f"Error: {e}")
```

Then add to `run_all_tests()`:
```python
self.test_my_custom_feature(page)
```

---

## 🐛 Troubleshooting

### Issue: "Playwright not installed"
**Solution:**
```bash
pip install playwright
playwright install
```

### Issue: "Connection refused"
**Solution:**
- Make sure your Flask app is running (`python app.py`)
- Check if it's on `http://localhost:5000`

### Issue: Browser closes too quickly
**Solution:**
- The browser stays open for 10 seconds after tests
- Increase timeout in `automated_test.py` line ~459:
```python
time.sleep(30)  # Keep open for 30 seconds
```

### Issue: Tests fail on specific element
**Solution:**
- Check screenshots in `test_screenshots/` folder
- Screenshots show exactly what the browser sees
- Compare with what you expect

### Issue: "Element not found"
**Solution:**
- Increase wait times in `automated_test.py`
- Elements might load slowly
- Add more `time.sleep()` calls

---

## 📈 Continuous Testing

### Run Tests Regularly

**Option 1: Manual**
```bash
python automated_test.py
```

**Option 2: After Code Changes**
```bash
# Make changes to code
git commit -m "Update feature X"
python automated_test.py  # Verify nothing broke
```

**Option 3: Scheduled (Windows Task Scheduler)**
- Create task to run `automated_test.py` daily
- Gets email with results

---

## 🎓 Learning Resources

### Playwright Documentation
- https://playwright.dev/python/
- Comprehensive guide to browser automation

### AI Vision APIs
- Claude: https://docs.anthropic.com/claude/docs
- OpenAI: https://platform.openai.com/docs/guides/vision

---

## ✨ Features Summary

| Feature | Status | Notes |
|---------|--------|-------|
| **Browser Automation** | ✅ | Playwright-based |
| **Screenshot Capture** | ✅ | Every test step |
| **Test Reports** | ✅ | JSON + Console |
| **AI Vision Analysis** | 🔧 | Optional, requires API key |
| **Custom Tests** | ✅ | Easy to extend |
| **Headless Mode** | 🔧 | Change `headless=True` |
| **Multiple Browsers** | ✅ | Chromium, Firefox, WebKit |

---

## 🎉 Next Steps

1. **Run the basic tests** - See what works/breaks
2. **Review screenshots** - Visual evidence of issues
3. **Fix failing tests** - Use screenshots to debug
4. **Add custom tests** - Test your specific features
5. **Enable AI analysis** - Get intelligent insights (optional)

**Happy Testing!** 🧪✨

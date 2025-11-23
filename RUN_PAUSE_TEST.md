# 🧪 How to Run Pause & Resume Test

## 📋 **Prerequisites**

Make sure Flask server is running on `http://localhost:5000`

---

## 🚀 **Run the Test**

### **Option 1: Automatic (Recommended)**

In your terminal, run:

```bash
python test_pause_resume.py
```

The test will:
- ✅ Check if server is running
- ✅ Start assessment
- ✅ Answer 5 questions
- ✅ Click "Pause Assessment"
- ✅ Verify redirect to /chatchat
- ✅ Check session file saved to disk
- ✅ Return to /personality-test
- ✅ Verify resume from question 6
- ✅ Take 9 screenshots of each step

---

## 📸 **Screenshots**

After running, check these files in `test_screenshots/`:

1. `step1_welcome.png` - Welcome page
2. `step2_first_question.png` - First question
3. `step3_after_5_questions.png` - After answering 5 questions
4. `step5_after_pause.png` - After clicking pause (should show chat page)
5. `step7_resume.png` - After returning (should show question 6)
6. `step9_final.png` - Final state

---

## ✅ **Expected Results**

### **Console Output:**
```
============================================================
TESTING PERSONALITY ASSESSMENT PAUSE & RESUME
============================================================

✅ Step 1: Navigate to personality test page
   Screenshot: step1_welcome.png

✅ Step 2: Start assessment
   Screenshot: step2_first_question.png
   Progress: Progress: 1/40

✅ Step 3: Answer 5 questions
   Question 1 answered
   Question 2 answered
   Question 3 answered
   Question 4 answered
   Question 5 answered
   Screenshot: step3_after_5_questions.png
   Progress after answering: Progress: 6/40

✅ Step 4: Click 'Pause Assessment' button
   Pause button clicked!

✅ Step 5: Verify redirect to chat page
   Current URL: http://localhost:5000/chatchat
   Screenshot: step5_after_pause.png
   ✅ Successfully redirected to chat page!

✅ Step 6: Check if session file exists
   ✅ Session files found: ['test_user_12345_session.json']
   📄 Session data:
      User ID: test_user_12345
      Current Question: 6/40
      Responses: 5

✅ Step 7: Return to personality test page
   Screenshot: step7_resume.png

✅ Step 8: Verify resume functionality
   Progress after resume: Progress: 6/40
   ✅ RESUME WORKS! Continued from where we left off!

✅ Step 9: Final verification
   Screenshot: step9_final.png

============================================================
TEST SUMMARY
============================================================
✅ Started assessment
✅ Answered 5 questions
✅ Clicked pause button
✅ Redirected to: http://localhost:5000/chatchat
✅ Returned to assessment
✅ Check screenshots in test_screenshots/ folder
============================================================
```

---

## ❌ **If Test Fails**

### **Server Not Running:**
```
❌ ERROR: Flask server is not running!
Please start the Flask server first:
   python app.py

Then run this test again.
```

**Solution:** Start Flask server first!

---

### **Pause Button Not Found:**
```
❌ Pause button not found!
```

**Solution:** Check if personality_test.html has the pause button

---

### **Resume Failed:**
```
❌ RESUME FAILED! Started from beginning
```

**Solution:** Check if session persistence is working properly

---

## 🔍 **What the Test Checks**

| Test | Description | Pass Criteria |
|------|-------------|---------------|
| 1 | Start assessment | Question 1/40 appears |
| 2 | Answer 5 questions | Progress shows 6/40 |
| 3 | Click pause | No errors |
| 4 | Redirect to chat | URL contains /chatchat |
| 5 | Session saved | JSON file exists in sessions/ |
| 6 | Session data | Contains 5 responses at question 6 |
| 7 | Return to test | Page loads |
| 8 | Resume works | Shows question 6/40 (not 1/40) |

---

## 🎯 **Success Criteria**

**✅ Test PASSES if:**
- Pause redirects to /chatchat
- Session file created in personality_profiles/sessions/
- Session contains 5 responses
- Resume shows Progress: 6/40 (not 1/40)
- All 9 screenshots captured

**❌ Test FAILS if:**
- Stays on assessment page after pause
- No session file created
- Resume starts from question 1
- Any step throws an error

---

## 📂 **Files Created**

### **Session File:**
```
personality_profiles/sessions/test_user_XXXXX_session.json
```

### **Screenshots:**
```
test_screenshots/
├── step1_welcome.png
├── step2_first_question.png
├── step3_after_5_questions.png
├── step5_after_pause.png
├── step7_resume.png
└── step9_final.png
```

---

## 💡 **Tips**

1. **Watch the browser!** Test runs with `headless=False` and `slow_mo=500` so you can see what's happening
2. **Check screenshots** if something goes wrong
3. **Read console output** for detailed step-by-step info
4. **Session files** are saved in `personality_profiles/sessions/`

---

## 🐛 **Debugging**

If test fails, check:

1. **Flask server running?**
   ```bash
   curl http://localhost:5000
   ```

2. **Session directory exists?**
   ```bash
   ls personality_profiles/sessions/
   ```

3. **Pause button exists?**
   - Check personality_test.html line 97

4. **Resume logic working?**
   - Check personality_profiler.py _load_active_sessions()

---

*Created: October 31, 2025 - 23:11*  
*Test Duration: ~30 seconds*  
*Browser: Chromium (non-headless for visibility)*

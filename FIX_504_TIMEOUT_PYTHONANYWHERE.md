# Fix 504 Gateway Timeout on PythonAnywhere

## **Error:**
```
POST https://trabcd.pythonanywhere.com/scientist/chat 504 (Gateway Time-out)
Error: SyntaxError: Unexpected token '<', "<html>..." is not valid JSON
```

---

## **Root Cause:**

### **Primary Issue: AI API Timeout**
- AI API call (OpenAI/Anthropic) takes >30 seconds
- PythonAnywhere web worker times out
- Returns HTML error page instead of JSON
- Frontend tries to parse HTML as JSON → Error

### **PythonAnywhere Limits:**
- **Free tier:** 100 seconds CPU time/day
- **Basic tier:** Request timeout ~30-60 seconds
- **Worker limits:** Limited concurrent requests
- **SQLite:** Can lock under concurrent load

---

## **Solutions:**

### **1. Add Timeout to AI API Calls** 🔴 **CRITICAL**

<function_calls>
<invoke name="grep_search">
<parameter name="SearchPath">c:\Users\trabc\CascadeProjects\ai-model-compare - Claude

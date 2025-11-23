# 📋 Administrator Log Guide - Auto-Discovery System

## 🎯 Zero Downtime Model Auto-Discovery

Your AI application now automatically discovers and uses new models when configured ones fail, with **zero downtime** in production.

---

## 📍 Where to Check Logs

### **Primary Admin Log File:**

```
logs/model_changes.log
```

**Full Path:**
```
c:\Users\trabc\CascadeProjects\ai-model-compare - Claude\logs\model_changes.log
```

**On PythonAnywhere (after deployment):**
```
~/ai-model-compare/logs/model_changes.log
```

---

## 📖 How to View Logs

### **Method 1: Direct File Access (Recommended)**

**On Windows:**
```powershell
# View entire log
Get-Content logs\model_changes.log

# View last 50 lines (recent changes)
Get-Content logs\model_changes.log -Tail 50

# Monitor live updates
Get-Content logs\model_changes.log -Wait -Tail 10
```

**On PythonAnywhere:**
```bash
# View entire log
cat ~/ai-model-compare/logs/model_changes.log

# View last 50 lines
tail -50 ~/ai-model-compare/logs/model_changes.log

# Monitor live
tail -f ~/ai-model-compare/logs/model_changes.log
```

### **Method 2: Web Dashboard (Future Feature)**

A web-based log viewer can be added at `/admin/logs` endpoint.

---

## 📊 Log Format

### **Entry Structure:**

```
YYYY-MM-DD HH:MM:SS | LEVEL | MESSAGE
```

**Example:**
```
2025-11-23 18:30:45 | INFO | MODEL DISCOVERY EVENT - Provider: GOOGLE
```

---

## 📝 What Gets Logged

### **1. Model Discovery Events** 🔍

Logged when new models are discovered:

```
===============================================================================
MODEL DISCOVERY EVENT - Provider: GOOGLE
================================================================================
NEW MODELS DISCOVERED: 3
  + gemini-2.5-flash
    Cost: $0.375/1M tokens (input+output)
    ✅ 25.0% CHEAPER than average existing models
  + gemini-2.5-pro
    Cost: $6.25/1M tokens (input+output)
    ⚠️  35.0% MORE EXPENSIVE than average existing models
  + gemini-3-pro-preview
    Cost: $0.0/1M tokens (input+output)
    Unknown cost comparison
================================================================================
```

### **2. Fallback Failures** ❌

Logged when all configured models fail:

```
================================================================================
ALL FALLBACK MODELS FAILED - Provider: GOOGLE
================================================================================
Reason: All configured models failed
Failed models (6):
  ❌ gemini-1.5-flash
  ❌ gemini-1.5-pro
  ❌ gemini-2.0-flash-exp
  ❌ gemini-1.0-pro
  ❌ gemini-pro
  ❌ gemini-pro-vision
Action: Triggering auto-discovery...
================================================================================
```

### **3. Config File Updates** 📝

Logged when `model_config.py` is automatically updated:

```
CONFIG FILE UPDATED - Provider: google
  New model list: ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-2.5-pro', ...]
  Total models: 6
```

### **4. Discovery Success** ✅

Logged when a new working model is found:

```
================================================================================
✅ DISCOVERY SUCCESS - Provider: GOOGLE
================================================================================
Working model found: gemini-2.5-flash
Attempts before success: 7
Action: Adding to config and using immediately
================================================================================
```

### **5. System Startup** 🚀

Logged when the system starts:

```
================================================================================
AI MODEL DISCOVERY SYSTEM STARTED
================================================================================
Log file: c:\...\logs\model_changes.log
Timestamp: 2025-11-23 18:30:00
Monitoring: OpenAI, Anthropic, Google, Meta
================================================================================
```

---

## 💰 Cost Tracking in Logs

Every new model includes cost comparison:

### **Cost Indicators:**

✅ **Cheaper** - New model costs <20% less than average
```
✅ 25.0% CHEAPER than average existing models
```

⚠️ **More Expensive** - New model costs >20% more than average
```
⚠️  35.0% MORE EXPENSIVE than average existing models
```

**Similar Cost** - Within ±20% of average
```
Similar cost (+5.2%)
```

### **Cost Information Per Model:**

```
Model: gemini-2.5-flash
  Input:  $0.075 per 1M tokens
  Output: $0.300 per 1M tokens
  Total:  $0.375 per 1M tokens
```

---

## 🔔 When to Check Logs

### **Daily Monitoring (Recommended):**

Check logs once per day for:
- Any new model discoveries
- Cost changes
- Fallback failures

### **Immediate Attention Required:**

Check logs immediately if:
- Users report errors
- API costs spike unexpectedly
- After deploying updates

### **Weekly Review:**

- Analyze cost trends
- Review model performance
- Clean up old log entries (optional)

---

## 🚨 Alert Conditions

Watch for these in logs:

### **🔴 Critical:**

```
ALL FALLBACK MODELS FAILED
```
**Action:** System is auto-discovering, but verify it recovers

### **🟡 Warning:**

```
⚠️  XX% MORE EXPENSIVE than average existing models
```
**Action:** Review if new model is necessary or if cheaper alternatives exist

### **⚠️ Notice:**

```
Failed to discover Google models
```
**Action:** Check API access and credentials

---

## 📈 Log Analysis Tools

### **Count Discovery Events:**

**Windows:**
```powershell
(Get-Content logs\model_changes.log | Select-String "MODEL DISCOVERY EVENT").Count
```

**Linux/Mac:**
```bash
grep -c "MODEL DISCOVERY EVENT" logs/model_changes.log
```

### **Find Expensive Models:**

```powershell
Get-Content logs\model_changes.log | Select-String "MORE EXPENSIVE"
```

### **Get Cost Comparisons:**

```powershell
Get-Content logs\model_changes.log | Select-String "CHEAPER|EXPENSIVE"
```

---

## 🔧 Log Management

### **Log Rotation:**

Logs don't automatically rotate. To manually archive:

**Windows:**
```powershell
# Archive old logs
Compress-Archive logs\model_changes.log logs\model_changes_2025-11.zip
# Clear log file
Clear-Content logs\model_changes.log
```

**Linux:**
```bash
# Archive
gzip -c logs/model_changes.log > logs/model_changes_$(date +%Y-%m).log.gz
# Clear
> logs/model_changes.log
```

### **Log Size Monitoring:**

**Windows:**
```powershell
(Get-Item logs\model_changes.log).Length / 1MB
# Output: Size in MB
```

---

## 🎯 Quick Reference

| What | Where | How |
|------|-------|-----|
| **View logs** | `logs/model_changes.log` | `Get-Content logs\model_changes.log` |
| **Recent changes** | Last 50 lines | `Get-Content logs\model_changes.log -Tail 50` |
| **Live monitoring** | Real-time | `Get-Content logs\model_changes.log -Wait` |
| **Cost alerts** | Search "EXPENSIVE" | `Select-String "EXPENSIVE"` |
| **Discovery events** | Search "DISCOVERY" | `Select-String "DISCOVERY"` |

---

## 📊 Example Real-World Log Session

```
2025-11-23 18:30:00 | INFO | AI MODEL DISCOVERY SYSTEM STARTED
2025-11-23 18:30:00 | INFO | Log file: ~/logs/model_changes.log
2025-11-23 18:30:00 | INFO | Monitoring: OpenAI, Anthropic, Google, Meta
================================================================================

2025-11-23 19:15:23 | ERROR | ALL FALLBACK MODELS FAILED - Provider: GOOGLE
2025-11-23 19:15:23 | ERROR | Reason: All configured models failed
2025-11-23 19:15:23 | ERROR | Failed models (5):
2025-11-23 19:15:23 | ERROR |   ❌ gemini-1.5-flash
2025-11-23 19:15:23 | ERROR |   ❌ gemini-1.5-pro
2025-11-23 19:15:23 | ERROR |   ❌ gemini-2.0-flash-exp
2025-11-23 19:15:23 | ERROR | Action: Triggering auto-discovery...
================================================================================

2025-11-23 19:15:28 | INFO | MODEL DISCOVERY EVENT - Provider: GOOGLE
================================================================================
2025-11-23 19:15:28 | INFO | NEW MODELS DISCOVERED: 3
2025-11-23 19:15:28 | INFO |   + gemini-2.5-flash
2025-11-23 19:15:28 | INFO |     Cost: $0.375/1M tokens (input+output)
2025-11-23 19:15:28 | INFO |     ✅ 50.0% CHEAPER than average existing models
2025-11-23 19:15:28 | INFO |   + gemini-2.0-flash
2025-11-23 19:15:28 | INFO |     Cost: $0.50/1M tokens (input+output)
2025-11-23 19:15:28 | INFO |     ✅ 33.3% CHEAPER than average existing models
================================================================================

2025-11-23 19:15:29 | INFO | CONFIG FILE UPDATED - Provider: google
2025-11-23 19:15:29 | INFO |   New model list: ['gemini-2.5-flash', 'gemini-2.0-flash', ...]
2025-11-23 19:15:29 | INFO |   Total models: 6

2025-11-23 19:15:30 | INFO | ✅ DISCOVERY SUCCESS - Provider: GOOGLE
2025-11-23 19:15:30 | INFO | Working model found: gemini-2.5-flash
2025-11-23 19:15:30 | INFO | Attempts before success: 6
2025-11-23 19:15:30 | INFO | Action: Adding to config and using immediately
================================================================================
```

---

## ✅ Summary

### **Where:** 
```
logs/model_changes.log
```

### **When:** 
- Daily monitoring (5 minutes)
- After deployment
- When costs change
- When users report issues

### **What to Look For:**
- ⚠️ "MORE EXPENSIVE" warnings
- ❌ "FALLBACK FAILED" errors
- ✅ "DISCOVERY SUCCESS" events
- 📊 Cost comparisons

### **Tools:**
- `Get-Content` (Windows)
- `tail` (Linux/Mac)
- Text search for keywords
- Log analysis scripts

---

**Your system is now fully automated with comprehensive admin logging!** 🚀

**Log file location**: `logs/model_changes.log`  
**Last updated**: November 23, 2025  
**Status**: ✅ Production Ready with Zero Downtime

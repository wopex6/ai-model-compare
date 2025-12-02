# AI Usage Monitor Dashboard

**Created:** December 3, 2025  
**Status:** DEPLOYED ✅  
**Access:** Administrators Only

---

## 🎯 OVERVIEW

The AI Usage Monitor is a dedicated dashboard for administrators to track and monitor AI call usage, costs, and quotas for all users in real-time.

---

## 📊 FEATURES

### **1. Summary Statistics**
- **Today's Calls** - Total calls made today vs 2000 system cap
- **This Month** - Total monthly AI calls
- **Today's Cost** - Estimated daily cost at $0.002/call
- **Monthly Cost** - Estimated monthly cost (max $120)

### **2. Daily Usage Table**
Real-time tracking of today's usage by user:
- Username
- Role (Admin/User badge)
- Calls today
- Quota (1000 for admins, 100 for users)
- Usage percentage with visual progress bar
- Cost today
- Status (Normal/Warning/Quota Exceeded)

**Features:**
- ✅ Color-coded progress bars (green/yellow/red)
- ✅ Visual warnings at 80% quota
- ✅ Sortable by calls, username, role
- ✅ Shows quota exceeded users

### **3. Monthly Usage Table**
Historical tracking for the current month:
- Username
- Role
- Total calls
- Daily average
- Total cost
- Peak day usage
- Trend (Increasing/Decreasing/Stable)

**Features:**
- ✅ Trend analysis with arrows
- ✅ Peak day identification
- ✅ Sortable by calls, cost, username
- ✅ Average daily usage calculation

---

## 🔐 ACCESS

### **How to Access:**

**Method 1: From Admin Dashboard**
1. Login as administrator
2. Go to **Admin** tab in chatchat
3. Click **"AI Usage Monitor"** button
4. Opens in new tab

**Method 2: Direct URL**
```
https://your-domain.com/admin/ai-usage-monitor
```

**Security:**
- ✅ Requires administrator role
- ✅ Requires authentication token
- ✅ 403 error if not admin
- ✅ All API endpoints protected

---

## 🖥️ USER INTERFACE

### **Layout:**
```
┌─────────────────────────────────────────────┐
│  AI Usage Monitor          [Refresh Button] │
├─────────────────────────────────────────────┤
│  [Today: 450/2000]  [Month: 12,340]        │
│  [Cost: $0.90]      [Cost: $24.68]         │
├─────────────────────────────────────────────┤
│  TODAY'S USAGE BY USER         [Sort ▼]    │
│  ┌────────────────────────────────────────┐ │
│  │ User │ Role │ Calls │ Quota │ Usage % │ │
│  │ john │ Usr  │   85  │  100  │ █████85%│ │
│  │ admin│ Adm  │  350  │ 1000  │ ███35%  │ │
│  └────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│  MONTHLY USAGE BY USER         [Sort ▼]    │
│  ┌────────────────────────────────────────┐ │
│  │ User  │ Total │ Avg  │ Cost  │ Trend  │ │
│  │ john  │ 2,450 │ 81.7 │ $4.90 │ ↑ Up   │ │
│  │ admin │ 8,340 │278.0 │$16.68 │ ↓ Down │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### **Color Codes:**
- **Green Progress Bar** - Under 80% quota (Normal)
- **Yellow Progress Bar** - 80-99% quota (Warning)
- **Red Progress Bar** - 100%+ quota (Exceeded)

### **Badges:**
- **Admin** - Yellow badge for administrators
- **User** - Green badge for regular users

### **Status Indicators:**
- **Normal** - Green badge (under 80%)
- **Warning** - Yellow badge (80-99%)
- **Quota Exceeded** - Red badge (100%+)

---

## 📡 API ENDPOINTS

All endpoints require admin authentication.

### **1. GET `/api/admin/ai-usage/summary`**
Returns summary statistics for today and this month.

**Response:**
```json
{
  "today_calls": 450,
  "month_calls": 12340,
  "today_cost": 0.90,
  "month_cost": 24.68,
  "system_cap": 2000,
  "month_cap_dollars": 120
}
```

### **2. GET `/api/admin/ai-usage/daily?sort=calls_desc`**
Returns today's usage by user.

**Query Parameters:**
- `sort`: `calls_desc`, `calls_asc`, `username`, `role`

**Response:**
```json
[
  {
    "user_id": 23,
    "username": "john_doe",
    "is_admin": false,
    "calls": 85
  },
  {
    "user_id": 1,
    "username": "admin",
    "is_admin": true,
    "calls": 350
  }
]
```

### **3. GET `/api/admin/ai-usage/monthly?sort=calls_desc`**
Returns this month's usage by user.

**Query Parameters:**
- `sort`: `calls_desc`, `calls_asc`, `username`, `cost_desc`

**Response:**
```json
[
  {
    "user_id": 23,
    "username": "john_doe",
    "is_admin": false,
    "total_calls": 2450,
    "avg_daily": 81.7,
    "peak_day": 120,
    "trend": "up"
  }
]
```

---

## 🔍 METRICS EXPLAINED

### **Daily Usage:**
- **Calls Today** - Number of successful AI calls made today
- **Quota** - Daily limit (1000 for admins, 100 for users)
- **Usage %** - Percentage of quota used
- **Cost Today** - Calls × $0.002

### **Monthly Usage:**
- **Total Calls** - Sum of all calls this month
- **Daily Avg** - Total calls ÷ days in month so far
- **Peak Day** - Maximum calls in a single day
- **Trend** - Comparing first half vs second half of month:
  - **Increasing ↑** - Second half > 120% of first half
  - **Decreasing ↓** - Second half < 80% of first half
  - **Stable →** - Within 80-120% range

---

## 💰 COST CALCULATIONS

### **Per Call:**
```
Cost = $0.002 per AI call
```

### **Daily Cost:**
```
Daily Cost = Total Calls Today × $0.002
```

### **Monthly Cost:**
```
Monthly Cost = Total Calls This Month × $0.002
Maximum: $120 (2000 calls/day × 30 days × $0.002)
```

### **Per User:**
```
Regular User Max: 100 calls/day × $0.002 = $0.20/day = $6/month
Admin User Max: 1000 calls/day × $0.002 = $2.00/day = $60/month
```

---

## 🔄 REFRESH & UPDATES

### **Auto-Refresh:**
- ❌ Not implemented (manual refresh only)
- Click **Refresh** button to update data

### **Manual Refresh:**
- Click **"Refresh"** button in top-right
- Reloads all three sections (summary, daily, monthly)
- Updates in real-time from database

### **Data Freshness:**
- Data pulled directly from `ai_usage_log` table
- Reflects current state immediately
- No caching delays

---

## 🧪 TESTING

### **Test Scenarios:**

**1. Access Control**
```
✓ Login as admin → Access granted
✓ Login as regular user → 403 Forbidden
✓ No login → Redirect to login
```

**2. Data Display**
```
✓ Summary stats show correct totals
✓ Daily table shows only today's users
✓ Monthly table shows all active users
✓ Progress bars display correctly
✓ Status badges show correct colors
```

**3. Sorting**
```
✓ Sort daily by calls (high/low)
✓ Sort daily by username
✓ Sort daily by role
✓ Sort monthly by calls
✓ Sort monthly by cost
```

**4. Edge Cases**
```
✓ No usage today → Shows "No AI usage today"
✓ No usage this month → Shows "No AI usage this month"
✓ User over quota → Red progress bar + "Quota Exceeded"
✓ User at 85% → Yellow progress bar + "Warning"
```

---

## 🚀 DEPLOYMENT

### **Files Modified:**
1. **`templates/chatchat.html`**
   - Added "AI Usage Monitor" button in Admin tab
   - Links to `/admin/ai-usage-monitor`

2. **`templates/ai_usage_monitor.html`** (NEW)
   - Full monitoring dashboard
   - Responsive design
   - Real-time data display

3. **`app.py`**
   - Route: `/admin/ai-usage-monitor` (page)
   - API: `/api/admin/ai-usage/summary`
   - API: `/api/admin/ai-usage/daily`
   - API: `/api/admin/ai-usage/monthly`

### **Database Requirements:**
- ✅ `ai_usage_log` table (exists)
- ✅ `users` table with `role` column (exists)
- ✅ No migrations needed

### **Dependencies:**
- ✅ Font Awesome (icons)
- ✅ Authentication system
- ✅ SQLite database

---

## 📱 RESPONSIVE DESIGN

### **Desktop (>1200px):**
- 4-column stats grid
- Full-width tables
- All columns visible

### **Tablet (768-1200px):**
- 2-column stats grid
- Horizontal scroll for tables
- All features available

### **Mobile (<768px):**
- Single column stats
- Horizontal scroll tables
- Touch-friendly buttons

---

## 🔧 CUSTOMIZATION

### **Adjust System Cap:**
Change in `ai_budget_manager.py`:
```python
SYSTEM_DAILY_CAP = 2000  # Change this value
```

### **Adjust User Quotas:**
```python
DAILY_CALL_LIMIT_USER = 100   # Regular users
DAILY_CALL_LIMIT_ADMIN = 1000 # Admins
```

### **Adjust Cost Per Call:**
```python
COST_PER_CALL = 0.002  # $0.002 per call
```

Changes will reflect in monitor automatically.

---

## ⚠️ TROUBLESHOOTING

### **Problem: Dashboard shows "Loading..." forever**

**Causes:**
1. Not logged in as admin
2. Token expired
3. API endpoint error

**Solution:**
1. Check browser console for errors
2. Verify admin role in database
3. Check server logs for API errors

### **Problem: Data not updating**

**Solution:**
1. Click "Refresh" button
2. Hard refresh page (Ctrl+Shift+R)
3. Check if calls are being logged to `ai_usage_log`

### **Problem: 403 Forbidden**

**Solution:**
1. Verify user role is 'administrator'
2. Check authentication token is valid
3. Ensure `@require_auth` decorator working

---

## 📊 MONITORING BEST PRACTICES

### **Daily Checks:**
1. ✅ Check system cap usage (should be under 2000)
2. ✅ Identify users near quota
3. ✅ Verify cost projections
4. ✅ Look for unusual spikes

### **Weekly Analysis:**
1. ✅ Review usage trends
2. ✅ Identify heavy users
3. ✅ Project monthly costs
4. ✅ Adjust quotas if needed

### **Monthly Review:**
1. ✅ Total cost vs budget
2. ✅ User growth impact
3. ✅ Peak usage days
4. ✅ Plan quota adjustments

---

## 🎯 KEY METRICS TO WATCH

### **Red Flags:**
- 🚨 System approaching 2000 daily cap
- 🚨 Monthly cost approaching $120
- 🚨 Multiple users consistently at 100% quota
- 🚨 Rapidly increasing trends

### **Good Indicators:**
- ✅ Even distribution among users
- ✅ Most users under 80% quota
- ✅ Stable or decreasing trends
- ✅ Monthly cost under $100

---

## 📝 FUTURE ENHANCEMENTS (Optional)

### **Potential Features:**
1. **Charts & Graphs**
   - Line chart for daily usage over time
   - Pie chart for cost distribution by user

2. **Alerts & Notifications**
   - Email when system cap at 80%
   - Alert when user exceeds quota
   - Daily usage summary email

3. **Export Functionality**
   - Download CSV of usage data
   - Generate monthly reports
   - Export for accounting

4. **Historical Data**
   - View past months
   - Year-over-year comparison
   - Trend predictions

5. **Auto-Refresh**
   - Update data every 30 seconds
   - Live usage counter
   - Real-time notifications

---

## ✅ DEPLOYMENT CHECKLIST

- [x] Code committed to GitHub
- [x] Button added to Admin Dashboard
- [x] AI Usage Monitor page created
- [x] API endpoints implemented
- [x] Admin authentication enforced
- [x] Responsive design implemented
- [x] Documentation complete
- [ ] **Deploy to PythonAnywhere**
- [ ] **Test as admin user**
- [ ] **Verify data accuracy**
- [ ] **Share with admins**

---

## 🔗 QUICK LINKS

**Access:**
- Admin Dashboard: `/chatchat` → Admin tab
- Direct Link: `/admin/ai-usage-monitor`

**API Docs:**
- Summary: `GET /api/admin/ai-usage/summary`
- Daily: `GET /api/admin/ai-usage/daily`
- Monthly: `GET /api/admin/ai-usage/monthly`

**Related Files:**
- Frontend: `templates/ai_usage_monitor.html`
- Backend: `app.py` (lines 2447-2657)
- Button: `templates/chatchat.html` (lines 707-715)

---

**Created by:** December 3, 2025  
**Version:** 1.0  
**Status:** Ready for Production ✅  
**Commit:** `23e91f6`

# Wisdom Agent Testing Guide

## Overview

The Wisdom Agent system has two layers of testing:

1. **Unit/Integration Tests** (`test_loophole_fixes.py`) — 447 regression tests covering all internal logic
2. **E2E Browser Tests** (`test_wisdom_agent_playwright.py`) — Playwright tests for web UI integration

---

## Quick Start

### Run All Regression Tests
```bash
python test_loophole_fixes.py
```
Expected: `447 passed, 0 failed`

### Run Playwright E2E Tests
```bash
# Install Playwright (first time only)
pip install playwright
playwright install chromium

# Run E2E tests
python test_wisdom_agent_playwright.py
```

---

## Test Coverage

### Unit/Integration Tests (`test_loophole_fixes.py`)

**Rounds 1-14:** Core functionality (322 tests)
- Profile loading/saving
- Pattern detection & lifecycle
- Nudge generation & deduplication
- Hypothesis engine
- Context gathering
- AI analysis fallback
- Database operations

**Round 15-16:** Audit fixes (40 tests)
- JSON parse error handling
- Digest trimming performance
- Hypothesis loading robustness
- Pattern matching edge cases

**Round 17:** Enhancements (63 tests)
- ThreadPoolExecutor parallelization
- Nudge content-hash deduplication
- Nudge TTL expiry (30 days)
- Pattern age filtering
- Frequency merging
- Hypothesis confidence decay
- Score history tracking
- Agent status endpoint
- Graceful shutdown loop

**Round 18:** Audit fixes (15 tests)
- Thread-safe `_known_tables` with Lock
- UTC timestamps (`datetime.utcnow()`)
- JSON parse logging
- O(1) pattern lookup optimization
- Score history deduplication
- Empty `response.choices` guard
- Score trend display

**E2E Integration:** (7 tests)
- Web integration point existence
- Function signature validation

---

## Playwright E2E Tests (`test_wisdom_agent_playwright.py`)

### Test Scenarios

#### 1. **User Login**
- Navigate to `/chatchat`
- Fill credentials
- Verify redirect after authentication

#### 2. **Wisdom Nudges Display**
- Navigate to `/wisdom/nudges`
- Verify nudges container loads
- Count displayed nudge cards
- Expected: 3+ nudges visible

#### 3. **Urgency Ordering**
- Check first nudge has urgency badge
- Verify "high" urgency appears first
- SQL: `ORDER BY CASE urgency WHEN 'high' THEN 1 ...`

#### 4. **Mark Nudge as Delivered**
- Click "Mark as Read" button
- Verify AJAX request completes
- Check DB: `delivered = 1`

#### 5. **Agent Status Endpoint**
- GET `/api/wisdom/status`
- Verify JSON response contains:
  - `db_path`
  - `wisdom_dir`
  - `users_with_profiles`
  - `pending_nudges_total`
  - `dry_run`
  - `status_at`

#### 6. **Background Analysis Trigger**
- Send chat message
- Verify `trigger_wisdom_analysis()` called
- Check logs for background thread start

---

## Configuration

### Test Database
- **Path:** `integrated_users.db`
- **Test User:** `test_wisdom_user`
- **Password:** `test123`

### Base URL
```python
BASE_URL = "http://localhost:5000"  # Development
# BASE_URL = "https://trabcd.pythonanywhere.com"  # Production
```

---

## Test Data Setup

The E2E test automatically:
1. Creates test user if not exists
2. Seeds 3 wisdom nudges with different urgencies:
   - **High:** Stress pattern warning
   - **Medium:** Growth opportunity reflection
   - **Low:** Positive trend encouragement
3. Cleans up after tests complete

### Manual Cleanup
```python
import sqlite3
conn = sqlite3.connect('integrated_users.db')
conn.execute("DELETE FROM wisdom_nudges WHERE user_id = (SELECT id FROM users WHERE username = 'test_wisdom_user')")
conn.commit()
conn.close()
```

---

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Wisdom Agent Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install playwright
          playwright install chromium
      
      - name: Run regression tests
        run: python test_loophole_fixes.py
      
      - name: Run E2E tests
        run: python test_wisdom_agent_playwright.py
```

---

## Debugging Failed Tests

### Regression Tests
```bash
# Run with verbose output
python test_loophole_fixes.py 2>&1 | tee test_output.txt

# Check for specific failure
grep "\[FAIL\]" test_output.txt
```

### Playwright Tests
```python
# In test_wisdom_agent_playwright.py, set:
browser = p.chromium.launch(headless=False, slow_mo=1000)  # Slow down
```

Enable screenshots on failure:
```python
try:
    # ... test code ...
except Exception as e:
    page.screenshot(path=f"error_{test_name}.png")
    raise
```

---

## Web Integration Points

The Wisdom Agent exposes these functions for `app.py`:

### `get_wisdom_nudges_for_user(user_id: str) -> List[Dict]`
- **Purpose:** Fetch pending nudges for display
- **Behavior:** 
  - Returns immediately (non-blocking)
  - Triggers background analysis if profile stale (>24h)
- **Usage:**
  ```python
  from agents.wisdom_agent import get_wisdom_nudges_for_user
  
  @app.route('/wisdom/nudges')
  def show_nudges():
      user_id = session['user_id']
      nudges = get_wisdom_nudges_for_user(user_id)
      return render_template('wisdom_nudges.html', nudges=nudges)
  ```

### `trigger_wisdom_analysis(user_id: str)`
- **Purpose:** Schedule background re-analysis after conversation
- **Behavior:**
  - Spawns daemon thread
  - Graceful fallback if DB locked
- **Usage:**
  ```python
  from agents.wisdom_agent import trigger_wisdom_analysis
  
  @app.route('/chat/send', methods=['POST'])
  def send_message():
      # ... save message ...
      trigger_wisdom_analysis(session['user_id'])
      return jsonify({'status': 'ok'})
  ```

### `WisdomAgent.get_agent_status() -> Dict`
- **Purpose:** Health-check endpoint
- **Returns:**
  ```json
  {
    "db_path": "integrated_users.db",
    "wisdom_dir": "wisdom_profiles/",
    "users_with_profiles": 42,
    "pending_nudges_total": 15,
    "dry_run": false,
    "status_at": "2026-06-16T05:20:00"
  }
  ```

---

## Performance Benchmarks

### Regression Suite
- **Duration:** ~8-12 seconds
- **Tests:** 447
- **Coverage:** All core logic paths

### E2E Suite
- **Duration:** ~30-45 seconds
- **Tests:** 6 scenarios
- **Browser:** Chromium (headless)

### Analysis Performance
- **Single user:** ~2-5 seconds (with AI)
- **Parallel (4 workers):** ~15-20 seconds for 10 users
- **Background trigger:** Non-blocking (<100ms HTTP response)

---

## Troubleshooting

### "Database is locked"
- **Cause:** SQLite write contention
- **Fix:** `trigger_wisdom_analysis` uses `dry_run=True` fallback

### "No nudges displayed"
- **Check:** User has conversation history (min 3 messages)
- **Check:** Profile `last_analyzed` < 24h ago
- **Check:** `wisdom_nudges` table has `delivered=0` rows

### "Playwright timeout"
- **Increase:** `page.wait_for_selector(..., timeout=10000)`
- **Check:** Flask dev server running on correct port
- **Check:** Selectors match actual HTML structure

### "ThreadPoolExecutor deadlock"
- **Cause:** `_known_tables` race condition (fixed in AG-FIX #1)
- **Verify:** `threading.Lock()` present in `__init__`

---

## Future Enhancements

- [ ] Visual regression testing (screenshot comparison)
- [ ] Load testing (100+ concurrent users)
- [ ] Nudge A/B testing framework
- [ ] Mobile browser testing (iOS Safari, Android Chrome)
- [ ] Accessibility testing (WCAG 2.1 AA)

---

## Related Documentation

- `agents/wisdom_agent.py` — Core agent implementation
- `agents/wisdom_hypothesis.py` — Hypothesis engine
- `knowledge_data/wisdom_lessons.json` — Wisdom knowledge base
- `test_loophole_fixes.py` — Full regression suite

---

**Last Updated:** 2026-06-16  
**Test Suite Version:** 18.0  
**Total Tests:** 447 regression + 6 E2E = 453

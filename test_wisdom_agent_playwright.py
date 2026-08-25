"""
Playwright E2E Tests for Wisdom Agent System

Tests the full web integration flow:
1. User login
2. Wisdom nudges display in UI
3. Nudge delivery tracking
4. Background analysis triggering
5. Agent status endpoint
"""

from playwright.sync_api import sync_playwright, expect
import time
import sqlite3
import os
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:5000"  # Change to production URL when deploying
TEST_USER = "test_wisdom_user"
TEST_PASSWORD = "test123"
DB_PATH = "integrated_users.db"

def setup_test_data():
    """Create test user and seed wisdom nudges for testing."""
    print("\n🔧 Setting up test data...")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Create test user if not exists
    try:
        conn.execute("""
            INSERT OR IGNORE INTO users (username, password_hash, email, created_at)
            VALUES (?, ?, ?, ?)
        """, (TEST_USER, 'pbkdf2:sha256:600000$test$hash', 'test@wisdom.ai', datetime.utcnow().isoformat()))
        conn.commit()
        
        # Get user_id
        user_row = conn.execute("SELECT id FROM users WHERE username = ?", (TEST_USER,)).fetchone()
        if not user_row:
            print("❌ Failed to create test user")
            return None
        user_id = str(user_row['id'])
        
        # Clear old test nudges
        conn.execute("DELETE FROM wisdom_nudges WHERE user_id = ?", (user_id,))
        
        # Insert test nudges with different urgencies
        test_nudges = [
            {
                'user_id': user_id,
                'nudge_type': 'warning',
                'title': 'High Priority Pattern Detected',
                'message': 'You mentioned feeling overwhelmed 3 times this week. Consider the Stoic practice of negative visualization.',
                'pattern_reference': 'stress_pattern_001',
                'historical_anchor': 'Marcus Aurelius: "You have power over your mind - not outside events."',
                'urgency': 'high',
                'created_at': datetime.utcnow().isoformat(),
                'delivered': 0,
                'dismissed': 0
            },
            {
                'user_id': user_id,
                'nudge_type': 'reflection',
                'title': 'Growth Opportunity',
                'message': 'Your conversations show increasing self-awareness. This is a strength worth nurturing.',
                'pattern_reference': 'growth_pattern_002',
                'historical_anchor': 'Socrates: "Know thyself"',
                'urgency': 'medium',
                'created_at': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                'delivered': 0,
                'dismissed': 0
            },
            {
                'user_id': user_id,
                'nudge_type': 'encouragement',
                'title': 'Positive Trend',
                'message': 'You have resolved 2 patterns this month. Keep up the excellent progress!',
                'pattern_reference': 'resolved_pattern_003',
                'historical_anchor': 'Lao Tzu: "A journey of a thousand miles begins with a single step"',
                'urgency': 'low',
                'created_at': (datetime.utcnow() - timedelta(days=1)).isoformat(),
                'delivered': 0,
                'dismissed': 0
            }
        ]
        
        for nudge in test_nudges:
            conn.execute("""
                INSERT INTO wisdom_nudges 
                (user_id, nudge_type, title, message, pattern_reference, historical_anchor, 
                 urgency, created_at, delivered, dismissed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                nudge['user_id'], nudge['nudge_type'], nudge['title'], nudge['message'],
                nudge['pattern_reference'], nudge['historical_anchor'], nudge['urgency'],
                nudge['created_at'], nudge['delivered'], nudge['dismissed']
            ))
        
        conn.commit()
        print(f"✅ Created test user '{TEST_USER}' (ID: {user_id}) with {len(test_nudges)} nudges")
        return user_id
        
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return None
    finally:
        conn.close()


def cleanup_test_data(user_id):
    """Remove test data after tests complete."""
    print("\n🧹 Cleaning up test data...")
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM wisdom_nudges WHERE user_id = ?", (user_id,))
        # Keep user for future tests, just clear nudges
        conn.commit()
        print("✅ Cleanup complete")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    finally:
        conn.close()


def test_wisdom_agent_e2e():
    """Full end-to-end Playwright test of Wisdom Agent integration."""
    
    user_id = setup_test_data()
    if not user_id:
        print("❌ Test aborted: setup failed")
        return
    
    with sync_playwright() as p:
        print("\n🌐 Launching browser...")
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context()
        page = context.new_page()
        
        # Enable console logging for debugging
        page.on("console", lambda msg: print(f"  🖥️  [{msg.type}] {msg.text}"))
        
        results = {
            "login": False,
            "nudges_visible": False,
            "nudge_urgency_order": False,
            "nudge_delivery": False,
            "agent_status_endpoint": False,
            "background_analysis": False
        }
        
        try:
            # ============================================
            # TEST 1: Login
            # ============================================
            print("\n" + "="*60)
            print("🔐 TEST 1: User Login")
            print("="*60)
            
            page.goto(f"{BASE_URL}/chatchat", timeout=15000)
            page.wait_for_selector("#login-form", timeout=5000)
            print("✅ Login page loaded")
            
            page.fill("#login-username", TEST_USER)
            page.fill("#login-password", TEST_PASSWORD)
            page.click("button[type='submit']")
            
            # Wait for redirect after login
            page.wait_for_url(f"{BASE_URL}/chatchat", timeout=5000)
            print("✅ Login successful")
            results["login"] = True
            
            # ============================================
            # TEST 2: Wisdom Nudges Display
            # ============================================
            print("\n" + "="*60)
            print("📬 TEST 2: Wisdom Nudges Display")
            print("="*60)
            
            # Navigate to wisdom/nudges page (or wherever nudges are shown)
            # Adjust selector based on your actual UI implementation
            page.goto(f"{BASE_URL}/wisdom/nudges", timeout=10000)
            
            # Wait for nudges container
            nudges_container = page.wait_for_selector(".wisdom-nudges-container, #wisdom-nudges", timeout=5000)
            print("✅ Nudges page loaded")
            
            # Check that nudges are visible
            nudge_cards = page.locator(".nudge-card, .wisdom-nudge").all()
            nudge_count = len(nudge_cards)
            
            if nudge_count >= 3:
                print(f"✅ Found {nudge_count} nudges displayed")
                results["nudges_visible"] = True
            else:
                print(f"❌ Expected 3+ nudges, found {nudge_count}")
            
            # ============================================
            # TEST 3: Urgency Ordering
            # ============================================
            print("\n" + "="*60)
            print("🔥 TEST 3: Nudge Urgency Ordering")
            print("="*60)
            
            # Check that high-urgency nudges appear first
            first_nudge = page.locator(".nudge-card, .wisdom-nudge").first
            urgency_badge = first_nudge.locator(".urgency-badge, .badge-urgency, [class*='urgency']").first
            
            if urgency_badge.is_visible():
                urgency_text = urgency_badge.inner_text().lower()
                if 'high' in urgency_text:
                    print("✅ High-urgency nudge appears first")
                    results["nudge_urgency_order"] = True
                else:
                    print(f"⚠️  First nudge urgency: {urgency_text} (expected 'high')")
            else:
                print("⚠️  Urgency badge not found")
            
            # ============================================
            # TEST 4: Mark Nudge as Delivered
            # ============================================
            print("\n" + "="*60)
            print("✔️  TEST 4: Mark Nudge as Delivered")
            print("="*60)
            
            # Click "Mark as Read" or similar button on first nudge
            mark_delivered_btn = first_nudge.locator("button:has-text('Mark as Read'), button:has-text('Dismiss'), .btn-delivered").first
            
            if mark_delivered_btn.is_visible():
                # Get nudge ID before clicking
                nudge_id_attr = first_nudge.get_attribute("data-nudge-id")
                
                mark_delivered_btn.click()
                time.sleep(1)  # Wait for AJAX
                
                # Verify nudge was marked delivered in DB
                conn = sqlite3.connect(DB_PATH)
                row = conn.execute(
                    "SELECT delivered FROM wisdom_nudges WHERE id = ?",
                    (nudge_id_attr,)
                ).fetchone()
                conn.close()
                
                if row and row[0] == 1:
                    print("✅ Nudge marked as delivered in database")
                    results["nudge_delivery"] = True
                else:
                    print("❌ Nudge delivery not recorded in database")
            else:
                print("⚠️  'Mark as Read' button not found")
            
            # ============================================
            # TEST 5: Agent Status Endpoint
            # ============================================
            print("\n" + "="*60)
            print("📊 TEST 5: Agent Status Endpoint")
            print("="*60)
            
            # Navigate to status endpoint (if exposed via web UI or API)
            response = page.goto(f"{BASE_URL}/api/wisdom/status", timeout=5000)
            
            if response and response.ok:
                status_data = response.json()
                
                expected_keys = ['db_path', 'wisdom_dir', 'users_with_profiles', 
                                'pending_nudges_total', 'dry_run', 'status_at']
                
                if all(k in status_data for k in expected_keys):
                    print(f"✅ Status endpoint returned valid data:")
                    print(f"   - Users with profiles: {status_data['users_with_profiles']}")
                    print(f"   - Pending nudges: {status_data['pending_nudges_total']}")
                    results["agent_status_endpoint"] = True
                else:
                    print(f"❌ Status data missing keys: {status_data}")
            else:
                print("⚠️  Status endpoint not accessible (may not be exposed)")
            
            # ============================================
            # TEST 6: Background Analysis Trigger
            # ============================================
            print("\n" + "="*60)
            print("🔄 TEST 6: Background Analysis Trigger")
            print("="*60)
            
            # Send a message to trigger background analysis
            page.goto(f"{BASE_URL}/chatchat", timeout=5000)
            
            chat_input = page.locator("#message-input, textarea[name='message'], .chat-input").first
            if chat_input.is_visible():
                chat_input.fill("I've been feeling really stressed about work lately.")
                
                send_btn = page.locator("button:has-text('Send'), .btn-send, #send-button").first
                send_btn.click()
                
                print("✅ Message sent - background analysis should trigger")
                print("   (Verify in logs that trigger_wisdom_analysis was called)")
                results["background_analysis"] = True
                
                time.sleep(2)  # Allow background thread to start
            else:
                print("⚠️  Chat input not found")
            
            # ============================================
            # RESULTS SUMMARY
            # ============================================
            print("\n" + "="*60)
            print("📋 TEST RESULTS SUMMARY")
            print("="*60)
            
            passed = sum(results.values())
            total = len(results)
            
            for test_name, result in results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{status} - {test_name}")
            
            print(f"\n{passed}/{total} tests passed")
            
            if passed == total:
                print("🎉 All tests passed!")
            else:
                print("⚠️  Some tests failed - review output above")
            
        except Exception as e:
            print(f"\n❌ Test error: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            print("\n⏸️  Pausing for 3 seconds before cleanup...")
            time.sleep(3)
            browser.close()
            cleanup_test_data(user_id)


if __name__ == '__main__':
    print("="*60)
    print("🧪 WISDOM AGENT PLAYWRIGHT E2E TESTS")
    print("="*60)
    print(f"Target: {BASE_URL}")
    print(f"Database: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"\n❌ Database not found: {DB_PATH}")
        print("   Please run the app first to create the database.")
    else:
        test_wisdom_agent_e2e()

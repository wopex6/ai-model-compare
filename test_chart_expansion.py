"""
Test to check if charts expand infinitely on the analytics page.
Takes screenshots at intervals to compare chart container heights.
"""
from playwright.sync_api import sync_playwright
import time

BASE_URL = "https://trabcd.pythonanywhere.com"
ADMIN_USER = "Wai Tse"
ADMIN_PASSWORD = "123"

def test_chart_expansion():
    """Test if chart containers expand over time"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1280, 'height': 720})
        
        # Login first
        print("Logging in...")
        page.goto(f"{BASE_URL}/")
        page.wait_for_load_state('networkidle')
        
        # Fill login
        page.fill('input[name="username"]', ADMIN_USER)
        page.fill('input[name="password"]', ADMIN_PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_timeout(3000)
        
        # Navigate to analytics
        print("Navigating to analytics...")
        page.goto(f"{BASE_URL}/admin/analytics")
        page.wait_for_timeout(5000)
        
        # Get initial chart container height
        heights = []
        
        for i in range(4):
            print(f"\n--- Measurement {i+1} ---")
            
            # Get chart container dimensions
            usage_container = page.query_selector('#usage-chart-container')
            context_container = page.query_selector('#context-chart-container')
            
            if usage_container:
                box = usage_container.bounding_box()
                if box:
                    print(f"Usage chart container: {box['width']:.0f}x{box['height']:.0f}")
                    heights.append(box['height'])
                else:
                    print("Usage chart container: no bounding box")
            else:
                print("Usage chart container: NOT FOUND")
            
            if context_container:
                box = context_container.bounding_box()
                if box:
                    print(f"Context chart container: {box['width']:.0f}x{box['height']:.0f}")
            
            # Take screenshot
            page.screenshot(path=f"chart_test_{i+1}.png")
            print(f"Screenshot saved: chart_test_{i+1}.png")
            
            if i < 3:
                print("Waiting 35 seconds for auto-refresh...")
                page.wait_for_timeout(35000)
        
        # Check if heights are expanding
        print("\n" + "="*50)
        print("RESULTS")
        print("="*50)
        print(f"Heights recorded: {heights}")
        
        if len(heights) >= 2:
            if heights[-1] > heights[0] * 1.1:  # More than 10% increase
                print("❌ FAIL: Chart container is expanding!")
                print(f"   Initial: {heights[0]:.0f}px, Final: {heights[-1]:.0f}px")
                print(f"   Increase: {((heights[-1]/heights[0])-1)*100:.1f}%")
            else:
                print("✅ PASS: Chart container height is stable")
                print(f"   Height range: {min(heights):.0f}px - {max(heights):.0f}px")
        
        browser.close()

if __name__ == "__main__":
    test_chart_expansion()

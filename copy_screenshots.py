#!/usr/bin/env python3
"""Copy screenshots to viewable location"""

import shutil
import os
from pathlib import Path

# Create destination directory
dest_dir = Path("screenshots_viewable")
dest_dir.mkdir(exist_ok=True)

# Copy key screenshots
source_dir = Path("test_screenshots")

key_screenshots = [
    "00_initial_page.png",
    "01_login_screen.png",
    "02_dashboard_after_login.png",
    "03_admin_tab_highlighted.png",
    "04_admin_tab_opened.png",
    "05_bulk_delete_NOT_FOUND.png",
    "06_deleted_user_highlighted.png",
    "07_delete_forever_button_highlighted.png",
    "08_full_admin_page.png"
]

print("Copying screenshots...")
copied = 0
for screenshot in key_screenshots:
    source = source_dir / screenshot
    dest = dest_dir / screenshot
    if source.exists():
        shutil.copy2(source, dest)
        print(f"  ✅ Copied: {screenshot}")
        copied += 1
    else:
        print(f"  ❌ Not found: {screenshot}")

print(f"\n✅ Copied {copied}/{len(key_screenshots)} screenshots")
print(f"📁 Location: {dest_dir.absolute()}")

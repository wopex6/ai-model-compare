import shutil
import os

# Copy screenshots to viewable folder
screenshots = [
    'highlight_1_welcome.png',
    'highlight_2_question1.png',
    'highlight_3_back_to_q1.png',
    'highlight_4_final.png'
]

os.makedirs('screenshots_viewable', exist_ok=True)

for screenshot in screenshots:
    src = f'test_screenshots/{screenshot}'
    dst = f'screenshots_viewable/{screenshot}'
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f'✅ Copied {screenshot}')
    else:
        print(f'❌ Not found: {screenshot}')

print('\n✅ All screenshots copied to screenshots_viewable/')

// Add this to multi_user_app.js setupEventListeners() function around line 448

// Take Personality Test button
const takePersonalityTestBtn = document.getElementById('take-personality-test-btn');
if (takePersonalityTestBtn) {
    takePersonalityTestBtn.addEventListener('click', () => {
        console.log('Take Personality Test button clicked');
        window.open('/personality-test', '_blank', 'width=1000,height=800');
    });
}

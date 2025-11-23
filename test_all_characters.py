"""
Test All 8 Characters - Quick verification script
"""
import asyncio
from ai_compare.character_factory import CharacterFactory

async def test_character(char_id):
    """Test a single character"""
    try:
        print(f"\n{'='*60}")
        print(f"Testing: {char_id}")
        print(f"{'='*60}")
        
        # Create character
        bot = CharacterFactory.create_character(char_id)
        info = CharacterFactory.get_character_info(char_id)
        
        print(f"✓ Character created: {info['display_name']}")
        print(f"  Tagline: {info['tagline']}")
        print(f"  Theme: {info['theme']['primary_color']}")
        
        # Test daily insight
        insight = bot.get_daily_insight()
        print(f"✓ Daily insight: {insight[:80]}...")
        
        # Test chat
        response = await bot.chat("Hello! Tell me about yourself.")
        print(f"✓ Chat response: {response.get('response', '')[:100]}...")
        
        # Test stats
        stats = bot.get_character_stats()
        print(f"✓ Stats retrieved: {len(stats)} fields")
        
        return {"status": "PASS", "name": info['display_name']}
        
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return {"status": "FAIL", "error": str(e)}

async def test_all():
    """Test all characters"""
    print("\n" + "="*60)
    print("TESTING ALL 8 CHARACTERS")
    print("="*60)
    
    char_ids = CharacterFactory.get_all_character_ids()
    print(f"\nFound {len(char_ids)} characters to test")
    
    results = {}
    for char_id in char_ids:
        results[char_id] = await test_character(char_id)
        await asyncio.sleep(0.5)  # Brief pause between tests
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results.values() if r["status"] == "PASS")
    failed = sum(1 for r in results.values() if r["status"] == "FAIL")
    
    print(f"\nTotal: {len(results)} characters")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ✗")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
    else:
        print("\n⚠️  Some tests failed:")
        for char_id, result in results.items():
            if result["status"] == "FAIL":
                print(f"  - {char_id}: {result.get('error', 'Unknown error')}")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(test_all())
    print("\n" + "="*60)
    print("Testing complete!")
    print("="*60 + "\n")

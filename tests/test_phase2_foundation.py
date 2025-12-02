"""
Phase 2 Foundation Tests - CRITICAL Must-Haves

Tests the core functionality that MUST work for Phase 2 to be solid:
1. End-to-end flow (extraction → storage → AI prompt)
2. Pattern extraction accuracy
3. Historical context preservation
4. Performance (<100ms extraction)
5. No duplicate contexts
6. Error handling
"""

import sys
import os
import time
import sqlite3

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from smart_response.explicit_context_handler import ExplicitContextHandler
from smart_response.personality_trend_analyzer import PersonalityTrendAnalyzer
from smart_response.conversation_context import ConversationContextManager


class TestPhase2Foundation:
    """Foundation tests for Phase 2 core functionality"""
    
    def __init__(self):
        self.db = sqlite3.connect(':memory:')  # In-memory test database
        self.setup_test_database()
        self.handler = ExplicitContextHandler(self.db)
        self.analyzer = PersonalityTrendAnalyzer(self.db)
        self.context_manager = ConversationContextManager(self.db)
        
    def setup_test_database(self):
        """Initialize test database with required tables"""
        cursor = self.db.cursor()
        
        # The handlers will create their own tables
        # We just need to ensure clean state
        self.db.commit()
    
    def test_pattern_extraction_all_types(self):
        """Test all extraction pattern types work correctly"""
        print("\n" + "="*80)
        print("TEST: Pattern Extraction - All Types")
        print("="*80)
        
        test_cases = [
            # (message, expected_type, expected_value_contains, description)
            ("I'm feeling happy", 'emotional_state', 'happy', "Basic emotion"),
            ("I feel stressed", 'emotional_state', 'stressed', "Alternative emotion pattern"),
            ("I'm anxious", 'emotional_state', 'anxious', "Short emotion"),
            ("My goal is to learn Python", 'goal', 'learn Python', "Explicit goal"),
            ("I want to succeed", 'goal', 'succeed', "Intention goal"),
            ("I hope to become a scientist", 'goal', 'become a scientist', "Aspiration goal"),
            ("I prefer morning work", 'preference', 'morning work', "Preference"),
            ("I like coding", 'preference', 'coding', "Like preference"),
            ("I need help", 'need', 'help', "Stated need"),
            
            # Quote handling (CRITICAL after recent fix)
            ('"I want success"', 'goal', 'success', "Quote-wrapped goal"),
            ('I\'m "stressed"', 'emotional_state', 'stressed', "Quoted emotion"),
        ]
        
        passed = 0
        failed = 0
        
        for i, (message, expected_type, expected_value, description) in enumerate(test_cases, 1):
            result = self.handler.extract_explicit_context(user_id=1, character="coach", message=message)
            
            if expected_type is None:
                if len(result) == 0:
                    print(f"✓ Test {i}: {description} - Correctly no match")
                    passed += 1
                else:
                    print(f"✗ Test {i}: {description} - FALSE POSITIVE: {result}")
                    failed += 1
            else:
                if len(result) > 0:
                    found = any(expected_value.lower() in item['value'].lower() 
                               and item['type'] == expected_type 
                               for item in result)
                    if found:
                        print(f"✓ Test {i}: {description} - Extracted: {result[0]['value']}")
                        passed += 1
                    else:
                        print(f"✗ Test {i}: {description} - Wrong extraction: {result}")
                        failed += 1
                else:
                    print(f"✗ Test {i}: {description} - FALSE NEGATIVE: No match")
                    failed += 1
        
        print(f"\nResults: {passed} passed, {failed} failed")
        return failed == 0
    
    def test_historical_context_preservation(self):
        """Verify old emotions are preserved, not deleted"""
        print("\n" + "="*80)
        print("TEST: Historical Context Preservation")
        print("="*80)
        
        # Clear any existing data
        cursor = self.db.cursor()
        cursor.execute('DELETE FROM explicit_context WHERE user_id = 99')
        self.db.commit()
        
        # Send 3 different emotions
        emotions = ["happy", "sad", "angry"]
        for emotion in emotions:
            self.handler.extract_explicit_context(99, "coach", f"I'm {emotion}")
        
        # Check database
        cursor.execute('''
            SELECT context_value, active FROM explicit_context
            WHERE user_id=99 AND context_type='emotional_state'
            ORDER BY timestamp
        ''')
        results = cursor.fetchall()
        
        print(f"\nStored emotions: {len(results)} rows")
        for i, (value, active) in enumerate(results, 1):
            status = "ACTIVE" if active else "inactive"
            print(f"  {i}. {value} ({status})")
        
        # Verify
        if len(results) == 3:
            print("\n✓ All 3 emotions preserved in database")
            if results[0][1] == 0 and results[1][1] == 0 and results[2][1] == 1:
                print("✓ Correct active flags (old=0, current=1)")
                return True
            else:
                print("✗ FAIL: Active flags incorrect")
                return False
        else:
            print(f"✗ FAIL: Expected 3 rows, got {len(results)}")
            return False
    
    def test_no_duplicate_contexts(self):
        """Ensure same context isn't stored multiple times as active"""
        print("\n" + "="*80)
        print("TEST: No Duplicate Active Contexts")
        print("="*80)
        
        # Clear data
        cursor = self.db.cursor()
        cursor.execute('DELETE FROM explicit_context WHERE user_id = 50')
        self.db.commit()
        
        # Send same emotion twice
        self.handler.extract_explicit_context(50, "coach", "I'm stressed")
        self.handler.extract_explicit_context(50, "coach", "I'm stressed")
        
        # Count active "stressed" entries
        cursor.execute('''
            SELECT COUNT(*) FROM explicit_context
            WHERE user_id=50 AND context_value='stressed' AND active=1
        ''')
        active_count = cursor.fetchone()[0]
        
        # Count total "stressed" entries
        cursor.execute('''
            SELECT COUNT(*) FROM explicit_context
            WHERE user_id=50 AND context_value='stressed'
        ''')
        total_count = cursor.fetchone()[0]
        
        print(f"\nTotal 'stressed' entries: {total_count}")
        print(f"Active 'stressed' entries: {active_count}")
        
        if active_count == 1:
            print("\n✓ Only 1 active entry (no duplicates)")
            return True
        else:
            print(f"\n✗ FAIL: Found {active_count} active entries (should be 1)")
            return False
    
    def test_extraction_performance(self):
        """Ensure extraction is fast (<100ms)"""
        print("\n" + "="*80)
        print("TEST: Extraction Performance")
        print("="*80)
        
        message = "I'm feeling stressed about deadlines and my goal is to succeed"
        
        # Warm-up run
        self.handler.extract_explicit_context(1, "coach", message)
        
        # Timed runs
        runs = 10
        times = []
        
        for _ in range(runs):
            start = time.time()
            result = self.handler.extract_explicit_context(1, "coach", message)
            duration = time.time() - start
            times.append(duration * 1000)  # Convert to ms
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"\nExtraction performance ({runs} runs):")
        print(f"  Average: {avg_time:.1f}ms")
        print(f"  Max: {max_time:.1f}ms")
        print(f"  Target: <100ms")
        
        if avg_time < 100:
            print(f"\n✓ Performance acceptable (avg {avg_time:.1f}ms < 100ms)")
            return True
        else:
            print(f"\n⚠ Warning: Performance slow (avg {avg_time:.1f}ms >= 100ms)")
            return False
    
    def test_error_handling(self):
        """System should handle invalid input gracefully"""
        print("\n" + "="*80)
        print("TEST: Error Handling")
        print("="*80)
        
        test_cases = [
            (None, "None input"),
            ("", "Empty string"),
            ("   ", "Just whitespace"),
            ("a" * 10000, "Very long message"),
            ("🎉😊🔥", "Only emojis"),
            ("<script>alert('xss')</script>", "XSS attempt"),
        ]
        
        passed = 0
        failed = 0
        
        for message, description in test_cases:
            try:
                result = self.handler.extract_explicit_context(1, "coach", message)
                if isinstance(result, list):
                    print(f"✓ {description}: Handled gracefully (returned list)")
                    passed += 1
                else:
                    print(f"✗ {description}: Unexpected return type: {type(result)}")
                    failed += 1
            except Exception as e:
                print(f"✗ {description}: CRASHED with {type(e).__name__}: {e}")
                failed += 1
        
        print(f"\nResults: {passed} passed, {failed} failed")
        return failed == 0
    
    def test_personality_analysis_integration(self):
        """Test personality pattern analysis detects traits"""
        print("\n" + "="*80)
        print("TEST: Personality Pattern Analysis")
        print("="*80)
        
        # Clear data
        cursor = self.db.cursor()
        cursor.execute('DELETE FROM explicit_context WHERE user_id = 88')
        cursor.execute('DELETE FROM inferred_traits WHERE user_id = 88')
        self.db.commit()
        
        # Simulate clear neurotic pattern (5 messages)
        messages = [
            "I'm stressed",
            "I'm worried",
            "I'm anxious",
            "My goal is excellence",
            "I want success"
        ]
        
        print("\nSending messages to build pattern:")
        for i, msg in enumerate(messages, 1):
            self.handler.extract_explicit_context(88, "coach", msg)
            print(f"  {i}. {msg}")
        
        # Trigger analysis
        print("\nRunning pattern analysis...")
        traits = self.analyzer.analyze_patterns(88, "coach", days=14)
        
        print(f"\nTraits detected: {len(traits)}")
        for trait in traits:
            print(f"  - {trait['category']}: {trait['trait']} "
                  f"(confidence: {trait['confidence']*100:.0f}%)")
        
        # Check for neurotic
        neurotic = [t for t in traits if t['trait'] == 'neurotic']
        
        if neurotic and neurotic[0]['confidence'] >= 0.60:
            print(f"\n✓ Neurotic trait detected (confidence: {neurotic[0]['confidence']*100:.0f}%)")
            return True
        else:
            print(f"\n✗ FAIL: Neurotic not detected or confidence too low")
            print(f"   Expected: 3 stress emotions → neurotic trait ≥60%")
            return False
    
    def test_context_in_ai_prompt(self):
        """Verify context is included in AI prompt format"""
        print("\n" + "="*80)
        print("TEST: Context in AI Prompt")
        print("="*80)
        
        # Clear and set up test context
        cursor = self.db.cursor()
        cursor.execute('DELETE FROM explicit_context WHERE user_id = 77')
        self.db.commit()
        
        # Add explicit context
        self.handler.extract_explicit_context(77, "coach", "I'm feeling stressed")
        self.handler.extract_explicit_context(77, "coach", "My goal is to succeed")
        
        # Get context for AI
        context = self.context_manager.get_context_for_ai(77, "coach", [])
        
        # Format for prompt
        prompt = self.context_manager.format_context_for_prompt(context)
        
        print("\nGenerated AI prompt context:")
        print("-" * 80)
        print(prompt)
        print("-" * 80)
        
        # Verify context is present
        has_stressed = 'stressed' in prompt.lower()
        has_succeed = 'succeed' in prompt.lower()
        has_priority = 'explicit' in prompt.lower() or 'critical' in prompt.lower()
        
        print(f"\nVerification:")
        print(f"  Contains 'stressed': {has_stressed}")
        print(f"  Contains 'succeed': {has_succeed}")
        print(f"  Has priority marker: {has_priority}")
        
        if has_stressed and has_succeed:
            print("\n✓ Context included in AI prompt")
            return True
        else:
            print("\n✗ FAIL: Context missing from AI prompt")
            return False
    
    def run_all_tests(self):
        """Run all foundation tests"""
        print("\n" + "="*80)
        print("PHASE 2 FOUNDATION TEST SUITE")
        print("="*80)
        
        tests = [
            ("Pattern Extraction", self.test_pattern_extraction_all_types),
            ("Historical Preservation", self.test_historical_context_preservation),
            ("No Duplicates", self.test_no_duplicate_contexts),
            ("Performance", self.test_extraction_performance),
            ("Error Handling", self.test_error_handling),
            ("Personality Analysis", self.test_personality_analysis_integration),
            ("Context in Prompt", self.test_context_in_ai_prompt),
        ]
        
        results = {}
        for name, test_func in tests:
            try:
                results[name] = test_func()
            except Exception as e:
                print(f"\n✗ EXCEPTION in {name}: {e}")
                import traceback
                traceback.print_exc()
                results[name] = False
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status}: {name}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL FOUNDATION TESTS PASSED!")
            print("Phase 2 core is SOLID!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed - needs attention")
        
        return passed == total


if __name__ == '__main__':
    tester = TestPhase2Foundation()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

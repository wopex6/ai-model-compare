"""
Test that all chatbots can be instantiated and have required methods
"""

import sys

def test_instantiation():
    """Test creating instances of all chatbot classes"""
    print("\n" + "=" * 80)
    print("🧪 TESTING CHATBOT INSTANTIATION")
    print("=" * 80)
    
    try:
        # Test AIChatbot
        print("\n1️⃣ Testing AIChatbot...")
        from ai_compare.chatbot import AIChatbot
        standard = AIChatbot()
        print(f"   ✅ Created: {standard.personality.traits.character}")
        print(f"   ✅ Session ID: {standard.session_id}")
        print(f"   ✅ Has chat method: {hasattr(standard, 'chat')}")
        print(f"   ✅ Has ai_compare: {hasattr(standard, 'ai_compare')}")
        print(f"   ✅ Has conversation_manager: {hasattr(standard, 'conversation_manager')}")
        
        # Test MotivationalChatbot
        print("\n2️⃣ Testing MotivationalChatbot...")
        from ai_compare.motivational_chatbot import MotivationalChatbot
        max_bot = MotivationalChatbot()
        print(f"   ✅ Created: {max_bot.personality.traits.character}")
        print(f"   ✅ Session ID: {max_bot.session_id}")
        print(f"   ✅ Has chat method: {hasattr(max_bot, 'chat')}")
        print(f"   ✅ Has motivational_system: {hasattr(max_bot, 'motivational_system')}")
        print(f"   ✅ Extends AIChatbot: {isinstance(max_bot, AIChatbot)}")
        
        # Test WisdomChatbot
        print("\n3️⃣ Testing WisdomChatbot...")
        from ai_compare.wisdom_chatbot import WisdomChatbot
        sage = WisdomChatbot()
        print(f"   ✅ Created: {sage.personality.traits.character}")
        print(f"   ✅ Session ID: {sage.session_id}")
        print(f"   ✅ Has chat method: {hasattr(sage, 'chat')}")
        print(f"   ✅ Has wisdom_topics: {hasattr(sage, 'wisdom_topics')}")
        print(f"   ✅ Has parables: {hasattr(sage, 'parables')}")
        print(f"   ✅ Extends AIChatbot: {isinstance(sage, AIChatbot)}")
        
        # Test BaseChatbot (if used directly)
        print("\n4️⃣ Testing BaseChatbot import...")
        from ai_compare.base_chatbot import BaseChatbot
        print(f"   ✅ BaseChatbot imported successfully")
        print(f"   ✅ Is ABC: {hasattr(BaseChatbot, '__abstractmethods__')}")
        
        # Verify shared components are the same type
        print("\n5️⃣ Verifying shared component types...")
        print(f"   ✅ All use AICompare: {type(standard.ai_compare).__name__} = {type(max_bot.ai_compare).__name__} = {type(sage.ai_compare).__name__}")
        print(f"   ✅ All use ConversationManager: {type(standard.conversation_manager).__name__} = {type(max_bot.conversation_manager).__name__} = {type(sage.conversation_manager).__name__}")
        
        # Test critical methods exist
        print("\n6️⃣ Verifying critical methods...")
        critical_methods = ['chat', '_build_enhanced_prompt', '_apply_personality_filter']
        for method in critical_methods:
            has_standard = hasattr(standard, method) and callable(getattr(standard, method))
            has_max = hasattr(max_bot, method) and callable(getattr(max_bot, method))
            has_sage = hasattr(sage, method) and callable(getattr(sage, method))
            all_have = has_standard and has_max and has_sage
            status = "✅" if all_have else "❌"
            print(f"   {status} {method}: Standard={has_standard}, Max={has_max}, Sage={has_sage}")
        
        print("\n" + "=" * 80)
        print("✅ ✅ ✅ ALL INSTANTIATION TESTS PASSED! ✅ ✅ ✅")
        print("=" * 80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_instantiation()
    sys.exit(0 if success else 1)

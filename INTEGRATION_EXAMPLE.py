"""
Example: Integrating Dynamic Knowledge System with Existing Chatbots
Shows how to add knowledge enhancement with minimal code changes
"""

# ============================================================
# EXAMPLE 1: Wisdom Sage with Knowledge Enhancement
# ============================================================

from ai_compare.chatbot import AIChatbot
from ai_compare.knowledge_enhanced_chatbot import KnowledgeEnhancedMixin
from typing import Dict

class WisdomChatbotEnhanced(KnowledgeEnhancedMixin, AIChatbot):
    """
    Wisdom Sage chatbot with dynamic knowledge expansion
    
    What changed from original:
    1. Added KnowledgeEnhancedMixin to inheritance
    2. Added self.setup_knowledge() in __init__
    3. Modified chat() to use chat_with_knowledge()
    
    That's it! Now automatically searches Taoist texts.
    """
    
    def __init__(self, personality_preset: str = "wisdom_sage", user_preset: str = "casual_learner"):
        super().__init__(personality_preset, user_preset)
        
        # NEW: Setup knowledge system (ONE LINE!)
        self.setup_knowledge("wisdom_sage")
        
        # Keep all existing code
        self.wisdom_topics = self._initialize_wisdom_topics()
        self.parables = self._initialize_parables()
        self.tao_principles = self._initialize_tao_principles()
    
    async def chat(self, user_message: str, include_context: bool = True) -> Dict:
        """
        MODIFIED: Now automatically enhanced with discovered Taoist texts
        """
        # Keep existing wisdom detection
        wisdom_response = await self._check_wisdom_request(user_message)
        if wisdom_response:
            return wisdom_response
        
        # MODIFIED: Use knowledge-enhanced chat instead of super().chat()
        # This automatically searches vector DB and adds relevant passages
        return await self.chat_with_knowledge(user_message, include_context)
    
    # All other methods stay exactly the same
    def _initialize_wisdom_topics(self):
        """Existing method - no changes"""
        return {
            "balance": ["harmony between opposing forces"],
            # ... rest of existing code
        }
    
    def _initialize_parables(self):
        """Existing method - no changes"""
        return [
            {"theme": "perspective", "parable": "..."},
            # ... rest of existing code
        ]
    
    def _initialize_tao_principles(self):
        """Existing method - no changes"""
        return {
            "wu_wei": "Action without forcing",
            # ... rest of existing code
        }
    
    async def _check_wisdom_request(self, message: str):
        """Existing method - no changes"""
        # ... existing code
        pass


# ============================================================
# EXAMPLE 2: Stoic Marcus with Knowledge Enhancement
# ============================================================

class StoicChatbotEnhanced(KnowledgeEnhancedMixin, AIChatbot):
    """
    Marcus Aurelius chatbot with automatic Meditations quotes
    """
    
    def __init__(self):
        super().__init__("stoic_philosopher", "casual_learner")
        self.setup_knowledge("stoic_philosopher")
    
    async def chat(self, user_message: str, include_context: bool = True) -> Dict:
        """Chat with knowledge from Meditations, Enchiridion, etc."""
        return await self.chat_with_knowledge(user_message, include_context)


# ============================================================
# EXAMPLE 3: Using Decorator (Even Easier!)
# ============================================================

from ai_compare.knowledge_enhanced_chatbot import with_knowledge_enhancement

@with_knowledge_enhancement("super_motivational_coach")
class MotivationalCoachEnhanced(AIChatbot):
    """
    Max with knowledge from Tony Robbins, Brendon Burchard, etc.
    
    The decorator automatically:
    - Adds knowledge mixin
    - Sets up knowledge system
    - Enhances chat() method
    
    Zero code changes needed!
    """
    
    def __init__(self):
        super().__init__("super_motivational_coach", "casual_learner")
        # That's it! Knowledge system auto-integrated by decorator


# ============================================================
# EXAMPLE 4: Manual Integration (Most Control)
# ============================================================

from ai_compare.knowledge_system import get_knowledge_system

class ManuallyIntegratedChatbot(AIChatbot):
    """
    Full manual control over knowledge integration
    Use when you want custom behavior
    """
    
    def __init__(self):
        super().__init__("wisdom_sage", "casual_learner")
        self.knowledge_system = get_knowledge_system()
        self.character_id = "wisdom_sage"
    
    async def chat(self, user_message: str, include_context: bool = True) -> Dict:
        """Manually integrate knowledge"""
        
        # 1. Search knowledge base
        knowledge_results = self.knowledge_system.search_knowledge(
            character_id=self.character_id,
            query=user_message,
            n_results=3
        )
        
        # 2. Format knowledge context
        knowledge_context = ""
        if knowledge_results:
            knowledge_context = "\n\nRELEVANT TAOIST WISDOM:\n"
            for i, result in enumerate(knowledge_results, 1):
                metadata = result['metadata']
                author = metadata.get('author', 'Unknown')
                title = metadata.get('title', 'Unknown')
                text = result['text']
                
                knowledge_context += f"\n[{i}. {title} by {author}]\n{text}\n"
            
            knowledge_context += "\nWeave this wisdom naturally into your response.\n"
        
        # 3. Add to message
        enhanced_message = user_message + knowledge_context
        
        # 4. Generate response
        response = await super().chat(enhanced_message, include_context)
        
        # 5. Add source citations
        if knowledge_results:
            sources = [
                f"{r['metadata'].get('title', 'Unknown')} by {r['metadata'].get('author', 'Unknown')}"
                for r in knowledge_results
            ]
            response['sources_consulted'] = sources
        
        return response


# ============================================================
# EXAMPLE 5: Flask Routes Integration
# ============================================================

from flask import Flask, jsonify, request
from ai_compare.knowledge_system import expand_knowledge_for_character, get_knowledge_stats

app = Flask(__name__)

# Initialize characters
wisdom_bot = WisdomChatbotEnhanced()
stoic_bot = StoicChatbotEnhanced()

@app.route('/sage/chat', methods=['POST'])
async def sage_chat_with_knowledge():
    """Sage chat now automatically uses discovered Taoist texts"""
    data = request.get_json()
    user_message = data.get('message', '')
    
    # Chat is now knowledge-enhanced automatically!
    response = await wisdom_bot.chat(user_message)
    return jsonify(response)

@app.route('/admin/expand-knowledge/<character_id>', methods=['POST'])
async def trigger_knowledge_expansion(character_id):
    """Admin endpoint to manually trigger knowledge discovery"""
    try:
        summary = await expand_knowledge_for_character(character_id, force=True)
        return jsonify({
            "success": True,
            "summary": summary
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/admin/knowledge-stats/<character_id>')
def get_character_knowledge_stats(character_id):
    """Get statistics about character's knowledge base"""
    try:
        stats = get_knowledge_stats(character_id)
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/sage/search-knowledge', methods=['POST'])
def search_sage_knowledge():
    """Search Sage Wei's knowledge base directly"""
    data = request.get_json()
    query = data.get('query', '')
    
    results = wisdom_bot.search_my_knowledge(query, n_results=5)
    
    formatted_results = []
    for result in results:
        formatted_results.append({
            "text": result['text'],
            "author": result['metadata'].get('author'),
            "title": result['metadata'].get('title'),
            "relevance": result['relevance_score']
        })
    
    return jsonify({
        "query": query,
        "results": formatted_results
    })


# ============================================================
# EXAMPLE 6: Background Task for Periodic Expansion
# ============================================================

import asyncio
from datetime import datetime

async def periodic_knowledge_expansion():
    """
    Background task to periodically expand knowledge
    Run this as a cron job or background worker
    """
    characters = [
        "wisdom_sage",
        "stoic_philosopher", 
        "super_motivational_coach"
    ]
    
    print(f"[{datetime.now()}] Starting periodic knowledge expansion")
    
    for char_id in characters:
        try:
            print(f"[{char_id}] Checking for new sources...")
            
            summary = await expand_knowledge_for_character(char_id)
            
            if summary.get('processed', 0) > 0:
                print(f"[{char_id}] ✅ Processed {summary['processed']} new sources")
                print(f"[{char_id}] New authors: {summary['new_authors']}")
            else:
                print(f"[{char_id}] No new sources found")
        
        except Exception as e:
            print(f"[{char_id}] ❌ Error: {e}")
    
    print(f"[{datetime.now()}] Expansion complete")

# Run once
# asyncio.run(periodic_knowledge_expansion())

# Or schedule with APScheduler
# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# scheduler = AsyncIOScheduler()
# scheduler.add_job(periodic_knowledge_expansion, 'cron', day_of_week='mon', hour=2)
# scheduler.start()


# ============================================================
# EXAMPLE 7: Creating Brand New Character
# ============================================================

from ai_compare.knowledge_config import create_custom_profile, register_character_profile

def create_new_buddhist_character():
    """
    Example: Creating a completely new character
    Shows how easy it is - no core code changes needed!
    """
    
    # Step 1: Define knowledge profile
    profile = create_custom_profile(
        character_name="Zen Master",
        domains=["spirituality", "philosophy"],
        authors=["Dogen", "Thich Nhat Hanh", "Shunryu Suzuki"],
        concepts=["mindfulness", "zazen", "satori", "emptiness", "compassion"],
        fields_of_study=["Zen Buddhism", "Meditation", "Buddhist Philosophy"]
    )
    
    # Step 2: Register profile
    register_character_profile("zen_master", profile)
    
    # Step 3: Create chatbot class
    @with_knowledge_enhancement("zen_master")
    class ZenMasterChatbot(AIChatbot):
        def __init__(self):
            super().__init__("wisdom_sage", "casual_learner")  # Reuse personality
    
    # Step 4: Use it!
    zen_bot = ZenMasterChatbot()
    
    # Step 5: Expand knowledge (discovers Dogen, Thich Nhat Hanh works automatically)
    # asyncio.run(zen_bot.expand_knowledge(force=True))
    
    # Step 6: Chat (automatically enhanced with discovered texts)
    # response = asyncio.run(zen_bot.chat("What is mindfulness?"))
    
    print("✅ New Zen Master character created!")
    print("   - Profile: Configured")
    print("   - Knowledge: Auto-discovers Buddhist texts")
    print("   - Chat: Enhanced with real sources")
    print("   - Total code: ~15 lines!")


# ============================================================
# EXAMPLE 8: Testing Knowledge System
# ============================================================

async def test_knowledge_system():
    """Test the knowledge system"""
    
    print("Testing Dynamic Knowledge System\n")
    print("=" * 50)
    
    # Test 1: Create and register profile
    print("\n1. Creating test profile...")
    profile = create_custom_profile(
        character_name="Test Character",
        domains=["philosophy"],
        authors=["Plato"],
        concepts=["forms", "justice", "virtue"],
        fields_of_study=["Ancient Philosophy"]
    )
    register_character_profile("test_character", profile)
    print("✅ Profile created and registered")
    
    # Test 2: Expand knowledge
    print("\n2. Expanding knowledge (discovering Plato's works)...")
    summary = await expand_knowledge_for_character("test_character", force=True)
    print(f"✅ Discovered: {summary['discovered']}")
    print(f"✅ Processed: {summary['processed']}")
    
    # Test 3: Search knowledge
    print("\n3. Searching knowledge base...")
    from ai_compare.knowledge_system import search_character_knowledge
    results = search_character_knowledge(
        "test_character",
        "What is justice?",
        n_results=3
    )
    print(f"✅ Found {len(results)} relevant passages")
    for i, result in enumerate(results, 1):
        print(f"   [{i}] {result['metadata'].get('title', 'Unknown')}")
    
    # Test 4: Get statistics
    print("\n4. Getting statistics...")
    stats = get_knowledge_stats("test_character")
    print(f"✅ Total sources: {stats['tracker']['total_sources']}")
    print(f"✅ Total chunks: {stats['vector_store']['total_chunks']}")
    print(f"✅ Authors: {stats['tracker']['authors']}")
    
    print("\n" + "=" * 50)
    print("All tests passed! System working correctly.")

# Run tests
# asyncio.run(test_knowledge_system())


if __name__ == "__main__":
    print("""
    Dynamic Knowledge System - Integration Examples
    
    This file shows 8 different ways to integrate the knowledge system:
    
    1. ✅ WisdomChatbotEnhanced - Mixin approach
    2. ✅ StoicChatbotEnhanced - Simple mixin
    3. ✅ MotivationalCoachEnhanced - Decorator approach
    4. ✅ ManuallyIntegratedChatbot - Full manual control
    5. ✅ Flask routes - API integration
    6. ✅ Background task - Periodic expansion
    7. ✅ New character - Creating from scratch
    8. ✅ Testing - Verify system works
    
    Pick the approach that fits your needs!
    
    To get started:
    1. pip install -r knowledge_requirements.txt
    2. Copy one of the examples above
    3. Run knowledge expansion
    4. Start chatting with enhanced knowledge!
    """)

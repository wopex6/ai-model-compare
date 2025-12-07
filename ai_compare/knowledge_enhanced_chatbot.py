"""
Knowledge-Enhanced Chatbot Mixin
Adds dynamic knowledge expansion to any chatbot
Simply inherit from this mixin to get knowledge capabilities
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from .knowledge_system import get_knowledge_system


class KnowledgeEnhancedMixin:
    """
    Mixin to add knowledge enhancement to any chatbot
    
    Usage:
        class MyCharacter(KnowledgeEnhancedMixin, AIChatbot):
            def __init__(self):
                super().__init__("my_personality")
                self.setup_knowledge("my_character_id")
    """
    
    def setup_knowledge(self, character_id: str):
        """Initialize knowledge system for this character"""
        self.character_id = character_id
        self.knowledge_system = get_knowledge_system()
        self._knowledge_enabled = True
    
    def enable_knowledge_enhancement(self, enabled: bool = True):
        """Enable or disable knowledge enhancement"""
        self._knowledge_enabled = enabled
    
    async def enhance_with_knowledge(self, 
                                    user_message: str,
                                    n_results: int = 3) -> str:
        """
        Enhance a user message with relevant knowledge
        Returns: Context string to add to the prompt
        """
        import time
        print(f"⏱️ [{time.time():.2f}] enhance_with_knowledge: START")
        
        if not self._knowledge_enabled:
            print(f"⏱️ [{time.time():.2f}] enhance_with_knowledge: Knowledge disabled, returning empty")
            return ""
        
        try:
            # Search knowledge base
            # FIXED: Run blocking search_knowledge() in thread pool to avoid blocking async loop
            print(f"⏱️ [{time.time():.2f}] enhance_with_knowledge: Searching knowledge system...")
            import asyncio
            results = await asyncio.to_thread(
                self.knowledge_system.search_knowledge,
                character_id=self.character_id,
                query=user_message,
                n_results=n_results
            )
            print(f"⏱️ [{time.time():.2f}] enhance_with_knowledge: Search returned {len(results) if results else 0} results")
            
            if not results:
                return ""
            
            # Format context
            context_parts = ["\n\nRELEVANT KNOWLEDGE FROM YOUR SOURCES:"]
            
            for i, result in enumerate(results, 1):
                metadata = result.get("metadata", {})
                text = result.get("text", "")
                
                author = metadata.get("author", "Unknown")
                title = metadata.get("title", "Unknown Source")
                
                context_parts.append(
                    f"\n[Source {i}: {title} by {author}]\n{text}"
                )
            
            context_parts.append(
                "\n\nUse this knowledge naturally in your response. "
                "Cite sources when directly quoting or referencing specific ideas."
            )
            
            return "\n".join(context_parts)
        
        except Exception as e:
            print(f"Knowledge enhancement error: {e}")
            return ""
    
    async def chat_with_knowledge(self, 
                                  user_message: str,
                                  include_context: bool = True) -> Dict:
        """
        Chat with automatic knowledge enhancement
        Override this in your chatbot class
        """
        import time
        print(f"⏱️ [{time.time():.2f}] STEP 11: Inside chat_with_knowledge()")
        print(f"   📚 Knowledge enabled: {self._knowledge_enabled}")
        
        # Get knowledge context
        print(f"⏱️ [{time.time():.2f}] STEP 12: Calling enhance_with_knowledge()")
        knowledge_context = await self.enhance_with_knowledge(user_message)
        print(f"⏱️ [{time.time():.2f}] STEP 13: enhance_with_knowledge() returned")
        print(f"   📖 Knowledge context length: {len(knowledge_context) if knowledge_context else 0}")
        
        # Combine with user message
        enhanced_message = user_message
        if knowledge_context:
            enhanced_message = user_message + knowledge_context
        
        # Call parent chat method (must be implemented by child)
        print(f"⏱️ [{time.time():.2f}] STEP 14: Calling parent (super) chat()")
        if hasattr(super(), 'chat'):
            result = await super().chat(enhanced_message, include_context)
            print(f"⏱️ [{time.time():.2f}] STEP 15: Parent chat() returned")
            return result
        else:
            raise NotImplementedError("Child class must implement chat() method")
    
    def get_knowledge_stats(self) -> Dict:
        """Get knowledge statistics for this character"""
        if not self._knowledge_enabled:
            return {"error": "Knowledge system not enabled"}
        
        return self.knowledge_system.get_character_stats(self.character_id)
    
    async def expand_knowledge(self, force: bool = False) -> Dict:
        """Trigger knowledge expansion for this character"""
        if not self._knowledge_enabled:
            return {"error": "Knowledge system not enabled"}
        
        return await self.knowledge_system.expand_character_knowledge(
            self.character_id,
            force=force
        )
    
    def search_my_knowledge(self, 
                           query: str,
                           n_results: int = 5,
                           filter_author: Optional[str] = None) -> List[Dict]:
        """Search this character's knowledge base"""
        if not self._knowledge_enabled:
            return []
        
        return self.knowledge_system.search_knowledge(
            character_id=self.character_id,
            query=query,
            n_results=n_results,
            filter_author=filter_author
        )
    
    def add_custom_knowledge(self,
                            text: str,
                            author: str,
                            title: str,
                            field: Optional[str] = None) -> bool:
        """Add custom text to this character's knowledge base"""
        if not self._knowledge_enabled:
            return False
        
        return self.knowledge_system.add_manual_source(
            character_id=self.character_id,
            text=text,
            author=author,
            title=title,
            field=field
        )


# ============================================================
# Example Integration with Existing Chatbots
# ============================================================

class KnowledgeEnhancedChatbot(KnowledgeEnhancedMixin):
    """
    Base class for knowledge-enhanced chatbots
    Inherit from this to get both AIChatbot and knowledge capabilities
    """
    
    def __init__(self, 
                 character_id: str,
                 personality_preset: str,
                 user_preset: str = "casual_learner"):
        # Import here to avoid circular dependency
        from .chatbot import AIChatbot
        
        # Initialize parent chatbot
        self.personality_preset = personality_preset
        self.user_preset = user_preset
        
        # Initialize as AIChatbot would
        # (This is a simplified version - adapt based on actual AIChatbot)
        
        # Setup knowledge system
        self.setup_knowledge(character_id)
    
    async def chat(self, user_message: str, include_context: bool = True) -> Dict:
        """
        Override to add automatic knowledge enhancement
        """
        # This should call the actual AIChatbot.chat() method
        # with knowledge enhancement
        return await self.chat_with_knowledge(user_message, include_context)


# ============================================================
# Decorator for Easy Integration
# ============================================================

def with_knowledge_enhancement(character_id: str):
    """
    Decorator to add knowledge enhancement to any chatbot class
    
    Usage:
        @with_knowledge_enhancement("stoic_philosopher")
        class MarcusChatbot(AIChatbot):
            pass
    """
    def decorator(cls):
        # Create a new class that inherits from both
        class KnowledgeEnhancedClass(KnowledgeEnhancedMixin, cls):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.setup_knowledge(character_id)
            
            async def chat(self, user_message: str, include_context: bool = True) -> Dict:
                return await self.chat_with_knowledge(user_message, include_context)
        
        # Preserve class metadata
        KnowledgeEnhancedClass.__name__ = cls.__name__
        KnowledgeEnhancedClass.__module__ = cls.__module__
        
        return KnowledgeEnhancedClass
    
    return decorator


# ============================================================
# Simple Integration Helper
# ============================================================

async def add_knowledge_to_response(character_id: str, 
                                   user_message: str,
                                   base_response: str,
                                   n_sources: int = 2) -> Tuple[str, List[Dict]]:
    """
    Simple helper to add knowledge citations to a response
    
    Returns: (enhanced_response, sources_used)
    """
    system = get_knowledge_system()
    
    # Search for relevant knowledge
    results = system.search_knowledge(
        character_id=character_id,
        query=user_message,
        n_results=n_sources
    )
    
    if not results:
        return base_response, []
    
    # Format sources as citations
    citations = []
    for i, result in enumerate(results, 1):
        metadata = result.get("metadata", {})
        author = metadata.get("author", "Unknown")
        title = metadata.get("title", "Unknown")
        
        citations.append({
            "number": i,
            "author": author,
            "title": title,
            "excerpt": result.get("text", "")[:150] + "...",
            "relevance": result.get("relevance_score", 0.0)
        })
    
    # Add citations to response
    enhanced_response = base_response
    
    if citations:
        enhanced_response += "\n\n---\n**Sources Referenced:**\n"
        for cite in citations:
            enhanced_response += f"\n{cite['number']}. *{cite['title']}* by {cite['author']}"
    
    return enhanced_response, citations

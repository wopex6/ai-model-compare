"""
Character Factory - Centralized character creation
Single source of truth for all character instantiation
"""
from typing import Dict, Optional
from .base_enhanced_chatbot import BaseEnhancedChatbot
from .character_configs import CHARACTER_CONFIGS


class CharacterFactory:
    """
    Factory for creating character chatbots
    Eliminates code duplication and ensures consistency
    """
    
    # Character registry - maps character_id to personality_preset and optional custom class
    CHARACTER_REGISTRY = {
        # New system characters (use BaseEnhancedChatbot)
        "zen_master": {"personality": "zen_master", "class": None},
        "business_coach": {"personality": "business_coach", "class": None},
        "life_coach": {"personality": "life_coach", "class": None},
        "scientist": {"personality": "scientist", "class": None},
        "psychologist": {"personality": "psychologist", "class": None},
        
        # Legacy characters (use existing custom classes)
        "super_motivational_coach": {"personality": "super_motivational_coach", "class": "MotivationalChatbot"},
        "wisdom_sage": {"personality": "wisdom_sage", "class": "WisdomChatbot"},
        "stoic_philosopher": {"personality": "stoic_philosopher", "class": "StoicChatbot"}
    }
    
    @staticmethod
    def create_character(character_id: str, user_preset: str = "casual_learner"):
        """
        Create a character chatbot by ID
        
        Args:
            character_id: Character identifier (e.g., "zen_master")
            user_preset: User personality preset
            
        Returns:
            Configured chatbot instance (BaseEnhancedChatbot or legacy class)
            
        Raises:
            ValueError: If character_id not recognized
        """
        if character_id not in CharacterFactory.CHARACTER_REGISTRY:
            raise ValueError(f"Unknown character: {character_id}. Available: {list(CharacterFactory.CHARACTER_REGISTRY.keys())}")
        
        # Get registry entry
        registry_entry = CharacterFactory.CHARACTER_REGISTRY[character_id]
        personality_preset = registry_entry["personality"]
        custom_class = registry_entry.get("class")
        
        # If has custom class, use existing implementation
        if custom_class:
            if custom_class == "MotivationalChatbot":
                from .motivational_chatbot import MotivationalChatbot
                return MotivationalChatbot(personality_preset, user_preset)
            elif custom_class == "WisdomChatbot":
                from .wisdom_chatbot import WisdomChatbot
                return WisdomChatbot(personality_preset, user_preset)
            elif custom_class == "StoicChatbot":
                from .stoic_chatbot import StoicChatbot
                return StoicChatbot(personality_preset, user_preset)
        
        # Otherwise use new base class
        config = CHARACTER_CONFIGS.get(character_id, {})
        character = BaseEnhancedChatbot(
            character_id=character_id,
            personality_preset=personality_preset,
            user_preset=user_preset,
            config=config
        )
        
        return character
    
    @staticmethod
    def get_all_character_ids() -> list:
        """Get list of all available character IDs"""
        return list(CharacterFactory.CHARACTER_REGISTRY.keys())
    
    @staticmethod
    def get_character_info(character_id: str) -> Dict:
        """
        Get display information for a character
        
        Returns dict with: display_name, tagline, description, theme
        """
        if character_id not in CHARACTER_CONFIGS:
            return {
                "display_name": "Unknown",
                "tagline": "",
                "description": "",
                "theme": {}
            }
        
        config = CHARACTER_CONFIGS[character_id]
        return {
            "display_name": config.get("display_name", ""),
            "tagline": config.get("tagline", ""),
            "description": config.get("description", ""),
            "theme": config.get("theme", {}),
            "quick_topics": config.get("quick_topics", [])
        }


# Convenience function for backward compatibility
def create_character(character_id: str, user_preset: str = "casual_learner") -> BaseEnhancedChatbot:
    """Create a character chatbot - convenience wrapper"""
    return CharacterFactory.create_character(character_id, user_preset)

"""
Domain Character System

This module implements the multi-character coordinator architecture where:
- Multiple domain characters monitor conversations
- Characters respond based on threshold triggers or user requests
- A Coordinator character synthesizes insights across domains
- All characters share full context visibility

Character Types:
1. Philosophy Characters (existing): Different approaches to guidance
2. Domain Characters (new): Specialists in specific life areas
3. Coordinator: Synthesizes multi-domain insights
"""

from .base import BaseCharacter, DomainCharacter, CoordinatorCharacter, CharacterResponse
from .manager import CharacterManager
from .configs import DOMAIN_CHARACTER_CONFIGS, PHILOSOPHY_CHARACTER_CONFIGS
from .ai_integration import DomainCharacterAI, create_ai_integration

__all__ = [
    'BaseCharacter',
    'DomainCharacter', 
    'CoordinatorCharacter',
    'CharacterResponse',
    'CharacterManager',
    'DomainCharacterAI',
    'create_ai_integration',
    'DOMAIN_CHARACTER_CONFIGS',
    'PHILOSOPHY_CHARACTER_CONFIGS'
]

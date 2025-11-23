"""
Smart Response System - Implicit Learning for Cost-Efficient AI Interactions
"""

from .detector import SmallTalkDetector
from .learner import UserStyleLearner
from .character_replies import CharacterQuickReplies
from .context_analyzer import ConversationContextAnalyzer

__all__ = [
    'SmallTalkDetector',
    'UserStyleLearner', 
    'CharacterQuickReplies',
    'ConversationContextAnalyzer'
]

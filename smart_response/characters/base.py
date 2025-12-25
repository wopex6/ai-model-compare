"""
Base Character Classes

Defines the foundation for all character types:
- BaseCharacter: Abstract base for all characters
- DomainCharacter: Characters specialized in life domains
- CoordinatorCharacter: Special coordinator with synthesis privileges
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import sqlite3


@dataclass
class CharacterResponse:
    """Response from a character"""
    character_id: str
    display_name: str
    content: str
    concern_level: float  # 0.0 to 1.0
    interpretation: Dict[str, Any] = field(default_factory=dict)
    should_display: bool = True  # Based on threshold
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'character_id': self.character_id,
            'display_name': self.display_name,
            'content': self.content,
            'concern_level': self.concern_level,
            'interpretation': self.interpretation,
            'should_display': self.should_display,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ThresholdConfig:
    """Configuration for character activation thresholds"""
    base_threshold: float = 0.7
    domain_keywords: List[str] = field(default_factory=list)
    emotional_triggers: List[str] = field(default_factory=list)
    urgency_multiplier: float = 1.0
    user_preference_weight: float = 0.2
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ThresholdConfig':
        """Create from dictionary"""
        return cls(
            base_threshold=data.get('base_threshold', 0.7),
            domain_keywords=data.get('domain_keywords', []),
            emotional_triggers=data.get('emotional_triggers', []),
            urgency_multiplier=data.get('urgency_multiplier', 1.0),
            user_preference_weight=data.get('user_preference_weight', 0.2)
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'base_threshold': self.base_threshold,
            'domain_keywords': self.domain_keywords,
            'emotional_triggers': self.emotional_triggers,
            'urgency_multiplier': self.urgency_multiplier,
            'user_preference_weight': self.user_preference_weight
        }


@dataclass
class StyleConfig:
    """Configuration for character communication style"""
    tone: str = "supportive"  # supportive, direct, gentle, energetic, etc.
    formality: str = "casual"  # formal, casual, professional
    emoji_usage: str = "moderate"  # none, minimal, moderate, frequent
    response_length: str = "medium"  # short, medium, long
    perspective: str = "second_person"  # first_person, second_person, third_person
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StyleConfig':
        """Create from dictionary"""
        return cls(
            tone=data.get('tone', 'supportive'),
            formality=data.get('formality', 'casual'),
            emoji_usage=data.get('emoji_usage', 'moderate'),
            response_length=data.get('response_length', 'medium'),
            perspective=data.get('perspective', 'second_person')
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'tone': self.tone,
            'formality': self.formality,
            'emoji_usage': self.emoji_usage,
            'response_length': self.response_length,
            'perspective': self.perspective
        }


class BaseCharacter(ABC):
    """
    Abstract base class for all characters
    
    All characters must implement:
    - analyze_context(): Calculate concern level for a message
    - generate_response(): Generate a response to the message
    - interpret_context(): Generate character-specific interpretation
    """
    
    def __init__(self, character_id: str, config: Dict, db_connection: sqlite3.Connection = None):
        self.character_id = character_id
        self.config = config
        self.db = db_connection
        
        # Core properties
        self.display_name = config.get('display_name', character_id)
        self.description = config.get('description', '')
        self.system_prompt = config.get('system_prompt', '')
        
        # Configuration objects
        threshold_data = config.get('threshold_config', {})
        self.threshold_config = ThresholdConfig.from_dict(threshold_data) if isinstance(threshold_data, dict) else threshold_data
        
        style_data = config.get('style_config', {})
        self.style_config = StyleConfig.from_dict(style_data) if isinstance(style_data, dict) else style_data
    
    @abstractmethod
    def analyze_context(self, message: str, context: Dict) -> float:
        """
        Analyze message and return concern level (0.0 to 1.0)
        
        Args:
            message: User's message
            context: Full conversation context
            
        Returns:
            Concern level from 0.0 (not my domain) to 1.0 (critical)
        """
        pass
    
    @abstractmethod
    def generate_response(self, message: str, context: Dict) -> CharacterResponse:
        """
        Generate a response to the message
        
        Args:
            message: User's message
            context: Full conversation context
            
        Returns:
            CharacterResponse with content and metadata
        """
        pass
    
    @abstractmethod
    def interpret_context(self, message: str, context: Dict) -> Dict:
        """
        Generate this character's interpretation of the context
        
        This is stored even when character doesn't respond,
        allowing future analysis from this character's perspective.
        
        Args:
            message: User's message
            context: Full conversation context
            
        Returns:
            Dictionary with interpretation details
        """
        pass
    
    def should_respond(self, concern_level: float, user_id: int = None) -> bool:
        """
        Determine if character should respond based on threshold.
        Uses personalized threshold if available, otherwise falls back to default.
        """
        threshold = self.get_threshold_for_user(user_id)
        return concern_level >= threshold
    
    def get_threshold_for_user(self, user_id: int = None) -> float:
        """Get the threshold for this character, personalized if user_id provided"""
        if not user_id or not self.db:
            return self.threshold_config.base_threshold
        
        try:
            cursor = self.db.cursor()
            cursor.execute('''
                SELECT parameters FROM user_personalization WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            
            if row:
                import json
                params = json.loads(row[0])
                routing = params.get('routing', {})
                threshold_key = f'{self.character_id}_threshold'
                if threshold_key in routing:
                    return routing[threshold_key]
        except Exception:
            pass
        
        return self.threshold_config.base_threshold
    
    def calculate_concern_level(self, message: str, context: Dict) -> float:
        """
        Calculate concern level using threshold configuration
        
        This is the default implementation that can be overridden.
        """
        concern = 0.0
        message_lower = message.lower()
        
        # Check domain keywords
        keyword_matches = sum(1 for kw in self.threshold_config.domain_keywords 
                             if kw.lower() in message_lower)
        if keyword_matches > 0:
            concern += min(keyword_matches * 0.15, 0.5)
        
        # Check emotional triggers (high priority)
        trigger_matches = sum(1 for trigger in self.threshold_config.emotional_triggers
                             if trigger.lower() in message_lower)
        if trigger_matches > 0:
            concern += min(trigger_matches * 0.3, 0.6)
        
        # Apply urgency multiplier
        concern *= self.threshold_config.urgency_multiplier
        
        # Factor in user preferences (if database available)
        if self.db and context.get('user_id'):
            user_preference = self._get_user_preference(context['user_id'])
            concern += user_preference * self.threshold_config.user_preference_weight
        
        return min(concern, 1.0)
    
    def _get_user_preference(self, user_id: int) -> float:
        """Get user's preference weight for this character"""
        if not self.db:
            return 0.0
        
        try:
            cursor = self.db.cursor()
            cursor.execute('''
                SELECT preference_score FROM user_character_preferences
                WHERE user_id = ? AND character_id = ?
            ''', (user_id, self.character_id))
            
            result = cursor.fetchone()
            return result[0] if result else 0.0
        except Exception:
            return 0.0
    
    def store_interpretation(self, history_id: int, interpretation: Dict, 
                           concern_level: float, responded: bool = False):
        """Store character's interpretation in database"""
        if not self.db:
            return
        
        try:
            cursor = self.db.cursor()
            cursor.execute('''
                INSERT INTO character_interpretations 
                (primary_history_id, character_id, interpretation, concern_level, responded)
                VALUES (?, ?, ?, ?, ?)
            ''', (history_id, self.character_id, json.dumps(interpretation), 
                  concern_level, 1 if responded else 0))
            self.db.commit()
        except Exception as e:
            print(f"Error storing interpretation: {e}")
    
    def get_style_instructions(self) -> str:
        """Generate style instructions for AI prompt"""
        style = self.style_config
        instructions = []
        
        if style.tone:
            instructions.append(f"Use a {style.tone} tone")
        if style.formality:
            instructions.append(f"Be {style.formality}")
        if style.emoji_usage == 'none':
            instructions.append("Do not use emojis")
        elif style.emoji_usage == 'frequent':
            instructions.append("Use emojis liberally to express emotion")
        if style.response_length == 'short':
            instructions.append("Keep responses brief and focused")
        elif style.response_length == 'long':
            instructions.append("Provide detailed, comprehensive responses")
        
        return ". ".join(instructions) + "." if instructions else ""


class DomainCharacter(BaseCharacter):
    """
    Character specialized in a specific life domain
    
    Domains: work, relationships, mental_health, physical_health, 
             finance, learning, creativity
    """
    
    def __init__(self, character_id: str, config: Dict, db_connection: sqlite3.Connection = None):
        super().__init__(character_id, config, db_connection)
        
        self.domain = config.get('domain', 'general')
        self.focus_areas = config.get('focus_areas', [])
        self.expertise = config.get('expertise', [])
    
    def is_domain_relevant(self, message: str, context: Dict) -> bool:
        """Check if message is relevant to this domain"""
        message_lower = message.lower()
        
        # Check focus areas
        for area in self.focus_areas:
            if area.lower() in message_lower:
                return True
        
        # Check domain keywords
        for keyword in self.threshold_config.domain_keywords:
            if keyword.lower() in message_lower:
                return True
        
        return False
    
    def analyze_context(self, message: str, context: Dict) -> float:
        """Calculate concern level based on domain relevance"""
        return self.calculate_concern_level(message, context)
    
    def generate_response(self, message: str, context: Dict) -> CharacterResponse:
        """
        Generate domain-specific response
        
        This method should be overridden by specific domain implementations
        or use AI to generate responses.
        """
        # Default implementation - will be enhanced with AI
        interpretation = self.interpret_context(message, context)
        concern_level = self.analyze_context(message, context)
        
        return CharacterResponse(
            character_id=self.character_id,
            display_name=self.display_name,
            content=f"[{self.display_name}] I notice this relates to {self.domain}.",
            concern_level=concern_level,
            interpretation=interpretation,
            should_display=self.should_respond(concern_level),
            metadata={
                'domain': self.domain,
                'focus_areas_matched': [a for a in self.focus_areas 
                                       if a.lower() in message.lower()]
            }
        )
    
    def interpret_context(self, message: str, context: Dict) -> Dict:
        """Generate domain-specific interpretation"""
        return {
            'domain': self.domain,
            'relevance': self.is_domain_relevant(message, context),
            'focus_areas_detected': [a for a in self.focus_areas 
                                    if a.lower() in message.lower()],
            'sentiment': 'neutral',  # To be enhanced with AI
            'key_themes': [],  # To be enhanced with AI
            'timestamp': datetime.now().isoformat()
        }


class CoordinatorCharacter(BaseCharacter):
    """
    Special coordinator character with synthesis privileges
    
    The Coordinator:
    - Can see all conversations across domains
    - Can request input from domain characters
    - Synthesizes multi-domain insights
    - Responds when no domain character has critical concern
    """
    
    def __init__(self, character_id: str, config: Dict, db_connection: sqlite3.Connection = None,
                 character_manager = None):
        super().__init__(character_id, config, db_connection)
        
        self.character_manager = character_manager
        self.special_privileges = config.get('special_privileges', [
            'can_see_all_conversations',
            'can_request_domain_input',
            'can_synthesize_multi_domain'
        ])
        
        # Lower threshold - coordinator is more responsive
        self.threshold_config.base_threshold = config.get('threshold_config', {}).get('base_threshold', 0.5)
    
    def set_character_manager(self, manager):
        """Set the character manager reference (for late binding)"""
        self.character_manager = manager
    
    def analyze_context(self, message: str, context: Dict) -> float:
        """
        Coordinator has lower threshold and broader concern
        """
        # Coordinator always has some level of concern
        base_concern = 0.3
        
        # Add concern based on message complexity or importance
        message_length = len(message.split())
        if message_length > 50:
            base_concern += 0.1
        
        # Check for multi-domain indicators
        multi_domain_keywords = ['life', 'everything', 'overwhelmed', 'balance', 
                                 'overall', 'general', 'help me']
        for keyword in multi_domain_keywords:
            if keyword in message.lower():
                base_concern += 0.15
        
        return min(base_concern, 1.0)
    
    def generate_response(self, message: str, context: Dict) -> CharacterResponse:
        """
        Generate coordinator response, potentially synthesizing domain insights
        """
        interpretation = self.interpret_context(message, context)
        concern_level = self.analyze_context(message, context)
        
        # Get domain insights if available
        domain_insights = self._get_domain_insights(context)
        
        return CharacterResponse(
            character_id=self.character_id,
            display_name=self.display_name,
            content=f"[{self.display_name}] I'm here to help you see the bigger picture.",
            concern_level=concern_level,
            interpretation=interpretation,
            should_display=True,  # Coordinator usually displays
            metadata={
                'is_coordinator': True,
                'domain_insights_count': len(domain_insights),
                'synthesized': len(domain_insights) > 1
            }
        )
    
    def interpret_context(self, message: str, context: Dict) -> Dict:
        """Generate holistic interpretation across domains"""
        return {
            'role': 'coordinator',
            'multi_domain_analysis': True,
            'domains_detected': self._detect_domains(message),
            'overall_sentiment': 'neutral',  # To be enhanced
            'priority_assessment': 'normal',  # To be enhanced
            'timestamp': datetime.now().isoformat()
        }
    
    def _detect_domains(self, message: str) -> List[str]:
        """Detect which domains are relevant to the message"""
        domains_detected = []
        message_lower = message.lower()
        
        domain_indicators = {
            'work': ['job', 'career', 'boss', 'work', 'office', 'project', 'deadline'],
            'relationships': ['relationship', 'partner', 'family', 'friend', 'marriage'],
            'mental_health': ['anxious', 'stressed', 'depressed', 'overwhelmed', 'worry'],
            'physical_health': ['health', 'tired', 'sleep', 'exercise', 'sick', 'pain'],
            'finance': ['money', 'budget', 'debt', 'savings', 'financial'],
            'learning': ['learn', 'study', 'course', 'skill', 'education'],
            'creativity': ['creative', 'art', 'hobby', 'music', 'writing']
        }
        
        for domain, keywords in domain_indicators.items():
            if any(kw in message_lower for kw in keywords):
                domains_detected.append(domain)
        
        return domains_detected
    
    def _get_domain_insights(self, context: Dict) -> List[Dict]:
        """Get insights from domain characters"""
        if not self.character_manager:
            return []
        
        # This will be implemented when CharacterManager is complete
        return []
    
    def synthesize_perspectives(self, responses: List[CharacterResponse]) -> str:
        """
        Synthesize multiple character perspectives into unified view
        
        Args:
            responses: List of responses from domain characters
            
        Returns:
            Synthesized insight string
        """
        if not responses:
            return "No domain-specific insights available."
        
        # Group by concern level
        critical = [r for r in responses if r.concern_level >= 0.8]
        notable = [r for r in responses if 0.5 <= r.concern_level < 0.8]
        
        synthesis_parts = []
        
        if critical:
            synthesis_parts.append(f"Critical areas: {', '.join(r.display_name for r in critical)}")
        
        if notable:
            synthesis_parts.append(f"Also relevant: {', '.join(r.display_name for r in notable)}")
        
        return " | ".join(synthesis_parts) if synthesis_parts else "Multiple perspectives available."
    
    def request_domain_input(self, domain: str, message: str, context: Dict) -> Optional[CharacterResponse]:
        """
        Request input from a specific domain character
        
        Args:
            domain: Domain to request from (e.g., 'work', 'relationships')
            message: User's message
            context: Conversation context
            
        Returns:
            Response from the domain character, or None
        """
        if not self.character_manager:
            return None
        
        # This will be implemented when CharacterManager is complete
        return None

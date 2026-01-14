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

# Import admin settings for configurable parameters
try:
    from smart_response.admin_settings import get_setting
except ImportError:
    def get_setting(key, default=None):
        return default


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
        Uses gradual scaling to allow for "noticed but didn't respond" scenarios.
        Settings are configurable via admin UI.
        """
        concern = 0.0
        message_lower = message.lower()
        
        # Get configurable concern per keyword (default 0.08)
        concern_per_keyword = get_setting('concern_per_keyword', 0.08)
        
        # Check domain keywords - gradual scaling
        # 1 match = 8%, 2 matches = 16%, allows for partial detection
        keyword_matches = sum(1 for kw in self.threshold_config.domain_keywords 
                             if kw.lower() in message_lower)
        if keyword_matches > 0:
            concern += min(keyword_matches * concern_per_keyword, 0.4)
        
        # Check emotional triggers (high priority - 0.2 per match)
        trigger_matches = sum(1 for trigger in self.threshold_config.emotional_triggers
                             if trigger.lower() in message_lower)
        if trigger_matches > 0:
            concern += min(trigger_matches * 0.2, 0.5)
        
        # Apply urgency multiplier
        concern *= self.threshold_config.urgency_multiplier
        
        # Factor in user preferences (if database available)
        if self.db and context.get('user_id'):
            user_preference = self._get_user_preference(context['user_id'])
            concern += user_preference * self.threshold_config.user_preference_weight
        
        return min(concern, 1.0)
    
    def update_threshold_from_feedback(self, user_id: int, was_helpful: bool, 
                                        concern_level: float) -> None:
        """
        Adaptively adjust threshold based on user feedback
        
        If user found response helpful when concern was low → lower threshold
        If user found response unhelpful when concern was high → raise threshold
        """
        if not self.db or not user_id:
            return
        
        try:
            cursor = self.db.cursor()
            
            # Calculate adjustment
            adjustment = 0.0
            if was_helpful and concern_level < self.threshold_config.base_threshold:
                # Response was helpful even though concern was below threshold
                # → lower threshold to respond more often
                adjustment = -0.05
            elif not was_helpful and concern_level >= self.threshold_config.base_threshold:
                # Response was not helpful even though concern was above threshold
                # → raise threshold to respond less often
                adjustment = 0.05
            
            if adjustment == 0.0:
                return
            
            # Get current personalized threshold
            cursor.execute('''
                SELECT parameters FROM user_personalization WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            
            if row:
                params = json.loads(row[0])
            else:
                params = {'routing': {}}
            
            if 'routing' not in params:
                params['routing'] = {}
            
            threshold_key = f'{self.character_id}_threshold'
            current_threshold = params['routing'].get(threshold_key, self.threshold_config.base_threshold)
            new_threshold = max(0.3, min(0.95, current_threshold + adjustment))
            params['routing'][threshold_key] = new_threshold
            
            # Save updated threshold
            cursor.execute('''
                INSERT INTO user_personalization (user_id, parameters)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET 
                    parameters = ?,
                    updated_at = CURRENT_TIMESTAMP
            ''', (user_id, json.dumps(params), json.dumps(params)))
            
            self.db.commit()
            print(f"[ADAPTIVE] {self.character_id} threshold for user {user_id}: {current_threshold:.2f} → {new_threshold:.2f}")
            
        except Exception as e:
            print(f"[ADAPTIVE] Error updating threshold: {e}")
    
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
    
    def get_user_history_insights(self, user_id: int, limit: int = 20) -> Dict:
        """
        Retrieve historical insights about a user from past interpretations.
        Returns aggregated patterns, common themes, and emotional trends.
        """
        if not self.db or not user_id:
            return {}
        
        try:
            cursor = self.db.cursor()
            
            # Get recent interpretations for this character and user
            cursor.execute('''
                SELECT ci.interpretation, ci.concern_level, ci.responded, ci.created_at
                FROM character_interpretations ci
                JOIN history_primary hp ON ci.primary_history_id = hp.id
                WHERE ci.character_id = ? AND hp.user_id = ?
                ORDER BY ci.created_at DESC
                LIMIT ?
            ''', (self.character_id, user_id, limit))
            
            rows = cursor.fetchall()
            
            if not rows:
                return {}
            
            # Aggregate insights
            all_emotions = []
            all_themes = []
            all_tags = []
            concern_levels = []
            responded_count = 0
            
            for row in rows:
                interp_json, concern, responded, created_at = row
                try:
                    interp = json.loads(interp_json) if interp_json else {}
                except:
                    interp = {}
                
                concern_levels.append(concern)
                if responded:
                    responded_count += 1
                
                # Collect emotions
                emotions = interp.get('detected_emotions', [])
                all_emotions.extend(emotions)
                
                # Collect themes
                themes = interp.get('key_themes', [])
                all_themes.extend(themes)
                
                # Collect continuity tags
                tags = interp.get('continuity_tags', [])
                all_tags.extend(tags)
            
            # Count frequencies
            from collections import Counter
            emotion_counts = Counter(all_emotions)
            theme_counts = Counter(all_themes)
            tag_counts = Counter(all_tags)
            
            return {
                'total_interactions': len(rows),
                'responded_count': responded_count,
                'avg_concern': sum(concern_levels) / len(concern_levels) if concern_levels else 0,
                'common_emotions': emotion_counts.most_common(5),
                'common_themes': theme_counts.most_common(5),
                'common_tags': tag_counts.most_common(10),
                'engagement_rate': responded_count / len(rows) if rows else 0
            }
        except Exception as e:
            print(f"Error getting user history insights: {e}")
            return {}
    
    def get_personalization_context(self, user_id: int) -> str:
        """
        Generate a personalization context string for AI prompts based on user history.
        """
        insights = self.get_user_history_insights(user_id)
        
        if not insights or insights.get('total_interactions', 0) < 2:
            return ""
        
        context_parts = []
        
        # Add emotional patterns
        if insights.get('common_emotions'):
            emotions = [e[0] for e in insights['common_emotions'][:3]]
            if emotions:
                context_parts.append(f"This user often expresses: {', '.join(emotions)}")
        
        # Add common themes
        if insights.get('common_themes'):
            themes = [t[0] for t in insights['common_themes'][:3]]
            if themes:
                context_parts.append(f"Recurring topics: {', '.join(themes)}")
        
        # Add engagement level
        engagement = insights.get('engagement_rate', 0)
        if engagement > 0.5:
            context_parts.append(f"User frequently engages with {self.domain} topics")
        elif engagement > 0.2:
            context_parts.append(f"User occasionally discusses {self.domain} matters")
        
        if context_parts:
            return "USER CONTEXT (from past conversations): " + ". ".join(context_parts) + "."
        
        return ""
    
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
        """Generate domain-specific interpretation with rich context for future reference"""
        message_lower = message.lower()
        
        # Get emotion detection method from settings (keyword, ai, or hybrid)
        detection_method = get_setting('emotion_detection_method', 'hybrid')
        
        # Build emotional indicators from configurable keywords
        stress_keywords = get_setting('emotion_keywords_stress', 'stress,overwhelm,pressure,anxious,worried').split(',')
        positive_keywords = get_setting('emotion_keywords_positive', 'happy,excited,grateful,hopeful,confident').split(',')
        negative_keywords = get_setting('emotion_keywords_negative', 'sad,angry,frustrated,disappointed,lonely').split(',')
        
        emotional_indicators = {
            'stressed': [kw.strip() for kw in stress_keywords],
            'frustrated': ['frustrat', 'annoy', 'angry', 'upset', 'irritat'],
            'hopeful': [kw.strip() for kw in positive_keywords[:5]],
            'sad': ['sad', 'down', 'depress', 'lonely', 'miss'],
            'confused': ['confus', 'unsure', 'don\'t know', 'uncertain', 'lost']
        }
        
        detected_emotions = []
        if detection_method in ('keyword', 'hybrid'):
            detected_emotions = [emotion for emotion, keywords in emotional_indicators.items()
                                if any(kw in message_lower for kw in keywords)]
        
        # Detect focus areas
        focus_areas_detected = [a for a in self.focus_areas if a.lower() in message_lower]
        
        # Generate character's unique perspective based on domain
        perspective = self._generate_perspective(message, focus_areas_detected, detected_emotions)
        
        # Generate potential advice (what character would suggest)
        potential_advice = self._generate_potential_advice(message, focus_areas_detected)
        
        return {
            'domain': self.domain,
            'relevance': self.is_domain_relevant(message, context),
            'focus_areas_detected': focus_areas_detected,
            'detected_emotions': detected_emotions,
            'user_emotional_state': detected_emotions[0] if detected_emotions else 'neutral',
            'character_perspective': perspective,
            'potential_advice': potential_advice,
            'key_themes': focus_areas_detected[:3],  # Top 3 themes
            'continuity_tags': self._get_continuity_tags(message, context),
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_perspective(self, message: str, focus_areas: List[str], emotions: List[str]) -> str:
        """Generate character's unique viewpoint on the situation"""
        if not focus_areas:
            return f"From a {self.domain} perspective, this seems tangentially related."
        
        emotion_context = f" The user seems {emotions[0]}." if emotions else ""
        return f"From a {self.domain} perspective, this relates to {', '.join(focus_areas)}.{emotion_context}"
    
    def _generate_potential_advice(self, message: str, focus_areas: List[str]) -> str:
        """Generate what this character would advise (even if not responding)"""
        if not focus_areas:
            return ""
        
        advice_templates = {
            'work': "Consider setting boundaries and prioritizing tasks.",
            'relationships': "Open communication might help address this.",
            'mental_health': "Taking time for self-care could be beneficial.",
            'finance': "Creating a budget or financial plan might help.",
            'learning': "Breaking this into smaller learning goals could help.",
            'creativity': "Exploring creative outlets might provide relief."
        }
        return advice_templates.get(self.domain, "Reflecting on this area might be helpful.")
    
    def _get_continuity_tags(self, message: str, context: Dict) -> List[str]:
        """Generate tags for tracking conversation themes over time"""
        tags = []
        message_lower = message.lower()
        
        # Add domain tag
        tags.append(f"domain:{self.domain}")
        
        # Add topic tags based on common themes
        topic_keywords = {
            'career': ['job', 'career', 'work', 'boss', 'colleague'],
            'health': ['health', 'exercise', 'sleep', 'tired', 'energy'],
            'relationships': ['partner', 'friend', 'family', 'relationship'],
            'goals': ['goal', 'plan', 'future', 'want to', 'trying to'],
            'challenges': ['problem', 'issue', 'struggle', 'difficult', 'hard']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in message_lower for kw in keywords):
                tags.append(f"topic:{topic}")
        
        return tags


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
        """
        Get insights from domain characters based on recent interpretations
        
        Returns list of domain insights with concern levels and key themes
        """
        if not self.character_manager:
            return []
        
        insights = []
        message = context.get('message', '')
        
        # Get analysis from each domain character
        for char_id, character in self.character_manager.domain_characters.items():
            try:
                concern_level = character.analyze_context(message, context)
                interpretation = character.interpret_context(message, context)
                
                insights.append({
                    'character_id': char_id,
                    'display_name': character.display_name,
                    'domain': getattr(character, 'domain', 'general'),
                    'concern_level': concern_level,
                    'interpretation': interpretation,
                    'is_relevant': concern_level >= 0.1  # Lower threshold to show more perspectives
                })
            except Exception as e:
                print(f"[COORDINATOR] Error getting insight from {char_id}: {e}")
        
        # Sort by concern level (highest first)
        insights.sort(key=lambda x: x['concern_level'], reverse=True)
        return insights
    
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
        
        # Find character by domain
        target_char_id = f"domain_{domain}"
        character = self.character_manager.domain_characters.get(target_char_id)
        
        if not character:
            # Try to find by matching domain attribute
            for char_id, char in self.character_manager.domain_characters.items():
                if getattr(char, 'domain', '').lower() == domain.lower():
                    character = char
                    break
        
        if not character:
            print(f"[COORDINATOR] No domain character found for domain: {domain}")
            return None
        
        try:
            # Generate response from the domain character
            response = character.generate_response(message, context)
            print(f"[COORDINATOR] Got input from {character.display_name} for domain {domain}")
            return response
        except Exception as e:
            print(f"[COORDINATOR] Error requesting input from {domain}: {e}")
            return None
    
    def get_cross_domain_insights(self, message: str, context: Dict) -> Dict:
        """
        Detect cross-domain patterns and correlations
        
        Returns insights about how different life domains are interconnected
        """
        insights = self._get_domain_insights({**context, 'message': message})
        relevant = [i for i in insights if i['is_relevant']]
        
        cross_domain_patterns = {
            'domains_affected': [i['domain'] for i in relevant],
            'primary_domain': relevant[0]['domain'] if relevant else None,
            'secondary_domains': [i['domain'] for i in relevant[1:3]] if len(relevant) > 1 else [],
            'total_concern': sum(i['concern_level'] for i in relevant),
            'is_multi_domain': len(relevant) >= 2,
            'correlations': []
        }
        
        # Detect common cross-domain correlations
        domains_set = set(cross_domain_patterns['domains_affected'])
        
        if {'work', 'mental_health'}.issubset(domains_set):
            cross_domain_patterns['correlations'].append({
                'type': 'work_stress',
                'description': 'Work-related stress affecting mental health',
                'domains': ['work', 'mental_health']
            })
        
        if {'relationships', 'mental_health'}.issubset(domains_set):
            cross_domain_patterns['correlations'].append({
                'type': 'relationship_wellbeing',
                'description': 'Relationship dynamics affecting emotional state',
                'domains': ['relationships', 'mental_health']
            })
        
        if {'finance', 'mental_health'}.issubset(domains_set):
            cross_domain_patterns['correlations'].append({
                'type': 'financial_stress',
                'description': 'Financial concerns affecting mental wellbeing',
                'domains': ['finance', 'mental_health']
            })
        
        if {'work', 'relationships'}.issubset(domains_set):
            cross_domain_patterns['correlations'].append({
                'type': 'work_life_balance',
                'description': 'Work demands affecting personal relationships',
                'domains': ['work', 'relationships']
            })
        
        return cross_domain_patterns

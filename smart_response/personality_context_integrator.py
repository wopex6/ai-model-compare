"""
Personality Context Integrator
==============================
Connects personality assessment data, user profile, and preferences
to the conversation processing system with dynamic adaptive thresholds.

Features:
- Pulls Big 5 traits from assessment_history and inferred_personality
- Integrates user profile preferences and goals
- Dynamic thresholds that adapt based on:
  - Conversation intensity/emotional state
  - Information recency and confidence
  - Personal circumstances changes
- Automatic change detection and context refresh

Usage:
    integrator = PersonalityContextIntegrator(db_connection, integrated_db)
    context = integrator.get_personality_context(user_id, conversation_state)
    prompt_addition = integrator.format_for_prompt(context)
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class AdaptiveThreshold:
    """Dynamic threshold that adapts based on context"""
    base_value: float = 0.5
    current_value: float = 0.5
    min_value: float = 0.1
    max_value: float = 0.9
    
    # Adaptation factors
    emotional_boost: float = 0.0  # Increases when emotional content detected
    recency_factor: float = 1.0   # Decreases as data gets stale
    confidence_factor: float = 1.0  # Based on data source reliability
    
    def compute(self) -> float:
        """Compute current effective threshold"""
        adjusted = self.base_value * self.recency_factor * self.confidence_factor
        adjusted += self.emotional_boost
        return max(self.min_value, min(self.max_value, adjusted))


@dataclass 
class PersonalityContext:
    """Complete personality context for a user"""
    user_id: int
    
    # Big 5 traits (0-1 scale)
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5
    
    # Source and confidence
    trait_source: str = "default"  # assessment, inferred, blended, default
    trait_confidence: float = 0.5
    trait_age_days: float = 0.0
    
    # Profile data
    goals: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    communication_style: str = "balanced"
    emotional_patterns: List[str] = field(default_factory=list)
    
    # Adaptive thresholds
    personality_influence: AdaptiveThreshold = field(default_factory=AdaptiveThreshold)
    goal_emphasis: AdaptiveThreshold = field(default_factory=AdaptiveThreshold)
    emotional_sensitivity: AdaptiveThreshold = field(default_factory=AdaptiveThreshold)
    
    # Change detection
    last_updated: datetime = field(default_factory=datetime.now)
    change_detected: bool = False
    change_summary: str = ""


class PersonalityContextIntegrator:
    """
    Integrates personality data into conversation context with adaptive thresholds.
    """
    
    # Trait interpretation for prompts
    TRAIT_INTERPRETATIONS = {
        'openness': {
            'high': "curious, creative, open to new ideas",
            'medium': "balanced between tradition and novelty",
            'low': "practical, prefers familiar approaches"
        },
        'conscientiousness': {
            'high': "organized, detail-oriented, values structure",
            'medium': "balanced between structure and flexibility",
            'low': "spontaneous, flexible, adaptable"
        },
        'extraversion': {
            'high': "energetic, social, expressive",
            'medium': "balanced social energy",
            'low': "reflective, reserved, prefers depth over breadth"
        },
        'agreeableness': {
            'high': "cooperative, empathetic, harmony-seeking",
            'medium': "balanced between cooperation and assertion",
            'low': "direct, competitive, values honesty over comfort"
        },
        'neuroticism': {
            'high': "emotionally sensitive, may need extra support",
            'medium': "typical emotional range",
            'low': "emotionally stable, resilient"
        }
    }
    
    def __init__(self, smart_response_db: sqlite3.Connection, integrated_db=None):
        """
        Initialize the integrator.
        
        Args:
            smart_response_db: Connection to smart_response.db (has inferred_personality)
            integrated_db: IntegratedDatabase instance (has assessment_history, user_profiles)
        """
        self.sr_db = smart_response_db
        self.integrated_db = integrated_db
        
        # Cache for personality contexts (user_id -> context)
        self._context_cache: Dict[int, PersonalityContext] = {}
        self._cache_ttl_minutes = 5  # Refresh cache every 5 minutes
        
        # Change detection thresholds
        self._significant_change_threshold = 0.15  # 15% change triggers update
        
        print("✓ PersonalityContextIntegrator initialized")
    
    def get_personality_context(self, user_id: int, 
                                conversation_state: Dict = None) -> PersonalityContext:
        """
        Get complete personality context for a user.
        
        Args:
            user_id: User ID
            conversation_state: Current conversation state (optional)
                - emotional_intensity: 0-1 (detected from recent messages)
                - topic_sensitivity: 0-1 (how personal/sensitive the topic)
                - goal_relevance: 0-1 (how goal-related the conversation is)
        
        Returns:
            PersonalityContext with all data and adaptive thresholds
        """
        # Check cache
        cached = self._context_cache.get(user_id)
        if cached and self._is_cache_valid(cached):
            # Update adaptive thresholds based on conversation state
            if conversation_state:
                self._adapt_thresholds(cached, conversation_state)
            return cached
        
        # Build fresh context
        context = self._build_context(user_id)
        
        # Detect changes from previous context
        if cached:
            self._detect_changes(cached, context)
        
        # Update adaptive thresholds
        if conversation_state:
            self._adapt_thresholds(context, conversation_state)
        
        # Cache it
        self._context_cache[user_id] = context
        
        return context
    
    def _build_context(self, user_id: int) -> PersonalityContext:
        """Build complete personality context from all data sources"""
        context = PersonalityContext(user_id=user_id)
        
        # 1. Get Big 5 traits (priority: assessment > inferred > default)
        self._load_traits(context)
        
        # 2. Get profile data (goals, interests, preferences)
        self._load_profile(context)
        
        # 3. Initialize adaptive thresholds based on data quality
        self._initialize_thresholds(context)
        
        context.last_updated = datetime.now()
        return context
    
    def _load_traits(self, context: PersonalityContext):
        """Load Big 5 traits from available sources"""
        
        # Try assessment first (most reliable)
        assessment = self._get_assessment_traits(context.user_id)
        if assessment:
            context.openness = assessment['openness']
            context.conscientiousness = assessment['conscientiousness']
            context.extraversion = assessment['extraversion']
            context.agreeableness = assessment['agreeableness']
            context.neuroticism = assessment['neuroticism']
            context.trait_source = "assessment"
            context.trait_confidence = assessment['confidence']
            context.trait_age_days = assessment['age_days']
            return
        
        # Try inferred traits
        inferred = self._get_inferred_traits(context.user_id)
        if inferred:
            context.openness = inferred['openness']
            context.conscientiousness = inferred['conscientiousness']
            context.extraversion = inferred['extraversion']
            context.agreeableness = inferred['agreeableness']
            context.neuroticism = inferred['neuroticism']
            context.trait_source = "inferred"
            context.trait_confidence = inferred['confidence']
            context.trait_age_days = inferred['age_days']
            return
        
        # Defaults (neutral)
        context.trait_source = "default"
        context.trait_confidence = 0.3
    
    def _get_assessment_traits(self, user_id: int) -> Optional[Dict]:
        """Get traits from formal personality assessment"""
        if not self.integrated_db:
            return None
        
        try:
            conn = self.integrated_db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT openness, conscientiousness, extraversion, 
                       agreeableness, neuroticism, completed_at,
                       julianday('now') - julianday(completed_at) as age_days
                FROM assessment_history
                WHERE user_id = ?
                ORDER BY completed_at DESC
                LIMIT 1
            ''', (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row and row[0] is not None:
                age_days = row[6] or 0
                # Confidence decreases with age (half-life of 90 days)
                age_factor = 0.5 ** (age_days / 90)
                confidence = 0.9 * age_factor  # Max 0.9 for assessment
                
                return {
                    'openness': row[0],
                    'conscientiousness': row[1],
                    'extraversion': row[2],
                    'agreeableness': row[3],
                    'neuroticism': row[4],
                    'confidence': confidence,
                    'age_days': age_days
                }
        except Exception as e:
            print(f"⚠️ Error loading assessment traits: {e}")
        
        return None
    
    def _get_inferred_traits(self, user_id: int) -> Optional[Dict]:
        """Get traits inferred from conversation patterns"""
        try:
            cursor = self.sr_db.cursor()
            
            cursor.execute('''
                SELECT openness, conscientiousness, extraversion,
                       agreeableness, neuroticism, confidence,
                       julianday('now') - julianday(last_updated) as age_days
                FROM inferred_personality
                WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            
            if row and row[0] is not None:
                # Inferred traits have lower base confidence
                base_confidence = row[5] or 0.5
                age_days = row[6] or 0
                age_factor = 0.5 ** (age_days / 30)  # Faster decay for inferred
                confidence = base_confidence * age_factor * 0.7  # Max 0.7 for inferred
                
                return {
                    'openness': row[0],
                    'conscientiousness': row[1],
                    'extraversion': row[2],
                    'agreeableness': row[3],
                    'neuroticism': row[4],
                    'confidence': confidence,
                    'age_days': age_days
                }
        except Exception as e:
            print(f"⚠️ Error loading inferred traits: {e}")
        
        return None
    
    def _load_profile(self, context: PersonalityContext):
        """Load user profile data (goals, interests, preferences)"""
        if not self.integrated_db:
            return
        
        try:
            conn = self.integrated_db.get_connection()
            cursor = conn.cursor()
            
            # Get profile preferences
            cursor.execute('''
                SELECT preferences FROM user_profiles WHERE user_id = ?
            ''', (context.user_id,))
            
            row = cursor.fetchone()
            if row and row[0]:
                prefs = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                
                # Extract goals
                user_prefs = prefs.get('user_preferences', {})
                context.goals = user_prefs.get('goals', [])
                context.interests = user_prefs.get('topics_of_interest', [])
                context.communication_style = user_prefs.get('communication_style', 'balanced')
                
                # Personal info for context
                personal = prefs.get('personal_info', {})
                if personal.get('interests'):
                    context.interests.extend(personal.get('interests', []))
            
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Error loading profile: {e}")
        
        # Also get goals from user_context table
        try:
            cursor = self.sr_db.cursor()
            cursor.execute('''
                SELECT content FROM user_context
                WHERE user_id = ? AND fact_type = 'goal' AND is_active = 1
                ORDER BY priority DESC, updated_at DESC
                LIMIT 5
            ''', (context.user_id,))
            
            for row in cursor.fetchall():
                if row[0] and row[0] not in context.goals:
                    context.goals.append(row[0])
                    
        except Exception as e:
            pass  # user_context table may not exist
    
    def _initialize_thresholds(self, context: PersonalityContext):
        """Initialize adaptive thresholds based on data quality"""
        
        # Personality influence threshold
        context.personality_influence = AdaptiveThreshold(
            base_value=0.6 if context.trait_source == "assessment" else 0.4,
            confidence_factor=context.trait_confidence,
            recency_factor=1.0 - (context.trait_age_days / 180)  # Decay over 6 months
        )
        
        # Goal emphasis threshold
        has_goals = len(context.goals) > 0
        context.goal_emphasis = AdaptiveThreshold(
            base_value=0.7 if has_goals else 0.3,
            confidence_factor=1.0 if has_goals else 0.5
        )
        
        # Emotional sensitivity (based on neuroticism)
        context.emotional_sensitivity = AdaptiveThreshold(
            base_value=0.3 + (context.neuroticism * 0.4),  # Higher for high neuroticism
            confidence_factor=context.trait_confidence
        )
    
    def _adapt_thresholds(self, context: PersonalityContext, 
                          conversation_state: Dict):
        """Dynamically adapt thresholds based on conversation state"""
        
        emotional_intensity = conversation_state.get('emotional_intensity', 0.5)
        topic_sensitivity = conversation_state.get('topic_sensitivity', 0.5)
        goal_relevance = conversation_state.get('goal_relevance', 0.5)
        
        # Boost personality influence for sensitive topics
        context.personality_influence.emotional_boost = topic_sensitivity * 0.2
        
        # Boost goal emphasis when conversation is goal-related
        context.goal_emphasis.emotional_boost = goal_relevance * 0.3
        
        # Boost emotional sensitivity for emotional conversations
        context.emotional_sensitivity.emotional_boost = emotional_intensity * 0.25
    
    def _detect_changes(self, old: PersonalityContext, new: PersonalityContext):
        """Detect significant changes in personality context"""
        changes = []
        
        # Check trait changes
        traits = ['openness', 'conscientiousness', 'extraversion', 
                  'agreeableness', 'neuroticism']
        for trait in traits:
            old_val = getattr(old, trait)
            new_val = getattr(new, trait)
            if abs(new_val - old_val) > self._significant_change_threshold:
                direction = "increased" if new_val > old_val else "decreased"
                changes.append(f"{trait} {direction}")
        
        # Check goal changes
        old_goals = set(old.goals)
        new_goals = set(new.goals)
        if old_goals != new_goals:
            added = new_goals - old_goals
            if added:
                changes.append(f"new goals: {', '.join(list(added)[:2])}")
        
        if changes:
            new.change_detected = True
            new.change_summary = "; ".join(changes)
            print(f"[PERSONALITY] Change detected for user {new.user_id}: {new.change_summary}")
    
    def _is_cache_valid(self, context: PersonalityContext) -> bool:
        """Check if cached context is still valid"""
        age = datetime.now() - context.last_updated
        return age.total_seconds() < (self._cache_ttl_minutes * 60)
    
    def format_for_prompt(self, context: PersonalityContext, 
                          verbosity: str = "normal") -> str:
        """
        Format personality context for AI prompt.
        
        Args:
            context: PersonalityContext object
            verbosity: "minimal", "normal", or "detailed"
            
        Returns:
            Formatted string for system prompt
        """
        if context.trait_source == "default" and not context.goals:
            return ""  # No useful data
        
        parts = []
        
        # Personality influence threshold determines how much to include
        influence = context.personality_influence.compute()
        
        if influence > 0.3:
            # Include personality traits
            trait_desc = self._describe_traits(context)
            if trait_desc:
                parts.append(f"User personality: {trait_desc}")
        
        # Goals (if goal emphasis is high enough)
        if context.goal_emphasis.compute() > 0.4 and context.goals:
            goals_str = ", ".join(context.goals[:3])
            parts.append(f"User goals: {goals_str}")
        
        # Communication style
        if context.communication_style and context.communication_style != "balanced":
            parts.append(f"Preferred style: {context.communication_style}")
        
        # Emotional sensitivity note (for high sensitivity)
        if context.emotional_sensitivity.compute() > 0.6:
            parts.append("Note: User may be emotionally sensitive - respond with extra care")
        
        # Interests (if relevant)
        if context.interests and verbosity in ("normal", "detailed"):
            interests_str = ", ".join(context.interests[:4])
            parts.append(f"Interests: {interests_str}")
        
        # Confidence note (for low confidence)
        if context.trait_confidence < 0.4 and verbosity == "detailed":
            parts.append(f"(Personality data confidence: {context.trait_confidence:.0%})")
        
        if not parts:
            return ""
        
        return "USER CONTEXT:\n" + "\n".join(f"- {p}" for p in parts)
    
    def _describe_traits(self, context: PersonalityContext) -> str:
        """Generate natural language description of traits"""
        descriptions = []
        
        traits = {
            'openness': context.openness,
            'conscientiousness': context.conscientiousness,
            'extraversion': context.extraversion,
            'agreeableness': context.agreeableness,
            'neuroticism': context.neuroticism
        }
        
        # Only describe notable traits (significantly different from neutral)
        for trait, value in traits.items():
            if value > 0.65:
                desc = self.TRAIT_INTERPRETATIONS[trait]['high']
                descriptions.append(desc)
            elif value < 0.35:
                desc = self.TRAIT_INTERPRETATIONS[trait]['low']
                descriptions.append(desc)
        
        if not descriptions:
            return ""
        
        return "; ".join(descriptions[:3])  # Limit to 3 notable traits
    
    def invalidate_cache(self, user_id: int):
        """Invalidate cache for a user (call when profile/assessment changes)"""
        if user_id in self._context_cache:
            del self._context_cache[user_id]
            print(f"[PERSONALITY] Cache invalidated for user {user_id}")
    
    def get_conversation_state_from_message(self, message: str, 
                                            recent_messages: List[str] = None) -> Dict:
        """
        Analyze message to determine conversation state for threshold adaptation.
        
        Args:
            message: Current user message
            recent_messages: Optional list of recent messages for context
            
        Returns:
            Conversation state dict
        """
        message_lower = message.lower()
        
        # Detect emotional intensity
        emotional_words = [
            'stressed', 'anxious', 'worried', 'scared', 'angry', 'frustrated',
            'sad', 'depressed', 'overwhelmed', 'happy', 'excited', 'grateful',
            'love', 'hate', 'fear', 'hope', 'desperate', 'lonely', 'hurt'
        ]
        emotional_count = sum(1 for word in emotional_words if word in message_lower)
        emotional_intensity = min(1.0, emotional_count * 0.25)
        
        # Detect topic sensitivity
        sensitive_patterns = [
            'personal', 'private', 'secret', 'struggle', 'problem', 'issue',
            'relationship', 'family', 'health', 'money', 'career', 'life',
            'feeling', 'emotion', 'mental', 'therapy', 'help me'
        ]
        sensitive_count = sum(1 for pattern in sensitive_patterns if pattern in message_lower)
        topic_sensitivity = min(1.0, sensitive_count * 0.2)
        
        # Detect goal relevance
        goal_patterns = [
            'goal', 'want to', 'trying to', 'working on', 'achieve', 'plan',
            'hope to', 'need to', 'should', 'must', 'will', 'going to',
            'improve', 'change', 'better', 'progress', 'success'
        ]
        goal_count = sum(1 for pattern in goal_patterns if pattern in message_lower)
        goal_relevance = min(1.0, goal_count * 0.15)
        
        return {
            'emotional_intensity': emotional_intensity,
            'topic_sensitivity': topic_sensitivity,
            'goal_relevance': goal_relevance
        }


def create_personality_integrator(smart_response_db: sqlite3.Connection,
                                  integrated_db=None) -> PersonalityContextIntegrator:
    """Factory function to create PersonalityContextIntegrator"""
    return PersonalityContextIntegrator(smart_response_db, integrated_db)

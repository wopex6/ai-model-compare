"""
Personality Resolver - Smart decision logic for real-time personality data usage

This module provides intelligent resolution of personality data from multiple sources
(assessment, inferred, defaults) with confidence scoring and age-based blending.

Usage:
    resolver = PersonalityResolver(integrated_db)
    profile = resolver.get_decision_ready_profile(user_id, context='character_selection')
    
    if profile['confidence'] > 0.7:
        # Use personality data for decisions
        character = select_based_on_traits(profile['traits'])
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class PersonalityResolver:
    """
    Resolves the BEST personality data to use for real-time decisions
    Handles priority, blending, and confidence scoring
    """
    
    # Age thresholds (in days)
    FRESH_THRESHOLD = 90      # < 3 months = fresh
    MODERATE_THRESHOLD = 365  # < 12 months = moderate
    
    # Confidence levels
    CONFIDENCE_FRESH = 0.95
    CONFIDENCE_BLENDED = 0.75
    CONFIDENCE_MODERATE = 0.65
    CONFIDENCE_OLD = 0.50
    CONFIDENCE_DEFAULT = 0.0
    
    # Cache duration (seconds)
    CACHE_DURATION = 300  # 5 minutes
    
    def __init__(self, db):
        """
        Initialize resolver with database connection
        
        Args:
            db: IntegratedDatabase instance
        """
        self.db = db
        self.cache = {}  # Simple in-memory cache
        
    def get_decision_ready_profile(
        self, 
        user_id: int,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get personality profile optimized for making decisions
        
        Args:
            user_id: User ID
            context: Optional context hint ('character_selection', 'response_tone', 'action_plan')
        
        Returns:
            {
                'traits': {
                    'openness': 0.80,
                    'conscientiousness': 0.70,
                    'extraversion': 0.60,
                    'agreeableness': 0.90,
                    'neuroticism': 0.30
                },
                'confidence': 0.85,  # Overall confidence 0-1
                'source': 'assessment',  # or 'inferred', 'blended', 'default'
                'metadata': {
                    'assessment_age_days': 45,
                    'assessment_exists': True,
                    'inferred_exists': True,
                    'inferred_confidence': 0.72,
                    'blend_ratio': None  # or {'assessment': 0.6, 'inferred': 0.4}
                },
                'recommendations': {
                    'reliability': 'high',  # 'high', 'medium', 'low', 'none'
                    'should_reassess': False,
                    'reasoning': 'Recent assessment data available'
                }
            }
        """
        
        # Check cache first
        cache_key = f"{user_id}_{context or 'default'}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['timestamp'] < self.CACHE_DURATION:
                return cached['data']
        
        # Get assessment data
        assessment = self._get_assessment_data(user_id)
        
        # Get inferred data
        inferred = self._get_inferred_data(user_id)
        
        # Apply decision logic
        result = self._resolve_personality(assessment, inferred)
        
        # Cache result
        self.cache[cache_key] = {
            'data': result,
            'timestamp': time.time()
        }
        
        return result
    
    def clear_cache(self, user_id: Optional[int] = None):
        """
        Clear cache for a specific user or all users
        
        Args:
            user_id: Optional user ID. If None, clears all cache.
        """
        if user_id is None:
            self.cache.clear()
        else:
            # Remove all cache entries for this user
            keys_to_remove = [k for k in self.cache.keys() if k.startswith(f"{user_id}_")]
            for key in keys_to_remove:
                del self.cache[key]
    
    def _get_assessment_data(self, user_id: int) -> Optional[Dict]:
        """
        Get latest assessment with age calculation
        
        Returns:
            {
                'traits': {...},
                'completed_at': '2025-09-25T10:30:00',
                'age_days': 45.3
            }
            or None if no assessment exists
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    openness, conscientiousness, extraversion, 
                    agreeableness, neuroticism,
                    completed_at,
                    julianday('now') - julianday(completed_at) as age_days
                FROM assessment_history
                WHERE user_id = ?
                ORDER BY completed_at DESC
                LIMIT 1
            ''', (user_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
                
            return {
                'traits': {
                    'openness': row[0],
                    'conscientiousness': row[1],
                    'extraversion': row[2],
                    'agreeableness': row[3],
                    'neuroticism': row[4]
                },
                'completed_at': row[5],
                'age_days': row[6]
            }
        finally:
            conn.close()
    
    def _get_inferred_data(self, user_id: int) -> Optional[Dict]:
        """
        Get inferred traits with metadata
        
        Returns:
            {
                'traits': {...},
                'confidence': 0.72,
                'message_count': 45,
                'last_updated': '2025-12-04T20:15:00'
            }
            or None if no inferred data exists
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    openness, conscientiousness, extraversion,
                    agreeableness, neuroticism,
                    confidence, message_count, last_updated
                FROM inferred_personality
                WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
                
            return {
                'traits': {
                    'openness': row[0],
                    'conscientiousness': row[1],
                    'extraversion': row[2],
                    'agreeableness': row[3],
                    'neuroticism': row[4]
                },
                'confidence': row[5],
                'message_count': row[6],
                'last_updated': row[7]
            }
        finally:
            conn.close()
    
    def _resolve_personality(
        self, 
        assessment: Optional[Dict], 
        inferred: Optional[Dict]
    ) -> Dict:
        """
        Apply decision logic to choose best personality data
        
        Decision tree:
        1. Fresh assessment (< 3 months) → Use it (0.95 confidence)
        2. Moderate assessment (3-12 months) + inferred → Blend 60/40 (0.75 confidence)
        3. Old assessment (3-12 months), no inferred → Use assessment (0.65 confidence)
        4. Very old assessment (> 12 months) + inferred → Use inferred
        5. Very old assessment, no inferred → Use assessment (0.50 confidence)
        6. No assessment, has inferred → Use inferred
        7. No data → Use defaults (0.0 confidence)
        """
        
        # CASE 1: Fresh assessment (< 3 months)
        if assessment and assessment['age_days'] < self.FRESH_THRESHOLD:
            return self._build_result(
                traits=assessment['traits'],
                confidence=self.CONFIDENCE_FRESH,
                source='assessment',
                assessment=assessment,
                inferred=inferred,
                blend_ratio=None,
                reliability='high',
                should_reassess=False,
                reasoning=f'Recent assessment ({int(assessment["age_days"])} days old)'
            )
        
        # CASE 2: Moderately old assessment (3-12 months) + inferred data
        if (assessment and 
            self.FRESH_THRESHOLD <= assessment['age_days'] < self.MODERATE_THRESHOLD and 
            inferred):
            
            # BLEND: 60% assessment, 40% inferred
            blended_traits = {}
            for trait in ['openness', 'conscientiousness', 'extraversion', 
                         'agreeableness', 'neuroticism']:
                blended_traits[trait] = (
                    0.6 * assessment['traits'][trait] + 
                    0.4 * inferred['traits'][trait]
                )
            
            return self._build_result(
                traits=blended_traits,
                confidence=self.CONFIDENCE_BLENDED,
                source='blended',
                assessment=assessment,
                inferred=inferred,
                blend_ratio={'assessment': 0.6, 'inferred': 0.4},
                reliability='medium',
                should_reassess=True,
                reasoning=f'Assessment is {int(assessment["age_days"])} days old, blended with recent conversation patterns'
            )
        
        # CASE 3: Old assessment (3-12 months) but no inferred data
        if (assessment and 
            self.FRESH_THRESHOLD <= assessment['age_days'] < self.MODERATE_THRESHOLD and 
            not inferred):
            
            return self._build_result(
                traits=assessment['traits'],
                confidence=self.CONFIDENCE_MODERATE,
                source='assessment',
                assessment=assessment,
                inferred=inferred,
                blend_ratio=None,
                reliability='medium',
                should_reassess=True,
                reasoning=f'Assessment is {int(assessment["age_days"])} days old, no recent conversation data'
            )
        
        # CASE 4: Very old assessment (> 12 months) but has inferred
        if assessment and assessment['age_days'] >= self.MODERATE_THRESHOLD and inferred:
            # Inferred data more reliable than 1+ year old assessment
            return self._build_result(
                traits=inferred['traits'],
                confidence=inferred['confidence'],
                source='inferred',
                assessment=assessment,
                inferred=inferred,
                blend_ratio=None,
                reliability='medium' if inferred['confidence'] > 0.6 else 'low',
                should_reassess=True,
                reasoning=f'Assessment is very old ({int(assessment["age_days"])} days), using recent conversation patterns'
            )
        
        # CASE 5: Very old assessment, no inferred
        if assessment and assessment['age_days'] >= self.MODERATE_THRESHOLD and not inferred:
            return self._build_result(
                traits=assessment['traits'],
                confidence=self.CONFIDENCE_OLD,
                source='assessment',
                assessment=assessment,
                inferred=inferred,
                blend_ratio=None,
                reliability='low',
                should_reassess=True,
                reasoning=f'Assessment is very old ({int(assessment["age_days"])} days), urgently needs reassessment'
            )
        
        # CASE 6: No assessment, has inferred
        if not assessment and inferred:
            reliability = 'medium' if inferred['confidence'] > 0.6 else 'low'
            return self._build_result(
                traits=inferred['traits'],
                confidence=inferred['confidence'],
                source='inferred',
                assessment=assessment,
                inferred=inferred,
                blend_ratio=None,
                reliability=reliability,
                should_reassess=True,
                reasoning=f'No formal assessment, using inferred data from {inferred["message_count"]} messages'
            )
        
        # CASE 7: No data at all - defaults
        return self._build_result(
            traits={
                'openness': 0.5,
                'conscientiousness': 0.5,
                'extraversion': 0.5,
                'agreeableness': 0.5,
                'neuroticism': 0.5
            },
            confidence=self.CONFIDENCE_DEFAULT,
            source='default',
            assessment=assessment,
            inferred=inferred,
            blend_ratio=None,
            reliability='none',
            should_reassess=True,
            reasoning='No personality data available, using neutral defaults'
        )
    
    def _build_result(
        self,
        traits: Dict[str, float],
        confidence: float,
        source: str,
        assessment: Optional[Dict],
        inferred: Optional[Dict],
        blend_ratio: Optional[Dict],
        reliability: str,
        should_reassess: bool,
        reasoning: str
    ) -> Dict:
        """Build standardized result dictionary"""
        return {
            'traits': traits,
            'confidence': confidence,
            'source': source,
            'metadata': {
                'assessment_age_days': assessment['age_days'] if assessment else None,
                'assessment_exists': assessment is not None,
                'inferred_exists': inferred is not None,
                'inferred_confidence': inferred['confidence'] if inferred else None,
                'blend_ratio': blend_ratio
            },
            'recommendations': {
                'reliability': reliability,
                'should_reassess': should_reassess,
                'reasoning': reasoning
            }
        }
    
    def get_confidence_for_context(self, profile: Dict, context: str) -> float:
        """
        Get adjusted confidence for specific context
        
        Different decisions need different confidence levels.
        This method can lower confidence if context requires higher certainty.
        
        Args:
            profile: Result from get_decision_ready_profile()
            context: Decision context
        
        Returns:
            Adjusted confidence (0-1)
        """
        base_confidence = profile['confidence']
        
        # Context-specific adjustments
        context_requirements = {
            'character_selection': 0.6,     # Medium confidence OK
            'response_tone': 0.7,            # Higher confidence needed
            'action_plan': 0.8,              # High confidence needed
            'crisis_intervention': 0.9       # Very high confidence needed
        }
        
        required = context_requirements.get(context, 0.5)
        
        # If below required, reduce confidence further
        if base_confidence < required:
            return base_confidence * 0.8  # Penalty for not meeting requirement
        
        return base_confidence

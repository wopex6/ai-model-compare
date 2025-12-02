"""
Personality Trend Analyzer
Infers personality traits from emotional and behavioral patterns over time

PSYCHOLOGICAL FOUNDATIONS:
1. Big Five Personality Traits (OCEAN)
2. Schwartz Theory of Basic Values
3. Approach-Avoidance Motivation
4. Emotional Granularity Theory

This system analyzes longitudinal patterns to infer:
- Personality traits (stable characteristics)
- Core values and motivations
- Behavioral tendencies
- Desire patterns
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter
import sqlite3


class PersonalityTrendAnalyzer:
    """
    Analyzes emotional and behavioral patterns to infer personality traits
    """
    
    # Minimum occurrences to establish pattern
    PATTERN_THRESHOLD = 3
    TIME_WINDOW_DAYS = 14
    
    # Confidence thresholds
    MIN_CONFIDENCE = 0.60  # Minimum to record inference
    HIGH_CONFIDENCE = 0.80  # High confidence threshold
    
    # Big Five Personality Traits (OCEAN Model)
    BIG_FIVE_PATTERNS = {
        # Openness to Experience
        'creative': ['curious', 'creative', 'imaginative', 'artistic', 'inventive'],
        'conventional': ['routine', 'traditional', 'practical', 'structured'],
        
        # Conscientiousness
        'organized': ['organized', 'planned', 'focused', 'disciplined', 'determined'],
        'spontaneous': ['spontaneous', 'flexible', 'adaptable', 'relaxed'],
        
        # Extraversion
        'extraverted': ['excited', 'energetic', 'social', 'outgoing', 'enthusiastic'],
        'introverted': ['quiet', 'reserved', 'solitary', 'reflective', 'calm'],
        
        # Agreeableness
        'cooperative': ['kind', 'caring', 'compassionate', 'helpful', 'generous'],
        'competitive': ['competitive', 'assertive', 'challenging', 'critical'],
        
        # Neuroticism (Emotional Stability)
        'emotionally_stable': ['calm', 'stable', 'confident', 'secure', 'resilient'],
        'neurotic': ['stressed', 'anxious', 'worried', 'nervous', 'tense', 'overwhelmed'],
    }
    
    # Emotional Temperament Patterns
    TEMPERAMENT_PATTERNS = {
        'optimistic': ['excited', 'happy', 'hopeful', 'confident', 'positive', 'grateful'],
        'pessimistic': ['worried', 'anxious', 'doubtful', 'negative', 'hopeless'],
        'emotional': ['sad', 'angry', 'frustrated', 'tearful', 'upset', 'emotional'],
        'rational': ['analytical', 'logical', 'calm', 'rational', 'objective'],
        'empathetic': ['caring', 'compassionate', 'understanding', 'concerned'],
        'detached': ['indifferent', 'detached', 'cold', 'distant', 'aloof'],
    }
    
    # Schwartz Theory of Basic Values - Core Motivations
    VALUE_PATTERNS = {
        # Power & Achievement
        'power_seeking': {
            'emotions': ['ambitious', 'competitive', 'determined', 'driven'],
            'goals': ['leadership', 'control', 'authority', 'influence', 'status', 'dominance'],
            'preferences': ['leading', 'managing', 'directing', 'commanding']
        },
        'achievement_oriented': {
            'emotions': ['motivated', 'determined', 'focused', 'driven'],
            'goals': ['success', 'excellence', 'accomplishment', 'winning', 'goals', 'achievement'],
            'preferences': ['competing', 'improving', 'advancing', 'excelling']
        },
        
        # Wealth & Security
        'wealth_seeking': {
            'emotions': ['ambitious', 'motivated'],
            'goals': ['money', 'wealth', 'financial', 'rich', 'prosperity', 'income'],
            'preferences': ['earning', 'investing', 'saving', 'acquiring']
        },
        'security_oriented': {
            'emotions': ['safe', 'secure', 'stable', 'protected'],
            'goals': ['security', 'stability', 'safety', 'protection', 'certainty'],
            'preferences': ['planning', 'preparing', 'organizing', 'protecting']
        },
        
        # Honor & Tradition
        'honor_driven': {
            'emotions': ['proud', 'dignified', 'principled', 'righteous'],
            'goals': ['respect', 'honor', 'dignity', 'reputation', 'integrity', 'righteousness'],
            'preferences': ['upholding', 'defending', 'honoring', 'respecting']
        },
        'tradition_oriented': {
            'emotions': ['respectful', 'devoted', 'reverent'],
            'goals': ['tradition', 'heritage', 'legacy', 'customs', 'values'],
            'preferences': ['preserving', 'maintaining', 'honoring', 'following']
        },
        
        # Hedonism & Contentment
        'pleasure_seeking': {
            'emotions': ['excited', 'joyful', 'happy', 'thrilled', 'delighted'],
            'goals': ['fun', 'pleasure', 'enjoyment', 'excitement', 'happiness', 'joy'],
            'preferences': ['enjoying', 'experiencing', 'savoring', 'indulging']
        },
        'contentment_seeking': {
            'emotions': ['peaceful', 'content', 'satisfied', 'fulfilled', 'serene'],
            'goals': ['peace', 'contentment', 'satisfaction', 'tranquility', 'harmony'],
            'preferences': ['accepting', 'appreciating', 'being present', 'relaxing']
        },
        
        # Stimulation & Adventure
        'adventure_seeking': {
            'emotions': ['excited', 'thrilled', 'adventurous', 'daring', 'bold'],
            'goals': ['adventure', 'exploration', 'discovery', 'challenge', 'risk', 'novelty'],
            'preferences': ['exploring', 'trying new', 'risking', 'adventuring', 'discovering']
        },
        'novelty_seeking': {
            'emotions': ['curious', 'interested', 'fascinated', 'intrigued'],
            'goals': ['learning', 'discovery', 'variety', 'change', 'novelty'],
            'preferences': ['learning', 'discovering', 'experimenting', 'varying']
        },
        
        # Self-Direction & Independence
        'independent': {
            'emotions': ['free', 'autonomous', 'self-reliant', 'independent'],
            'goals': ['independence', 'freedom', 'autonomy', 'self-reliance', 'self-direction'],
            'preferences': ['deciding', 'choosing', 'self-managing', 'controlling own']
        },
        'self_directed': {
            'emotions': ['creative', 'innovative', 'original', 'unique'],
            'goals': ['creativity', 'innovation', 'originality', 'self-expression'],
            'preferences': ['creating', 'innovating', 'expressing', 'designing']
        },
        
        # Benevolence & Relationships
        'relationship_oriented': {
            'emotions': ['loving', 'caring', 'connected', 'close', 'intimate'],
            'goals': ['relationships', 'connection', 'belonging', 'intimacy', 'love', 'friendship'],
            'preferences': ['connecting', 'relating', 'bonding', 'sharing', 'communicating']
        },
        'socially_dependent': {
            'emotions': ['lonely', 'needy', 'dependent', 'attached'],
            'goals': ['approval', 'acceptance', 'validation', 'belonging', 'companionship'],
            'preferences': ['pleasing', 'fitting in', 'being liked', 'gaining approval']
        },
        'altruistic': {
            'emotions': ['compassionate', 'caring', 'generous', 'giving'],
            'goals': ['helping', 'caring', 'supporting', 'serving', 'contributing', 'kindness'],
            'preferences': ['helping others', 'giving', 'supporting', 'volunteering']
        },
        
        # Universalism & Nature
        'nature_connected': {
            'emotions': ['peaceful', 'grounded', 'connected', 'natural'],
            'goals': ['nature', 'environment', 'earth', 'natural', 'wilderness', 'outdoors'],
            'preferences': ['nature', 'outdoors', 'natural', 'environmental', 'hiking']
        },
        'intellectually_oriented': {
            'emotions': ['curious', 'analytical', 'thoughtful', 'contemplative'],
            'goals': ['knowledge', 'understanding', 'wisdom', 'learning', 'truth', 'insight'],
            'preferences': ['thinking', 'analyzing', 'studying', 'researching', 'reading']
        },
        
        # Conformity & Behavior Style
        'conformist': {
            'emotions': ['obedient', 'compliant', 'dutiful', 'responsible'],
            'goals': ['rules', 'duty', 'obligation', 'responsibility', 'conformity'],
            'preferences': ['following', 'obeying', 'complying', 'adhering']
        },
        'rebellious': {
            'emotions': ['defiant', 'rebellious', 'resistant', 'independent'],
            'goals': ['freedom', 'rebellion', 'resistance', 'breaking rules', 'defiance'],
            'preferences': ['challenging', 'questioning', 'resisting', 'breaking']
        },
        
        # Depth vs Surface
        'depth_seeking': {
            'emotions': ['thoughtful', 'deep', 'profound', 'meaningful'],
            'goals': ['meaning', 'depth', 'substance', 'significance', 'purpose'],
            'preferences': ['deep conversations', 'meaningful', 'profound', 'substantial']
        },
        'surface_oriented': {
            'emotions': ['casual', 'light', 'easygoing', 'superficial'],
            'goals': ['fun', 'entertainment', 'distraction', 'amusement'],
            'preferences': ['light', 'casual', 'surface', 'simple', 'easy']
        },
        
        # Impulsivity vs Deliberation
        'impulsive': {
            'emotions': ['impulsive', 'spontaneous', 'reckless', 'hasty'],
            'goals': ['immediate', 'now', 'instant', 'quick'],
            'preferences': ['acting quickly', 'spontaneous', 'immediate', 'instant']
        },
        'deliberate': {
            'emotions': ['careful', 'cautious', 'thoughtful', 'measured'],
            'goals': ['planning', 'preparation', 'consideration', 'deliberation'],
            'preferences': ['planning', 'thinking through', 'considering', 'deliberating']
        },
    }
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._init_tables()
    
    def _init_tables(self):
        """Create pattern tracking tables"""
        cursor = self.db.cursor()
        
        # Store inferred traits with evidence
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inferred_traits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                
                trait_category TEXT NOT NULL,
                trait_name TEXT NOT NULL,
                confidence FLOAT NOT NULL,
                
                evidence_count INTEGER NOT NULL,
                evidence_summary TEXT,
                
                first_detected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                active BOOLEAN DEFAULT 1,
                
                UNIQUE(user_id, character, trait_category, trait_name)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_inferred_user_active
            ON inferred_traits(user_id, character, active)
        ''')
        
        self.db.commit()
        print("✓ Personality Trend Analyzer initialized")
    
    def analyze_patterns(self, user_id: int, character: str, days: int = 14) -> List[Dict]:
        """
        Analyze emotional and behavioral patterns to infer personality traits
        
        Returns:
            List of inferred traits with confidence scores
        """
        inferred_traits = []
        
        # Get recent explicit context
        recent_context = self._get_recent_context(user_id, character, days)
        
        # Separate by type
        emotions = [c for c in recent_context if c['type'] == 'emotional_state']
        goals = [c for c in recent_context if c['type'] == 'goal']
        preferences = [c for c in recent_context if c['type'] == 'preference']
        needs = [c for c in recent_context if c['type'] == 'need']
        self_descriptions = [c for c in recent_context if c['type'] == 'self_description']
        
        # Debug: Show what we're analyzing
        print(f"   📋 Context retrieved: {len(emotions)} emotions, {len(goals)} goals, {len(preferences)} preferences", flush=True)
        if emotions:
            print(f"      Emotions: {[e['value'] for e in emotions]}", flush=True)
        if goals:
            print(f"      Goals: {[g['value'] for g in goals]}", flush=True)
        if preferences:
            print(f"      Preferences: {[p['value'] for p in preferences]}", flush=True)
        
        # Note: All goals (including intentions, efforts, etc.) are stored as type='goal'
        # They're differentiated by context_key, but for pattern analysis we treat them all as goals
        
        # 1. Analyze Big Five patterns from emotions
        big_five = self._analyze_big_five(emotions)
        inferred_traits.extend(big_five)
        
        # 2. Analyze temperament patterns
        temperament = self._analyze_temperament(emotions)
        inferred_traits.extend(temperament)
        
        # 3. Analyze value patterns (comprehensive)
        # Pass goals for all goal-related analysis (intentions, efforts, aspirations all included)
        value_traits = self._analyze_values(emotions, goals, preferences, needs, self_descriptions)
        inferred_traits.extend(value_traits)
        
        # Store high-confidence inferences
        for trait in inferred_traits:
            if trait['confidence'] >= self.MIN_CONFIDENCE:
                self._store_inferred_trait(user_id, character, trait)
        
        return inferred_traits
    
    def _get_recent_context(self, user_id: int, character: str, days: int) -> List[Dict]:
        """Get all explicit context from recent time window"""
        cursor = self.db.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT context_type, context_key, context_value, timestamp, confidence
            FROM explicit_context
            WHERE user_id = ? AND character = ? 
            AND timestamp >= ?
            AND active = 1
            ORDER BY timestamp DESC
        ''', (user_id, character, cutoff_date))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'type': row[0],
                'key': row[1],
                'value': row[2],
                'timestamp': row[3],
                'confidence': row[4]
            })
        
        return results
    
    def _analyze_big_five(self, emotions: List[Dict]) -> List[Dict]:
        """Analyze Big Five personality traits from emotional patterns"""
        traits = []
        
        # Extract emotion values
        emotion_values = [e['value'].lower() for e in emotions]
        
        for trait_name, keywords in self.BIG_FIVE_PATTERNS.items():
            matches = [e for e in emotion_values if any(k in e for k in keywords)]
            
            if len(matches) >= self.PATTERN_THRESHOLD:
                confidence = self._calculate_confidence(
                    len(matches), 
                    len(emotions),
                    self.PATTERN_THRESHOLD
                )
                
                traits.append({
                    'category': 'big_five',
                    'trait': trait_name,
                    'confidence': confidence,
                    'evidence': matches,
                    'evidence_count': len(matches)
                })
        
        return traits
    
    def _analyze_temperament(self, emotions: List[Dict]) -> List[Dict]:
        """Analyze emotional temperament patterns"""
        traits = []
        
        emotion_values = [e['value'].lower() for e in emotions]
        
        for trait_name, keywords in self.TEMPERAMENT_PATTERNS.items():
            matches = [e for e in emotion_values if any(k in e for k in keywords)]
            
            if len(matches) >= self.PATTERN_THRESHOLD:
                confidence = self._calculate_confidence(
                    len(matches),
                    len(emotions),
                    self.PATTERN_THRESHOLD
                )
                
                traits.append({
                    'category': 'temperament',
                    'trait': trait_name,
                    'confidence': confidence,
                    'evidence': matches,
                    'evidence_count': len(matches)
                })
        
        return traits
    
    def _analyze_values(self, emotions: List[Dict], goals: List[Dict], 
                       preferences: List[Dict], needs: List[Dict],
                       self_descriptions: List[Dict]) -> List[Dict]:
        """Analyze core values and motivations from multiple signals"""
        traits = []
        
        # Extract text from each type
        emotion_texts = [e['value'].lower() for e in emotions]
        goal_texts = [g['value'].lower() for g in goals]  # Includes all intentions, efforts, etc.
        pref_texts = [p['value'].lower() for p in preferences]
        need_texts = [n['value'].lower() for n in needs]
        desc_texts = [d['value'].lower() for d in self_descriptions]
        
        for trait_name, pattern in self.VALUE_PATTERNS.items():
            # Match across all sources
            matches = {
                'emotions': [],
                'goals': [],
                'preferences': [],
                'needs': [],
                'self_descriptions': []
            }
            
            # Check emotions
            for emotion in emotion_texts:
                if any(k in emotion for k in pattern.get('emotions', [])):
                    matches['emotions'].append(emotion)
            
            # Check goals (includes intentions, efforts, aspirations, etc.)
            for goal in goal_texts:
                if any(k in goal for k in pattern.get('goals', [])):
                    matches['goals'].append(goal)
            
            # Check preferences
            for pref in pref_texts:
                if any(k in pref for k in pattern.get('preferences', [])):
                    matches['preferences'].append(pref)
            
            # Check needs
            for need in need_texts:
                if any(k in need for k in pattern.get('goals', [])):  # Needs often express values/goals
                    matches['needs'].append(need)
            
            # Check self-descriptions (for personality traits matching values)
            for desc in desc_texts:
                if any(k in desc for k in pattern.get('goals', [])):
                    matches['self_descriptions'].append(desc)
            
            # Total evidence count
            total_evidence = sum(len(v) for v in matches.values())
            
            # Need minimum evidence across multiple sources for values
            if total_evidence >= self.PATTERN_THRESHOLD:
                # Higher confidence if multiple signal types
                signal_diversity = sum(1 for v in matches.values() if len(v) > 0)
                
                confidence = self._calculate_value_confidence(
                    total_evidence,
                    signal_diversity
                )
                
                traits.append({
                    'category': 'core_value',
                    'trait': trait_name,
                    'confidence': confidence,
                    'evidence': matches,
                    'evidence_count': total_evidence,
                    'signal_diversity': signal_diversity
                })
        
        return traits
    
    def _calculate_confidence(self, match_count: int, total_count: int, 
                             threshold: int) -> float:
        """
        Calculate confidence score for trait inference
        
        Factors:
        - Frequency: More matches = higher confidence
        - Proportion: Matches / Total
        - Above threshold: Bonus for exceeding minimum
        """
        if total_count == 0:
            return 0.0
        
        # Base confidence from frequency
        frequency_score = min(match_count / 10.0, 0.5)  # Max 0.5 from frequency
        
        # Proportion score
        proportion_score = min((match_count / total_count) * 0.3, 0.3)  # Max 0.3
        
        # Threshold bonus
        above_threshold = max(0, match_count - threshold)
        threshold_bonus = min(above_threshold * 0.05, 0.2)  # Max 0.2
        
        confidence = frequency_score + proportion_score + threshold_bonus
        
        return min(confidence, 0.95)  # Cap at 0.95 (never 100% certain from inference)
    
    def _calculate_value_confidence(self, evidence_count: int, 
                                    signal_diversity: int) -> float:
        """
        Calculate confidence for value patterns
        Values need cross-signal validation for higher confidence
        """
        # Base from evidence count
        base = min(evidence_count / 8.0, 0.5)
        
        # Diversity bonus (multiple signal types = more confident)
        diversity_bonus = (signal_diversity - 1) * 0.1  # +0.1 for each additional signal type
        
        confidence = base + diversity_bonus
        
        return min(confidence, 0.90)
    
    def _store_inferred_trait(self, user_id: int, character: str, trait: Dict):
        """Store inferred trait in database"""
        cursor = self.db.cursor()
        
        evidence_summary = f"{trait['evidence_count']} occurrences"
        if 'signal_diversity' in trait:
            evidence_summary += f" across {trait['signal_diversity']} signal types"
        
        cursor.execute('''
            INSERT OR REPLACE INTO inferred_traits
            (user_id, character, trait_category, trait_name, confidence,
             evidence_count, evidence_summary, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            user_id, character, trait['category'], trait['trait'],
            trait['confidence'], trait['evidence_count'], evidence_summary
        ))
        
        self.db.commit()
    
    def get_inferred_traits(self, user_id: int, character: str,
                           min_confidence: float = 0.60) -> List[Dict]:
        """Get all inferred traits for user above confidence threshold"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT trait_category, trait_name, confidence,
                   evidence_count, evidence_summary,
                   first_detected, last_updated
            FROM inferred_traits
            WHERE user_id = ? AND character = ?
            AND confidence >= ?
            AND active = 1
            ORDER BY confidence DESC, evidence_count DESC
        ''', (user_id, character, min_confidence))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'category': row[0],
                'trait': row[1],
                'confidence': row[2],
                'evidence_count': row[3],
                'evidence_summary': row[4],
                'first_detected': row[5],
                'last_updated': row[6]
            })
        
        return results
    
    def format_for_ai_prompt(self, user_id: int, character: str) -> str:
        """Format inferred traits for AI prompt"""
        traits = self.get_inferred_traits(user_id, character, min_confidence=0.70)
        
        if not traits:
            return ""
        
        # Group by category
        by_category = {}
        for trait in traits:
            cat = trait['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(trait)
        
        prompt_parts = ["INFERRED PERSONALITY PATTERNS (Based on observations):"]
        
        # Big Five
        if 'big_five' in by_category:
            traits_str = ", ".join([t['trait'] for t in by_category['big_five'][:3]])
            prompt_parts.append(f"- Personality: {traits_str}")
        
        # Temperament
        if 'temperament' in by_category:
            traits_str = ", ".join([t['trait'] for t in by_category['temperament'][:2]])
            prompt_parts.append(f"- Temperament: {traits_str}")
        
        # Core Values (most important)
        if 'core_value' in by_category:
            values = by_category['core_value'][:3]
            for v in values:
                prompt_parts.append(f"- Values: {v['trait'].replace('_', ' ')} (confidence: {v['confidence']:.0%})")
        
        return "\n".join(prompt_parts)

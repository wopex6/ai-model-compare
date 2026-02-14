"""
Personality-Aware Context Interpreter
Interprets user events and context through the lens of their personality traits

Phase 3: Personality Integration
"""

import sqlite3
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class PersonalityAwareContextInterpreter:
    """
    Interprets context based on user personality
    
    Key Insight: "I failed my exam" means different things to different personalities:
    - High Neuroticism + High Conscientiousness: Perfectionist under pressure → needs validation
    - Low Neuroticism + High Conscientiousness: Competent person facing challenge → needs solutions
    - High Openness + Low Conscientiousness: Creative learner → needs new approaches
    """
    
    def __init__(self, db_path='integrated_users.db'):
        """Initialize personality interpreter with database connection"""
        self.db_path = db_path
        self._init_tables()
        
        # Event type patterns
        self.event_patterns = {
            'stress': [
                r'\b(stress|anxious|anxiety|worried|nervous|overwhelmed|pressure)\b',
                r'\bfeeling (stressed|anxious|nervous|overwhelmed)\b',
                r'\b(under pressure|too much)\b'
            ],
            'failure': [
                r'\b(failed|failure|didn\'t pass|lost|mess|messed up|wrong)\b',
                r'\b(didn\'t get|missed|unsuccessful)\b',
                r'\b(bad|terrible|awful) (result|outcome|grade)\b'
            ],
            'success': [
                r'\b(success|succeeded|achieved|accomplished|won|passed|nailed)\b',
                r'\b(great|excellent|amazing) (result|outcome|grade)\b',
                r'\b(did well|did great)\b'
            ],
            'goal': [
                r'\b(goal|aim|objective|target|want to|hoping to|plan to)\b',
                r'\b(my goal is|i want to|i hope to|i plan to)\b',
                r'\b(working toward|aiming for)\b'
            ],
            'relationship': [
                r'\b(friend|colleague|team|group|social|relationship)\b',
                r'\b(conflict|argument|disagreement|tension)\b',
                r'\b(connection|collaboration|working with)\b'
            ],
            'learning': [
                r'\b(learn|study|course|class|training|education)\b',
                r'\b(understand|figure out|master)\b',
                r'\b(struggling with|hard to understand)\b'
            ]
        }
        
    def _connect(self):
        """Open a SQLite connection with WAL mode and busy timeout."""
        conn = sqlite3.connect(self.db_path)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        return conn
    
    def _init_tables(self):
        """Initialize database tables for personality interpretations"""
        conn = self._connect()
        cursor = conn.cursor()
        
        # Create personality interpretations log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personality_interpretations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                event_type TEXT NOT NULL,
                raw_event TEXT NOT NULL,
                raw_message TEXT NOT NULL,
                interpretation TEXT NOT NULL,
                emotional_impact TEXT,
                recommended_approach TEXT,
                confidence REAL NOT NULL,
                traits_used TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_personality_interp_user 
            ON personality_interpretations(user_id, created_at DESC)
        ''')
        
        # Add personality interpretation columns to history_secondary if not exist
        try:
            cursor.execute('''
                ALTER TABLE history_secondary 
                ADD COLUMN personality_interpretation TEXT
            ''')
        except sqlite3.OperationalError:
            pass  # Column already exists
            
        try:
            cursor.execute('''
                ALTER TABLE history_secondary 
                ADD COLUMN interpretation_confidence REAL DEFAULT 0.0
            ''')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('''
                ALTER TABLE history_secondary 
                ADD COLUMN personality_traits_used TEXT
            ''')
        except sqlite3.OperationalError:
            pass
        
        conn.commit()
        conn.close()
        
        print("✓ Personality interpretation tables initialized")
    
    def get_user_personality(self, user_id: int) -> Dict:
        """
        Get user personality with 3-tier fallback system:
        
        Level 1: Formal assessment from psychology_traits table (if completed)
        Level 2: Inferred from inferred_traits table
        Level 3: Neutral defaults (0.5 for all traits)
        
        Returns:
            {
                'traits': {...},
                'source': 'assessment' | 'inferred' | 'default',
                'confidence': 0.0-1.0
            }
        """
        conn = self._connect()
        cursor = conn.cursor()
        
        # Level 1: Check for formal personality assessment in psychology_traits table
        cursor.execute('''
            SELECT trait_name, trait_value
            FROM psychology_traits
            WHERE user_id = ?
            ORDER BY updated_at DESC
        ''', (user_id,))
        
        psych_traits = cursor.fetchall()
        if psych_traits and len(psych_traits) >= 3:  # At least 3 traits assessed
            traits = {}
            for trait_name, trait_value in psych_traits:
                traits[trait_name.lower()] = trait_value
            
            # Check if we have the Big 5 traits
            has_big5 = all(k in traits for k in ['extraversion', 'agreeableness', 'conscientiousness', 'neuroticism', 'openness'])
            
            if has_big5:
                conn.close()
                return {
                    'traits': {
                        'extraversion': traits.get('extraversion', 0.5),
                        'agreeableness': traits.get('agreeableness', 0.5),
                        'conscientiousness': traits.get('conscientiousness', 0.5),
                        'neuroticism': traits.get('neuroticism', 0.5),
                        'openness': traits.get('openness', 0.5)
                    },
                    'source': 'assessment',
                    'confidence': 0.85  # High confidence for formal assessment
                }
        
        # Level 2: Check inferred_traits table (most recent for each trait)
        cursor.execute('''
            SELECT trait_name, confidence
            FROM inferred_traits
            WHERE user_id = ? AND active = 1
            ORDER BY last_updated DESC
        ''', (user_id,))
        
        inferred = cursor.fetchall()
        if inferred and len(inferred) >= 2:  # At least 2 traits inferred
            # Get unique traits (most recent)
            traits_dict = {}
            confidences = []
            
            for trait_name, confidence in inferred:
                trait_lower = trait_name.lower()
                if trait_lower not in traits_dict:
                    # Map to Big 5 if possible
                    if trait_lower in ['extraversion', 'agreeableness', 'conscientiousness', 'neuroticism', 'openness']:
                        traits_dict[trait_lower] = 0.7  # Moderate trait value for inferred
                        confidences.append(confidence if confidence else 0.6)
            
            if traits_dict:
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.6
                
                conn.close()
                return {
                    'traits': {
                        'extraversion': traits_dict.get('extraversion', 0.5),
                        'agreeableness': traits_dict.get('agreeableness', 0.5),
                        'conscientiousness': traits_dict.get('conscientiousness', 0.5),
                        'neuroticism': traits_dict.get('neuroticism', 0.5),
                        'openness': traits_dict.get('openness', 0.5)
                    },
                    'source': 'inferred',
                    'confidence': avg_confidence
                }
        
        conn.close()
        
        # Level 3: Neutral defaults
        return {
            'traits': {
                'extraversion': 0.5,
                'agreeableness': 0.5,
                'conscientiousness': 0.5,
                'neuroticism': 0.5,
                'openness': 0.5
            },
            'source': 'default',
            'confidence': 0.3
        }
    
    def interpret_event_with_personality(self, user_id: int, character: str, 
                                        event_data: Dict) -> Dict:
        """
        Main interpretation method - interprets event through personality lens
        
        Args:
            user_id: User ID
            character: Character name
            event_data: {
                'message': str,
                'context_type': str (optional),
                'context_value': str (optional)
            }
        
        Returns:
            {
                'interpreted_meaning': str,
                'emotional_impact': str,
                'recommended_approach': str,
                'confidence': float,
                'traits_used': dict,
                'personality_source': str
            }
        """
        # Get user personality
        personality_data = self.get_user_personality(user_id)
        traits = personality_data['traits']
        
        # Classify event type
        message = event_data.get('message', '')
        event_type = self._classify_event_type(message)
        
        # Route to appropriate interpreter
        if event_type == 'stress':
            interpretation = self._interpret_stress_event(message, traits)
        elif event_type == 'failure':
            interpretation = self._interpret_failure_event(message, traits)
        elif event_type == 'success':
            interpretation = self._interpret_success_event(message, traits)
        elif event_type == 'goal':
            interpretation = self._interpret_goal_event(message, traits)
        elif event_type == 'relationship':
            interpretation = self._interpret_relationship_event(message, traits)
        elif event_type == 'learning':
            interpretation = self._interpret_learning_event(message, traits)
        else:
            interpretation = self._interpret_general_event(message, traits)
        
        # Add personality metadata
        interpretation['traits_used'] = traits
        interpretation['personality_source'] = personality_data['source']
        interpretation['event_type'] = event_type
        
        # Adjust confidence based on personality source
        base_confidence = interpretation.get('confidence', 0.5)
        personality_confidence = personality_data['confidence']
        final_confidence = (base_confidence + personality_confidence) / 2
        interpretation['confidence'] = final_confidence
        
        # Store interpretation in database
        self._store_interpretation(
            user_id, character, event_type, event_data, message, interpretation
        )
        
        return interpretation
    
    def _classify_event_type(self, message: str) -> str:
        """Classify event into categories for targeted interpretation"""
        message_lower = message.lower()
        
        # Check each pattern category
        for event_type, patterns in self.event_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return event_type
        
        return 'general'
    
    def _interpret_stress_event(self, message: str, traits: Dict) -> Dict:
        """Interpret stress/anxiety mentions based on personality"""
        neuroticism = traits.get('neuroticism', 0.5)
        conscientiousness = traits.get('conscientiousness', 0.5)
        
        # High neuroticism + High conscientiousness
        if neuroticism > 0.7 and conscientiousness > 0.7:
            return {
                'interpreted_meaning': 'Perfectionist experiencing high pressure',
                'emotional_impact': 'high_anxiety',
                'recommended_approach': 'validate_then_reframe',
                'guidance': 'Acknowledge the stress is real, validate perfectionist standards, then help reframe expectations',
                'confidence': 0.85
            }
        
        # High neuroticism + Low conscientiousness
        elif neuroticism > 0.7 and conscientiousness < 0.4:
            return {
                'interpreted_meaning': 'Overwhelmed person feeling scattered',
                'emotional_impact': 'anxiety_with_disorganization',
                'recommended_approach': 'emotional_support_plus_structure',
                'guidance': 'Provide emotional support first, then help create structure and manageable steps',
                'confidence': 0.80
            }
        
        # Low neuroticism + High conscientiousness
        elif neuroticism < 0.4 and conscientiousness > 0.7:
            return {
                'interpreted_meaning': 'Competent person facing temporary challenge',
                'emotional_impact': 'manageable_concern',
                'recommended_approach': 'problem_solving_focus',
                'guidance': 'Skip excessive validation, focus on practical solutions and action steps',
                'confidence': 0.80
            }
        
        # Low neuroticism + Low conscientiousness
        elif neuroticism < 0.4 and conscientiousness < 0.4:
            return {
                'interpreted_meaning': 'Laid-back person in stressful situation',
                'emotional_impact': 'mild_concern',
                'recommended_approach': 'gentle_guidance',
                'guidance': 'Light touch, offer options without pressure, respect their coping style',
                'confidence': 0.75
            }
        
        # Middle range
        else:
            return {
                'interpreted_meaning': 'Person experiencing moderate stress',
                'emotional_impact': 'moderate_stress',
                'recommended_approach': 'balanced_support',
                'guidance': 'Balance emotional support with practical suggestions',
                'confidence': 0.65
            }
    
    def _interpret_failure_event(self, message: str, traits: Dict) -> Dict:
        """Interpret failure/setback mentions based on personality"""
        neuroticism = traits.get('neuroticism', 0.5)
        openness = traits.get('openness', 0.5)
        
        # High neuroticism + Low openness (Fixed mindset + taking it hard)
        if neuroticism > 0.7 and openness < 0.4:
            return {
                'interpreted_meaning': 'Fixed mindset person taking failure personally',
                'emotional_impact': 'deep_discouragement',
                'recommended_approach': 'validation_then_gradual_reframe',
                'guidance': 'Extensive validation, then very gradually introduce growth mindset',
                'confidence': 0.85
            }
        
        # High neuroticism + High openness (Self-critical but growth-oriented)
        elif neuroticism > 0.7 and openness > 0.7:
            return {
                'interpreted_meaning': 'Self-critical learner ready to grow',
                'emotional_impact': 'painful_but_motivated',
                'recommended_approach': 'acknowledge_pain_focus_learning',
                'guidance': 'Acknowledge the pain is real, then pivot to what can be learned',
                'confidence': 0.80
            }
        
        # Low neuroticism + High openness (Resilient learner)
        elif neuroticism < 0.4 and openness > 0.7:
            return {
                'interpreted_meaning': 'Resilient learner seeing opportunity',
                'emotional_impact': 'brief_disappointment',
                'recommended_approach': 'quick_pivot_to_learning',
                'guidance': 'Brief acknowledgment, then straight to "what did you learn" and next steps',
                'confidence': 0.80
            }
        
        # Low neuroticism + Low openness (Moving on naturally)
        elif neuroticism < 0.4 and openness < 0.4:
            return {
                'interpreted_meaning': 'Pragmatic person moving forward',
                'emotional_impact': 'minimal_impact',
                'recommended_approach': 'simple_encouragement',
                'guidance': 'Simple encouragement, respect their natural resilience',
                'confidence': 0.75
            }
        
        # Middle range
        else:
            return {
                'interpreted_meaning': 'Person experiencing setback',
                'emotional_impact': 'moderate_disappointment',
                'recommended_approach': 'balanced_perspective',
                'guidance': 'Balance validation with forward-looking perspective',
                'confidence': 0.65
            }
    
    def _interpret_success_event(self, message: str, traits: Dict) -> Dict:
        """Interpret success/achievement mentions based on personality"""
        extraversion = traits.get('extraversion', 0.5)
        conscientiousness = traits.get('conscientiousness', 0.5)
        
        # High extraversion + High conscientiousness (Driven achiever)
        if extraversion > 0.7 and conscientiousness > 0.7:
            return {
                'interpreted_meaning': 'Driven achiever celebrating milestone',
                'emotional_impact': 'high_energy_satisfaction',
                'recommended_approach': 'enthusiastic_celebration_then_next',
                'guidance': 'Match their enthusiasm, celebrate big, then help channel energy to next goal',
                'confidence': 0.80
            }
        
        # Low extraversion + High conscientiousness (Quiet achiever)
        elif extraversion < 0.4 and conscientiousness > 0.7:
            return {
                'interpreted_meaning': 'Quiet achiever reaching standards',
                'emotional_impact': 'quiet_satisfaction',
                'recommended_approach': 'respectful_acknowledgment',
                'guidance': 'Acknowledge without over-celebrating, focus on the quality of work',
                'confidence': 0.75
            }
        
        # High extraversion + Low conscientiousness (Spontaneous celebrator)
        elif extraversion > 0.7 and conscientiousness < 0.4:
            return {
                'interpreted_meaning': 'Spontaneous person enjoying win',
                'emotional_impact': 'joyful_moment',
                'recommended_approach': 'celebrate_naturally',
                'guidance': 'Celebrate the moment, enjoy the win, light touch on sustainability',
                'confidence': 0.75
            }
        
        # Middle range
        else:
            return {
                'interpreted_meaning': 'Person achieving positive outcome',
                'emotional_impact': 'satisfaction',
                'recommended_approach': 'genuine_acknowledgment',
                'guidance': 'Genuine acknowledgment and encouragement for continued growth',
                'confidence': 0.65
            }
    
    def _interpret_goal_event(self, message: str, traits: Dict) -> Dict:
        """Interpret goal-setting mentions based on personality"""
        conscientiousness = traits.get('conscientiousness', 0.5)
        openness = traits.get('openness', 0.5)
        
        # High conscientiousness + High openness (Methodical explorer)
        if conscientiousness > 0.7 and openness > 0.7:
            return {
                'interpreted_meaning': 'Methodical explorer setting ambitious goals',
                'emotional_impact': 'excited_and_systematic',
                'recommended_approach': 'structured_exploration',
                'guidance': 'Help create structured plan that allows for creative exploration',
                'confidence': 0.80
            }
        
        # High conscientiousness + Low openness (Traditional planner)
        elif conscientiousness > 0.7 and openness < 0.4:
            return {
                'interpreted_meaning': 'Traditional planner with clear objectives',
                'emotional_impact': 'focused_determination',
                'recommended_approach': 'detailed_milestones',
                'guidance': 'Help break into clear, measurable milestones with timelines',
                'confidence': 0.80
            }
        
        # Low conscientiousness + High openness (Free-spirited explorer)
        elif conscientiousness < 0.4 and openness > 0.7:
            return {
                'interpreted_meaning': 'Free-spirited person with flexible aims',
                'emotional_impact': 'curious_and_open',
                'recommended_approach': 'flexible_guidance',
                'guidance': 'Offer light structure, focus on exploration and discovery over rigid plans',
                'confidence': 0.75
            }
        
        # Low conscientiousness + Low openness (Needs structure help)
        elif conscientiousness < 0.4 and openness < 0.4:
            return {
                'interpreted_meaning': 'Person needing structure and clarity',
                'emotional_impact': 'uncertain_direction',
                'recommended_approach': 'provide_clear_framework',
                'guidance': 'Provide simple, clear framework and step-by-step guidance',
                'confidence': 0.75
            }
        
        # Middle range
        else:
            return {
                'interpreted_meaning': 'Person setting goals',
                'emotional_impact': 'motivated',
                'recommended_approach': 'balanced_planning',
                'guidance': 'Help create balanced plan with structure and flexibility',
                'confidence': 0.65
            }
    
    def _interpret_relationship_event(self, message: str, traits: Dict) -> Dict:
        """Interpret social/relationship mentions based on personality"""
        agreeableness = traits.get('agreeableness', 0.5)
        extraversion = traits.get('extraversion', 0.5)
        
        # High agreeableness + High extraversion (Social harmony seeker)
        if agreeableness > 0.7 and extraversion > 0.7:
            return {
                'interpreted_meaning': 'Socially engaged person valuing harmony',
                'emotional_impact': 'connection_focused',
                'recommended_approach': 'empathy_and_collaboration',
                'guidance': 'Emphasize connection, collaboration, and mutual understanding',
                'confidence': 0.75
            }
        
        # Low agreeableness + Low extraversion (Independent operator)
        elif agreeableness < 0.4 and extraversion < 0.4:
            return {
                'interpreted_meaning': 'Independent person managing social dynamics',
                'emotional_impact': 'pragmatic_approach',
                'recommended_approach': 'direct_solutions',
                'guidance': 'Focus on practical solutions, respect need for independence',
                'confidence': 0.75
            }
        
        # Middle range
        else:
            return {
                'interpreted_meaning': 'Person navigating social situation',
                'emotional_impact': 'social_awareness',
                'recommended_approach': 'balanced_perspective',
                'guidance': 'Balance social harmony with practical outcomes',
                'confidence': 0.65
            }
    
    def _interpret_learning_event(self, message: str, traits: Dict) -> Dict:
        """Interpret learning/education mentions based on personality"""
        openness = traits.get('openness', 0.5)
        conscientiousness = traits.get('conscientiousness', 0.5)
        
        # High openness + High conscientiousness (Dedicated learner)
        if openness > 0.7 and conscientiousness > 0.7:
            return {
                'interpreted_meaning': 'Dedicated learner with deep curiosity',
                'emotional_impact': 'engaged_and_systematic',
                'recommended_approach': 'deep_exploration_with_structure',
                'guidance': 'Support deep exploration with structured learning paths',
                'confidence': 0.80
            }
        
        # High openness + Low conscientiousness (Curious dabbler)
        elif openness > 0.7 and conscientiousness < 0.4:
            return {
                'interpreted_meaning': 'Curious learner exploring broadly',
                'emotional_impact': 'excited_but_scattered',
                'recommended_approach': 'channel_curiosity',
                'guidance': 'Help channel curiosity into focused learning spurts',
                'confidence': 0.75
            }
        
        # Low openness + High conscientiousness (Methodical student)
        elif openness < 0.4 and conscientiousness > 0.7:
            return {
                'interpreted_meaning': 'Methodical learner following structure',
                'emotional_impact': 'disciplined_approach',
                'recommended_approach': 'systematic_progression',
                'guidance': 'Provide clear progression path with measurable milestones',
                'confidence': 0.75
            }
        
        # Middle range
        else:
            return {
                'interpreted_meaning': 'Person engaged in learning',
                'emotional_impact': 'learning_oriented',
                'recommended_approach': 'supportive_guidance',
                'guidance': 'Provide supportive guidance tailored to learning style',
                'confidence': 0.65
            }
    
    def _interpret_general_event(self, message: str, traits: Dict) -> Dict:
        """General interpretation for events that don't fit specific categories"""
        # Use neuroticism as general emotional sensitivity indicator
        neuroticism = traits.get('neuroticism', 0.5)
        
        if neuroticism > 0.7:
            approach = 'gentle_and_supportive'
            guidance = 'Use gentle, supportive tone with validation'
        elif neuroticism < 0.3:
            approach = 'direct_and_practical'
            guidance = 'Use direct, practical approach without excessive emotion'
        else:
            approach = 'balanced'
            guidance = 'Use balanced approach with moderate support'
        
        return {
            'interpreted_meaning': 'User sharing experience',
            'emotional_impact': 'neutral_to_moderate',
            'recommended_approach': approach,
            'guidance': guidance,
            'confidence': 0.50
        }
    
    def format_for_ai_prompt(self, interpretation: Dict) -> str:
        """Format interpretation for inclusion in AI prompt"""
        formatted = f"""
PERSONALITY-AWARE INTERPRETATION:
- Meaning: {interpretation.get('interpreted_meaning', 'N/A')}
- Emotional Impact: {interpretation.get('emotional_impact', 'N/A')}
- Recommended Approach: {interpretation.get('recommended_approach', 'N/A')}
- Guidance: {interpretation.get('guidance', 'N/A')}
- Confidence: {interpretation.get('confidence', 0.0):.0%}
- Personality Source: {interpretation.get('personality_source', 'unknown')}

IMPORTANT: Use this interpretation to inform your response style and content.
Adapt your approach based on the recommended guidance above.
"""
        return formatted
    
    def _store_interpretation(self, user_id: int, character: str, event_type: str,
                            event_data: Dict, message: str, interpretation: Dict):
        """Store interpretation in database for learning and analysis"""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO personality_interpretations 
            (user_id, character, event_type, raw_event, raw_message,
             interpretation, emotional_impact, recommended_approach, 
             confidence, traits_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            character,
            event_type,
            json.dumps(event_data),
            message,
            interpretation.get('interpreted_meaning', ''),
            interpretation.get('emotional_impact', ''),
            interpretation.get('recommended_approach', ''),
            interpretation.get('confidence', 0.0),
            json.dumps(interpretation.get('traits_used', {}))
        ))
        
        conn.commit()
        conn.close()
    
    def get_interpretation_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get recent interpretation history for user"""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT event_type, raw_message, interpretation, emotional_impact,
                   recommended_approach, confidence, traits_used, created_at
            FROM personality_interpretations
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'event_type': row[0],
                'message': row[1],
                'interpretation': row[2],
                'emotional_impact': row[3],
                'recommended_approach': row[4],
                'confidence': row[5],
                'traits_used': json.loads(row[6]) if row[6] else {},
                'timestamp': row[7]
            })
        
        return history


# Test function
if __name__ == "__main__":
    print("="*70)
    print("PERSONALITY-AWARE CONTEXT INTERPRETER - TEST")
    print("="*70)
    
    interpreter = PersonalityAwareContextInterpreter()
    
    # Test scenarios
    test_cases = [
        {
            'name': 'High Neuroticism + High Conscientiousness (Stress)',
            'user_id': 1,
            'character': 'Coach Max',
            'message': "I'm feeling really stressed about my project deadlines",
            'expected_meaning': 'Perfectionist'
        },
        {
            'name': 'Low Neuroticism + High Openness (Failure)',
            'user_id': 2,
            'character': 'Sage Wei',
            'message': "I failed my coding interview today",
            'expected_meaning': 'Resilient learner'
        },
        {
            'name': 'High Conscientiousness (Goal)',
            'user_id': 1,
            'character': 'Coach Jordan',
            'message': "My goal is to become a data scientist",
            'expected_meaning': 'planner'
        }
    ]
    
    print("\nRunning test scenarios...\n")
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['name']}")
        print(f"Message: \"{test['message']}\"")
        
        result = interpreter.interpret_event_with_personality(
            test['user_id'],
            test['character'],
            {'message': test['message']}
        )
        
        print(f"✓ Interpretation: {result['interpreted_meaning']}")
        print(f"✓ Approach: {result['recommended_approach']}")
        print(f"✓ Confidence: {result['confidence']:.0%}")
        print(f"✓ Source: {result['personality_source']}")
        print()
    
    print("="*70)
    print("✅ ALL TESTS COMPLETED")
    print("="*70)

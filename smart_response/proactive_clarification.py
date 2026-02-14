"""
Proactive Clarification System
Asks clarifying questions when confidence < 60% or context gaps detected.
Identifies ambiguity, missing info, and generates targeted questions.
"""

import re
import json
import sqlite3
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class ClarificationReason(Enum):
    AMBIGUOUS_GOAL = "ambiguous_goal"
    MISSING_CONTEXT = "missing_context"
    CONFLICTING_INFO = "conflicting_info"
    VAGUE_TIMEFRAME = "vague_timeframe"
    UNCLEAR_PRIORITY = "unclear_priority"
    EMOTIONAL_UNCERTAINTY = "emotional_uncertainty"
    MULTIPLE_INTERPRETATIONS = "multiple_interpretations"


class ImportanceLevel(Enum):
    CRITICAL = "critical"  # Must clarify before proceeding
    HIGH = "high"          # Should clarify for best response
    NORMAL = "normal"      # Nice to clarify but can proceed


@dataclass
class ClarificationQuestion:
    """A question to ask the user for clarification"""
    question: str
    reason: ClarificationReason
    importance: ImportanceLevel
    context_gap: str  # What info is missing
    suggested_options: List[str] = None  # Multiple choice options if applicable
    
    def to_dict(self) -> Dict:
        return {
            'question': self.question,
            'reason': self.reason.value,
            'importance': self.importance.value,
            'context_gap': self.context_gap,
            'suggested_options': self.suggested_options
        }


@dataclass
class ConfidenceScore:
    """Confidence assessment for understanding user intent"""
    overall: float  # 0.0 - 1.0
    goal_clarity: float
    emotional_clarity: float
    context_sufficiency: float
    action_clarity: float
    
    def needs_clarification(self, threshold: float = 0.6) -> bool:
        """Returns True if any dimension is below threshold"""
        return (self.overall < threshold or 
                self.goal_clarity < threshold or
                self.action_clarity < threshold)


class ProactiveClarificationSystem:
    """
    Detects uncertainty and generates clarifying questions.
    
    Key principles:
    - Don't ask too many questions (max 1-2 per response)
    - Prioritize questions that will most improve the response
    - Remember what we've already asked
    - Adapt question style to user's communication preference
    """
    
    # Ambiguity indicators
    VAGUE_PHRASES = [
        r'\b(something|anything|stuff|things?)\b',
        r'\b(maybe|perhaps|might|could be)\b',
        r'\b(kind of|sort of|kinda|sorta)\b',
        r'\b(whatever|whenever|wherever)\b',
        r'\b(some|few|many|several)\b(?!\s+\d)',  # Not followed by number
        r'\b(soon|later|eventually|sometime)\b',
        r'\b(better|worse|more|less)\b(?!\s+than)',  # Comparative without reference
    ]
    
    # Emotional distress indicators (trigger supportive clarification)
    DISTRESS_INDICATORS = [
        r'\b(overwhelmed|stressed|anxious|depressed|hopeless)\b',
        r'\b(can\'t cope|too much|falling apart|breaking down)\b',
        r'\b(don\'t know what to do|lost|stuck|trapped)\b',
        r'\b(everything is|nothing works|always|never)\b',
    ]
    
    # Decision-making indicators (trigger option exploration)
    DECISION_INDICATORS = [
        r'\b(should i|which one|what if|either|or)\b',
        r'\b(deciding|choose|pick|option|alternative)\b',
        r'\b(pros and cons|trade-?off|weighing)\b',
    ]
    
    # Goal-setting indicators (trigger specificity questions)
    GOAL_INDICATORS = [
        r'\b(i want to|i need to|i\'m trying to|my goal)\b',
        r'\b(i wish|i hope|dream of|aspire)\b',
        r'\b(achieve|accomplish|reach|attain)\b',
    ]
    
    # Relationship indicators (trigger context questions)
    RELATIONSHIP_INDICATORS = [
        r'\b(my (partner|spouse|husband|wife|boyfriend|girlfriend))\b',
        r'\b(my (boss|colleague|coworker|friend|family))\b',
        r'\b(relationship|marriage|dating|breakup)\b',
    ]
    
    # Missing context indicators
    CONTEXT_GAPS = {
        'timeframe': [
            r'\b(when|how long|how soon|deadline)\b',
            r'\b(start|begin|finish|complete|done)\b',
        ],
        'specificity': [
            r'\b(this|that|it|they|them)\b(?!\s+is|\s+are|\s+was)',  # Pronouns without clear referent
        ],
        'quantity': [
            r'\b(some|few|many|lot|bunch)\b',
        ],
        'priority': [
            r'\b(important|urgent|asap|priority)\b',
        ],
    }
    
    # Question templates by context gap type
    QUESTION_TEMPLATES = {
        'goal': [
            "What specific outcome are you hoping for?",
            "What would success look like for you here?",
            "Could you tell me more about what you're trying to achieve?",
        ],
        'timeframe': [
            "Is there a specific timeframe you're working with?",
            "When do you need this by?",
            "How urgent is this for you?",
        ],
        'context': [
            "Could you give me a bit more background?",
            "What's prompted this?",
            "Is there anything else I should know about this situation?",
        ],
        'priority': [
            "What's most important to you in this?",
            "If you had to choose one thing to focus on, what would it be?",
            "What would you like me to prioritize?",
        ],
        'emotion': [
            "How are you feeling about this?",
            "What's your main concern here?",
            "Is there something specific that's worrying you?",
        ],
        'clarify_reference': [
            "When you mention '{reference}', could you tell me more about that?",
            "I want to make sure I understand - what do you mean by '{reference}'?",
        ],
        # New template categories
        'distress_support': [
            "That sounds really difficult. What would be most helpful for you right now - someone to listen, or to explore some options?",
            "I hear you. Before we dive in, what's weighing on you most heavily?",
            "It sounds like you're going through a lot. What feels most urgent to address?",
        ],
        'decision_explore': [
            "What factors are most important to you in making this decision?",
            "Have you considered what the best and worst outcomes might be for each option?",
            "What's holding you back from deciding right now?",
        ],
        'goal_specificity': [
            "That's a great goal! What would be the first sign that you're making progress?",
            "What's been stopping you from achieving this so far?",
            "How will you know when you've succeeded?",
        ],
        'relationship_context': [
            "How long have you been dealing with this situation?",
            "What's the dynamic typically like between you two?",
            "Have you talked to them about how you feel?",
        ],
    }
    
    def __init__(self, db_connection: sqlite3.Connection):
        self.db = db_connection
        self._init_tables()
    
    def _init_tables(self):
        """Create tables for tracking clarifications"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clarification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character_id TEXT NOT NULL,
                question_asked TEXT NOT NULL,
                reason TEXT NOT NULL,
                context_gap TEXT,
                user_response TEXT,
                was_helpful BOOLEAN,
                asked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                responded_at DATETIME
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS context_gaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character_id TEXT NOT NULL,
                gap_type TEXT NOT NULL,
                gap_description TEXT,
                resolved BOOLEAN DEFAULT 0,
                detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved_at DATETIME
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_clarification_user ON clarification_history(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_context_gaps_user ON context_gaps(user_id)')
        
        self.db.commit()
    
    def analyze_message(self, message: str, user_context: Dict = None) -> Tuple[ConfidenceScore, List[ClarificationQuestion]]:
        """
        Analyze a message for clarity and generate clarification questions if needed.
        
        Returns:
            (confidence_score, list_of_questions)
        """
        message_lower = message.lower()
        
        # Calculate confidence scores
        confidence = self._calculate_confidence(message, user_context)
        
        questions = []
        
        # Only generate questions if confidence is low
        if confidence.needs_clarification():
            questions = self._generate_questions(message, confidence, user_context)
        
        return confidence, questions
    
    def _calculate_confidence(self, message: str, user_context: Dict = None) -> ConfidenceScore:
        """Calculate confidence in understanding the user's intent"""
        message_lower = message.lower()
        
        # Count vagueness indicators
        vague_count = sum(1 for pattern in self.VAGUE_PHRASES 
                        if re.search(pattern, message_lower))
        
        # Message length factor (very short = less context)
        word_count = len(message.split())
        length_factor = min(1.0, word_count / 10)  # Max out at 10 words
        
        # Check for clear goal indicators
        goal_indicators = [
            r'\b(i want|i need|i\'d like|help me|can you)\b',
            r'\b(my goal|i\'m trying to|i hope to)\b',
            r'\?$',  # Questions are clear goals
        ]
        has_clear_goal = any(re.search(p, message_lower) for p in goal_indicators)
        
        # Check for emotional clarity
        emotion_indicators = [
            r'\b(i feel|i\'m feeling|makes me|i\'m \w+ed)\b',
            r'\b(happy|sad|angry|frustrated|excited|worried|anxious|stressed)\b',
        ]
        has_emotion_clarity = any(re.search(p, message_lower) for p in emotion_indicators)
        
        # Check for action clarity
        action_indicators = [
            r'\b(should i|how do i|what should|can i)\b',
            r'\b(tell me|show me|explain|help)\b',
        ]
        has_action_clarity = any(re.search(p, message_lower) for p in action_indicators)
        
        # Context from previous conversations
        has_context = bool(user_context and user_context.get('conversation_summary'))
        
        # Calculate scores
        vague_penalty = min(0.3, vague_count * 0.1)
        
        goal_clarity = 0.8 if has_clear_goal else 0.5
        goal_clarity = max(0.3, goal_clarity - vague_penalty)
        
        emotional_clarity = 0.9 if has_emotion_clarity else 0.6
        
        context_sufficiency = 0.7 if has_context else 0.5
        context_sufficiency = max(0.3, context_sufficiency * length_factor)
        
        action_clarity = 0.8 if has_action_clarity else 0.5
        action_clarity = max(0.3, action_clarity - vague_penalty)
        
        # Overall is weighted average
        overall = (
            goal_clarity * 0.35 +
            emotional_clarity * 0.2 +
            context_sufficiency * 0.25 +
            action_clarity * 0.2
        )
        
        return ConfidenceScore(
            overall=overall,
            goal_clarity=goal_clarity,
            emotional_clarity=emotional_clarity,
            context_sufficiency=context_sufficiency,
            action_clarity=action_clarity
        )
    
    def _generate_questions(self, message: str, confidence: ConfidenceScore, 
                           user_context: Dict = None) -> List[ClarificationQuestion]:
        """Generate clarification questions based on detected gaps"""
        questions = []
        message_lower = message.lower()
        
        # Prioritize by what's most unclear
        gaps = []
        
        # Check for emotional distress first (highest priority)
        has_distress = any(re.search(p, message_lower) for p in self.DISTRESS_INDICATORS)
        if has_distress:
            gaps.append(('distress_support', ClarificationReason.EMOTIONAL_UNCERTAINTY, ImportanceLevel.CRITICAL))
        
        # Check for decision-making context
        has_decision = any(re.search(p, message_lower) for p in self.DECISION_INDICATORS)
        if has_decision and confidence.action_clarity < 0.7:
            gaps.append(('decision_explore', ClarificationReason.UNCLEAR_PRIORITY, ImportanceLevel.HIGH))
        
        # Check for goal-setting context
        has_goal = any(re.search(p, message_lower) for p in self.GOAL_INDICATORS)
        if has_goal and confidence.goal_clarity < 0.7:
            gaps.append(('goal_specificity', ClarificationReason.AMBIGUOUS_GOAL, ImportanceLevel.HIGH))
        
        # Check for relationship context
        has_relationship = any(re.search(p, message_lower) for p in self.RELATIONSHIP_INDICATORS)
        if has_relationship and confidence.context_sufficiency < 0.6:
            gaps.append(('relationship_context', ClarificationReason.MISSING_CONTEXT, ImportanceLevel.HIGH))
        
        # Standard clarity checks (lower priority if specific triggers found)
        if not gaps:
            if confidence.goal_clarity < 0.6:
                gaps.append(('goal', ClarificationReason.AMBIGUOUS_GOAL, ImportanceLevel.HIGH))
            
            if confidence.context_sufficiency < 0.5:
                gaps.append(('context', ClarificationReason.MISSING_CONTEXT, ImportanceLevel.NORMAL))
            
            if confidence.action_clarity < 0.5:
                gaps.append(('priority', ClarificationReason.UNCLEAR_PRIORITY, ImportanceLevel.NORMAL))
        
        # Check for vague references that need clarification
        vague_refs = re.findall(r'\b(this|that|it)\s+(\w+)', message_lower)
        for ref in vague_refs[:1]:  # Only first one
            gaps.append(('clarify_reference', ClarificationReason.MULTIPLE_INTERPRETATIONS, ImportanceLevel.HIGH))
        
        # Check for timeframe ambiguity
        time_vague = re.search(r'\b(soon|later|eventually|sometime)\b', message_lower)
        if time_vague:
            gaps.append(('timeframe', ClarificationReason.VAGUE_TIMEFRAME, ImportanceLevel.NORMAL))
        
        # Generate questions for top 2 gaps
        for gap_type, reason, importance in gaps[:2]:
            templates = self.QUESTION_TEMPLATES.get(gap_type, [])
            if templates:
                # Pick first template (could randomize or personalize)
                question_text = templates[0]
                
                # Fill in any placeholders
                if '{reference}' in question_text and vague_refs:
                    question_text = question_text.format(reference=vague_refs[0][1])
                
                questions.append(ClarificationQuestion(
                    question=question_text,
                    reason=reason,
                    importance=importance,
                    context_gap=gap_type
                ))
        
        return questions
    
    def should_ask_clarification(self, user_id: int, character_id: str,
                                 questions: List[ClarificationQuestion]) -> List[ClarificationQuestion]:
        """
        Filter questions based on:
        - Don't ask same question twice in a row
        - Don't ask too many questions in one session
        - Prioritize by importance
        """
        if not questions:
            return []
        
        cursor = self.db.cursor()
        
        # Check recent questions asked
        cursor.execute('''
            SELECT question_asked, context_gap FROM clarification_history
            WHERE user_id = ? AND character_id = ?
            ORDER BY asked_at DESC LIMIT 5
        ''', (user_id, character_id))
        
        recent = cursor.fetchall()
        recent_questions = [r[0] for r in recent]
        recent_gaps = [r[1] for r in recent]
        
        # Filter out recently asked questions/gaps
        filtered = []
        for q in questions:
            if q.question not in recent_questions and q.context_gap not in recent_gaps:
                filtered.append(q)
        
        # Sort by importance
        importance_order = {ImportanceLevel.CRITICAL: 0, ImportanceLevel.HIGH: 1, ImportanceLevel.NORMAL: 2}
        filtered.sort(key=lambda q: importance_order.get(q.importance, 3))
        
        # Return max 2 questions
        return filtered[:2]
    
    def record_question_asked(self, user_id: int, character_id: str, 
                             question: ClarificationQuestion):
        """Record that we asked a clarification question"""
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO clarification_history
            (user_id, character_id, question_asked, reason, context_gap)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, character_id, question.question, 
              question.reason.value, question.context_gap))
        self.db.commit()
    
    def record_context_gap(self, user_id: int, character_id: str,
                          gap_type: str, description: str):
        """Record a detected context gap"""
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO context_gaps
            (user_id, character_id, gap_type, gap_description)
            VALUES (?, ?, ?, ?)
        ''', (user_id, character_id, gap_type, description))
        self.db.commit()
    
    def format_clarification_for_response(self, questions: List[ClarificationQuestion],
                                          user_language: Dict = None) -> str:
        """
        Format clarification questions to append to AI response.
        Adapts style based on user's communication preferences.
        """
        if not questions:
            return ""
        
        # Adapt formality based on user language
        is_brief = user_language and user_language.get('preferred_length') in ('brief', 'very_brief')
        
        if len(questions) == 1:
            q = questions[0]
            if is_brief:
                prefix = "Quick question: "
            else:
                prefix = "To help me give you the best response, "
            return f"\n\n{prefix}{q.question}"
        else:
            # Multiple questions
            if is_brief:
                prefix = "Quick questions:"
            else:
                prefix = "A couple of things that would help me assist you better:"
            
            formatted = [f"\n\n{prefix}"]
            for i, q in enumerate(questions[:2], 1):
                formatted.append(f"\n{i}. {q.question}")
            return "".join(formatted)
    
    def get_pending_clarifications(self, user_id: int, character_id: str) -> List[Dict]:
        """Get clarification questions that haven't been answered"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT id, question_asked, reason, context_gap, asked_at
            FROM clarification_history
            WHERE user_id = ? AND character_id = ? 
            AND user_response IS NULL
            ORDER BY asked_at DESC LIMIT 5
        ''', (user_id, character_id))
        
        return [
            {'id': r[0], 'question': r[1], 'reason': r[2], 
             'context_gap': r[3], 'asked_at': r[4]}
            for r in cursor.fetchall()
        ]


    # --- Phase 4 Enhancements: Multi-Perspective Clarification ---
    
    def analyze_with_perspectives(
        self, 
        message: str, 
        user_context: Dict = None,
        character_trait_system=None,
        personality: Dict[str, float] = None
    ) -> Tuple[ConfidenceScore, List[ClarificationQuestion], List[Dict]]:
        """
        Enhanced analysis that generates multi-perspective clarifying questions.
        Each character lens asks different types of clarifying questions.
        
        Returns:
            (confidence, standard_questions, perspective_questions)
            perspective_questions is a list of dicts with character_name, lens, question
        """
        confidence, standard_questions = self.analyze_message(message, user_context)
        
        perspective_questions = []
        
        if not confidence.needs_clarification(threshold=0.65):
            return confidence, standard_questions, perspective_questions
        
        if not character_trait_system:
            return confidence, standard_questions, perspective_questions
        
        # Get situation analysis to find relevant characters
        try:
            situation = character_trait_system.analyze_situation(message)
        except Exception:
            situation = None
        
        # Map context gaps to character lens questions
        perspective_questions = self._generate_perspective_questions(
            message, confidence, situation, character_trait_system
        )
        
        return confidence, standard_questions, perspective_questions
    
    def _generate_perspective_questions(
        self,
        message: str,
        confidence: ConfidenceScore,
        situation,
        character_trait_system
    ) -> List[Dict]:
        """Generate clarifying questions from different character perspectives"""
        
        # Character lens question templates
        LENS_QUESTIONS = {
            'stoicism': {
                'goal': "What is within your control here, and what isn't?",
                'emotion': "What virtue do you want to practice in this situation?",
                'context': "What would the wisest version of yourself do here?",
                'priority': "If this were your last day, what would matter most?",
            },
            'empathy': {
                'goal': "What outcome would feel right emotionally, not just logically?",
                'emotion': "When you sit with this feeling, what comes up for you?",
                'context': "Who else is affected by this, and how are they feeling?",
                'priority': "What does your heart tell you is most important here?",
            },
            'analytical': {
                'goal': "What specific metrics would tell you this is going well?",
                'emotion': "On a scale of 1-10, how urgent does this feel?",
                'context': "What data or facts would help you make this decision?",
                'priority': "What are the top 3 factors you're weighing?",
            },
            'motivation': {
                'goal': "What would achieving this make possible for you?",
                'emotion': "What's the fire behind this — what drives you?",
                'context': "What's the biggest obstacle standing in your way right now?",
                'priority': "If you could only fix one thing today, what would it be?",
            },
            'wisdom': {
                'goal': "How does this fit into the bigger picture of your life?",
                'emotion': "What lesson might this experience be teaching you?",
                'context': "Have you faced something similar before? What did you learn?",
                'priority': "What would you advise a close friend in this situation?",
            },
            'pragmatism': {
                'goal': "What's the simplest next step you could take?",
                'emotion': "What would make tomorrow 10% better?",
                'context': "What resources or support do you already have?",
                'priority': "What's the deadline or time pressure here?",
            },
        }
        
        # Determine which gaps exist
        gap_types = []
        if confidence.goal_clarity < 0.6:
            gap_types.append('goal')
        if confidence.emotional_clarity < 0.6:
            gap_types.append('emotion')
        if confidence.context_sufficiency < 0.5:
            gap_types.append('context')
        if confidence.action_clarity < 0.5:
            gap_types.append('priority')
        
        if not gap_types:
            gap_types = ['context']  # Default
        
        # Select 2-3 diverse character lenses
        selected_lenses = self._select_diverse_lenses(
            message, gap_types, character_trait_system
        )
        
        perspective_questions = []
        primary_gap = gap_types[0]
        
        for lens_name, display_name in selected_lenses[:3]:
            templates = LENS_QUESTIONS.get(lens_name, {})
            question = templates.get(primary_gap)
            if question:
                perspective_questions.append({
                    'character_lens': lens_name,
                    'character_name': display_name,
                    'gap_type': primary_gap,
                    'question': question
                })
        
        return perspective_questions
    
    def _select_diverse_lenses(
        self, message: str, gap_types: List[str], character_trait_system
    ) -> List[Tuple[str, str]]:
        """Select diverse character lenses for multi-perspective questions"""
        
        # Map traits to lenses
        TRAIT_TO_LENS = {
            'stoicism': ('stoicism', 'Stoic Advisor'),
            'empathy': ('empathy', 'Empathetic Guide'),
            'analytical_thinking': ('analytical', 'Analytical Thinker'),
            'motivation': ('motivation', 'Motivational Coach'),
            'wisdom': ('wisdom', 'Wise Mentor'),
            'pragmatism': ('pragmatism', 'Practical Advisor'),
            'directness': ('pragmatism', 'Practical Advisor'),
            'warmth': ('empathy', 'Empathetic Guide'),
            'humor': ('motivation', 'Motivational Coach'),
            'structure': ('analytical', 'Analytical Thinker'),
            'patience': ('wisdom', 'Wise Mentor'),
            'intensity': ('motivation', 'Motivational Coach'),
        }
        
        # Try to get relevant characters from trait system
        try:
            situation = character_trait_system.analyze_situation(message)
            best = character_trait_system.find_best_character_for_situation(message)
            
            if best and best.get('character'):
                char = best['character']
                dominant = char.traits.get_dominant_traits(3)
                
                lenses = []
                seen = set()
                for trait_name, _ in dominant:
                    mapping = TRAIT_TO_LENS.get(trait_name)
                    if mapping and mapping[0] not in seen:
                        lenses.append(mapping)
                        seen.add(mapping[0])
                
                # Ensure diversity - add contrasting lenses
                all_lenses = [
                    ('stoicism', 'Stoic Advisor'), ('empathy', 'Empathetic Guide'),
                    ('analytical', 'Analytical Thinker'), ('motivation', 'Motivational Coach'),
                    ('wisdom', 'Wise Mentor'), ('pragmatism', 'Practical Advisor')
                ]
                for lens in all_lenses:
                    if lens[0] not in seen and len(lenses) < 3:
                        lenses.append(lens)
                        seen.add(lens[0])
                
                return lenses
        except Exception:
            pass
        
        # Fallback: return default diverse set
        return [
            ('empathy', 'Empathetic Guide'),
            ('pragmatism', 'Practical Advisor'),
            ('wisdom', 'Wise Mentor')
        ]
    
    def format_perspective_clarification(
        self, 
        standard_questions: List[ClarificationQuestion],
        perspective_questions: List[Dict],
        user_language: Dict = None
    ) -> str:
        """
        Format multi-perspective clarification for appending to response.
        Character names are NOT shown to the user — only the questions.
        """
        if not standard_questions and not perspective_questions:
            return ""
        
        is_brief = user_language and user_language.get('preferred_length') in ('brief', 'very_brief')
        parts = []
        
        if perspective_questions:
            if is_brief:
                parts.append("\n\nA few things that might help:")
            else:
                parts.append("\n\nTo help me understand your situation better, consider these questions:")
            
            for i, pq in enumerate(perspective_questions[:3], 1):
                parts.append(f"\n{i}. {pq['question']}")
        elif standard_questions:
            # Fall back to standard format
            return self.format_clarification_for_response(standard_questions, user_language)
        
        return "".join(parts)
    
    def get_clarification_stats(self, user_id: int = None) -> Dict:
        """Get clarification system statistics"""
        cursor = self.db.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT COUNT(*) FROM clarification_history WHERE user_id = ?
            ''', (user_id,))
            total = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM clarification_history 
                WHERE user_id = ? AND user_response IS NOT NULL
            ''', (user_id,))
            answered = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM clarification_history 
                WHERE user_id = ? AND was_helpful = 1
            ''', (user_id,))
            helpful = cursor.fetchone()[0]
        else:
            cursor.execute('SELECT COUNT(*) FROM clarification_history')
            total = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM clarification_history 
                WHERE user_response IS NOT NULL
            ''')
            answered = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM clarification_history WHERE was_helpful = 1
            ''')
            helpful = cursor.fetchone()[0]
        
        # Gap distribution
        cursor.execute('''
            SELECT context_gap, COUNT(*) as cnt 
            FROM clarification_history
            GROUP BY context_gap 
            ORDER BY cnt DESC
        ''')
        gap_distribution = {r[0]: r[1] for r in cursor.fetchall()}
        
        # Reason distribution
        cursor.execute('''
            SELECT reason, COUNT(*) as cnt 
            FROM clarification_history
            GROUP BY reason 
            ORDER BY cnt DESC
        ''')
        reason_distribution = {r[0]: r[1] for r in cursor.fetchall()}
        
        return {
            'total_questions_asked': total,
            'answered': answered,
            'helpful': helpful,
            'response_rate': round(answered / max(total, 1), 2),
            'helpfulness_rate': round(helpful / max(answered, 1), 2),
            'gap_distribution': gap_distribution,
            'reason_distribution': reason_distribution
        }


def create_clarification_system(db_connection: sqlite3.Connection) -> ProactiveClarificationSystem:
    """Factory function"""
    return ProactiveClarificationSystem(db_connection)

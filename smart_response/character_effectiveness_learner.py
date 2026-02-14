"""
Phase 7: Character Effectiveness Learner

Automatically tracks how well different characters/approaches work for each user
and situation type. Learns from conversation signals without requiring explicit
user feedback, though explicit feedback is also supported.

Signals tracked:
- Conversation length (engagement depth)
- Message length trends (increasing = engaged, decreasing = disengaged)
- Emotional trajectory (improving sentiment = effective)
- Goal mentions and progress indicators
- User return rate (came back = positive)
- Explicit feedback (thumbs up/down if provided)

Integrates with CharacterTraitSystem.record_outcome() for score updates.
"""

import sqlite3
import json
import re
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from enum import Enum


class EngagementLevel(Enum):
    """How engaged the user was in the conversation"""
    VERY_LOW = "very_low"      # 1-2 messages, short
    LOW = "low"                # 3-4 messages, brief
    MODERATE = "moderate"      # 5-8 messages
    HIGH = "high"              # 9-15 messages, detailed
    VERY_HIGH = "very_high"    # 16+ messages, deep


class OutcomeSignal(Enum):
    """Types of outcome signals we detect"""
    ENGAGEMENT_DEPTH = "engagement_depth"
    MESSAGE_LENGTH_TREND = "message_length_trend"
    EMOTIONAL_TRAJECTORY = "emotional_trajectory"
    GOAL_PROGRESS = "goal_progress"
    EXPLICIT_THANKS = "explicit_thanks"
    EXPLICIT_FRUSTRATION = "explicit_frustration"
    RETURN_RATE = "return_rate"
    USER_FEEDBACK = "user_feedback"


@dataclass
class ConversationOutcome:
    """Analyzed outcome of a conversation"""
    session_id: str
    user_id: int
    character_id: str
    message_count: int
    user_message_count: int
    engagement_level: EngagementLevel
    satisfaction_estimate: float  # 0-1 estimated from signals
    goal_achieved: Optional[bool]
    signals: Dict[str, float] = field(default_factory=dict)
    situation_type: str = "general"
    timestamp: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'character_id': self.character_id,
            'message_count': self.message_count,
            'user_message_count': self.user_message_count,
            'engagement_level': self.engagement_level.value,
            'satisfaction_estimate': round(self.satisfaction_estimate, 3),
            'goal_achieved': self.goal_achieved,
            'signals': {k: round(v, 3) for k, v in self.signals.items()},
            'situation_type': self.situation_type,
            'timestamp': self.timestamp
        }


class CharacterEffectivenessLearner:
    """
    Learns which characters work best for which users and situations
    by analyzing conversation outcomes automatically.
    """
    
    # Engagement thresholds
    ENGAGEMENT_THRESHOLDS = {
        EngagementLevel.VERY_LOW: (0, 2),
        EngagementLevel.LOW: (3, 4),
        EngagementLevel.MODERATE: (5, 8),
        EngagementLevel.HIGH: (9, 15),
        EngagementLevel.VERY_HIGH: (16, float('inf'))
    }
    
    # Positive sentiment indicators
    POSITIVE_INDICATORS = [
        r'\bthank(s| you)\b', r'\bhelpful\b', r'\bgreat\b', r'\bgood point\b',
        r'\bthat helps\b', r'\bmakes sense\b', r'\bi agree\b', r'\bexactly\b',
        r'\bperfect\b', r'\bamazing\b', r'\bawesome\b', r'\blovely\b',
        r'\bi see\b', r'\bthat\'s true\b', r'\byou\'re right\b',
        r'\bi feel better\b', r'\bthat resonates\b', r'\binsightful\b'
    ]
    
    # Negative sentiment indicators
    NEGATIVE_INDICATORS = [
        r'\bnot helpful\b', r'\bconfused\b', r'\bdoesn\'t make sense\b',
        r'\bwrong\b', r'\bfrustrat', r'\bnot what i\b', r'\bnevermind\b',
        r'\bforget it\b', r'\bwhatever\b', r'\bno\b.*\bthat\'s not\b',
        r'\byou don\'t understand\b', r'\bmissing the point\b'
    ]
    
    # Goal progress indicators
    GOAL_INDICATORS = [
        r'\bi will\b', r'\bi\'m going to\b', r'\bmy plan is\b',
        r'\bnext step\b', r'\bi\'ll try\b', r'\blet me\b',
        r'\bi decided\b', r'\bi\'ve decided\b', r'\bgoing forward\b',
        r'\bi\'ll do\b', r'\baction item\b', r'\bgoal\b.*\bset\b'
    ]
    
    # Situation type detection keywords
    SITUATION_KEYWORDS = {
        'career': [r'\bjob\b', r'\bcareer\b', r'\bwork\b', r'\bpromot', r'\bresign', r'\bboss\b', r'\bcolleague\b', r'\binterview\b', r'\bresume\b', r'\bsalary\b'],
        'emotional': [r'\bfeel(ing)?\b', r'\bsad\b', r'\banxi', r'\bdepress', r'\bstress', r'\blonely\b', r'\boverwhel', r'\bworr', r'\bafraid\b', r'\bpanic\b'],
        'relationship': [r'\brelationship\b', r'\bpartner\b', r'\bfriend\b', r'\bfamily\b', r'\bmarriage\b', r'\bdivorce\b', r'\bbreakup\b', r'\bparent\b', r'\bchild\b'],
        'health': [r'\bhealth\b', r'\bsick\b', r'\bdoctor\b', r'\bexercise\b', r'\bdiet\b', r'\bsleep\b', r'\bpain\b', r'\bmedic', r'\bmental health\b'],
        'financial': [r'\bmoney\b', r'\bfinance\b', r'\bdebt\b', r'\bbudget\b', r'\bsaving\b', r'\binvest', r'\bexpense\b', r'\bbill\b'],
        'personal_growth': [r'\bgoal\b', r'\bgrow', r'\bimprove\b', r'\blearn\b', r'\bhabit\b', r'\bmotivat', r'\bdiscipline\b', r'\bpurpose\b', r'\bmeaning\b'],
        'decision': [r'\bdecid', r'\bchoose\b', r'\bchoice\b', r'\bdilemma\b', r'\bshould i\b', r'\boption\b', r'\badvice\b'],
    }
    
    def __init__(self, db: sqlite3.Connection, character_trait_system=None):
        self.db = db
        self.character_trait_system = character_trait_system
        self._init_tables()
    
    def _init_tables(self):
        """Create effectiveness learning tables"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                character_id TEXT NOT NULL,
                message_count INTEGER DEFAULT 0,
                user_message_count INTEGER DEFAULT 0,
                engagement_level TEXT,
                satisfaction_estimate REAL,
                goal_achieved BOOLEAN,
                signals_json TEXT,
                situation_type TEXT DEFAULT 'general',
                analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(session_id, character_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                character_id TEXT,
                feedback_type TEXT NOT NULL,
                feedback_value REAL,
                feedback_text TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS effectiveness_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id TEXT NOT NULL,
                effectiveness_score REAL,
                sample_size INTEGER,
                avg_satisfaction REAL,
                avg_engagement REAL,
                goal_rate REAL,
                snapshot_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conv_outcomes_user ON conversation_outcomes(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conv_outcomes_char ON conversation_outcomes(character_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conv_outcomes_session ON conversation_outcomes(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_feedback_session ON user_feedback(session_id)')
        
        self.db.commit()
    
    # ================================================================
    # CONVERSATION ANALYSIS
    # ================================================================
    
    def analyze_conversation(
        self,
        session_id: str,
        user_id: int,
        messages: List[Dict],
        character_id: str = "chatchat",
        situation_type: str = "general"
    ) -> ConversationOutcome:
        """
        Analyze a conversation's messages to determine outcome quality.
        Call this when a conversation ends or after significant exchanges.
        
        messages: list of {sender_type, content, timestamp, metadata}
        """
        if not messages:
            return ConversationOutcome(
                session_id=session_id, user_id=user_id,
                character_id=character_id, message_count=0,
                user_message_count=0,
                engagement_level=EngagementLevel.VERY_LOW,
                satisfaction_estimate=0.5, goal_achieved=None,
                situation_type=situation_type,
                timestamp=datetime.now().isoformat()
            )
        
        user_msgs = [m for m in messages if m.get('sender_type') == 'user']
        ai_msgs = [m for m in messages if m.get('sender_type') == 'assistant']
        
        # Auto-detect situation type if not explicitly provided
        if situation_type == "general":
            situation_type = self.detect_situation_type(messages)
        
        signals = {}
        
        # Signal 1: Engagement depth
        engagement = self._calc_engagement(len(user_msgs))
        signals['engagement_depth'] = self._engagement_to_score(engagement)
        
        # Signal 2: Message length trend (are user messages getting longer/shorter?)
        signals['message_length_trend'] = self._calc_length_trend(user_msgs)
        
        # Signal 3: Emotional trajectory
        signals['emotional_trajectory'] = self._calc_emotional_trajectory(user_msgs)
        
        # Signal 4: Goal progress indicators
        signals['goal_progress'] = self._calc_goal_progress(user_msgs)
        
        # Signal 5: Explicit thanks/positive
        signals['explicit_thanks'] = self._calc_explicit_sentiment(user_msgs, positive=True)
        
        # Signal 6: Explicit frustration/negative
        signals['explicit_frustration'] = self._calc_explicit_sentiment(user_msgs, positive=False)
        
        # Composite satisfaction estimate
        satisfaction = self._calc_satisfaction(signals)
        
        # Goal achieved estimate
        goal_achieved = signals['goal_progress'] > 0.5
        
        outcome = ConversationOutcome(
            session_id=session_id,
            user_id=user_id,
            character_id=character_id,
            message_count=len(messages),
            user_message_count=len(user_msgs),
            engagement_level=engagement,
            satisfaction_estimate=satisfaction,
            goal_achieved=goal_achieved,
            signals=signals,
            situation_type=situation_type,
            timestamp=datetime.now().isoformat()
        )
        
        return outcome
    
    def record_conversation_outcome(self, outcome: ConversationOutcome):
        """Store a conversation outcome and update character effectiveness"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO conversation_outcomes
            (session_id, user_id, character_id, message_count, user_message_count,
             engagement_level, satisfaction_estimate, goal_achieved, signals_json,
             situation_type, analyzed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            outcome.session_id, outcome.user_id, outcome.character_id,
            outcome.message_count, outcome.user_message_count,
            outcome.engagement_level.value, outcome.satisfaction_estimate,
            outcome.goal_achieved, json.dumps(outcome.signals),
            outcome.situation_type
        ))
        
        self.db.commit()
        
        # Also push to CharacterTraitSystem if available
        if self.character_trait_system:
            try:
                situation = self.character_trait_system.analyze_situation(
                    f"Conversation about {outcome.situation_type}"
                )
                self.character_trait_system.record_outcome(
                    outcome.user_id, outcome.character_id, situation,
                    outcome.message_count, outcome.satisfaction_estimate,
                    outcome.goal_achieved
                )
            except Exception as e:
                print(f"⚠️ Could not push outcome to trait system: {e}")
        
        return outcome
    
    def analyze_and_record(
        self,
        session_id: str,
        user_id: int,
        messages: List[Dict],
        character_id: str = "chatchat",
        situation_type: str = "general"
    ) -> ConversationOutcome:
        """Convenience: analyze + record in one call"""
        outcome = self.analyze_conversation(
            session_id, user_id, messages, character_id, situation_type
        )
        self.record_conversation_outcome(outcome)
        return outcome
    
    # ================================================================
    # USER FEEDBACK
    # ================================================================
    
    def record_feedback(
        self,
        session_id: str,
        user_id: int,
        feedback_type: str,  # 'thumbs_up', 'thumbs_down', 'rating', 'text'
        feedback_value: float = None,
        feedback_text: str = None,
        character_id: str = None
    ):
        """Record explicit user feedback on a conversation"""
        cursor = self.db.cursor()
        
        # Normalize feedback value
        if feedback_type == 'thumbs_up':
            feedback_value = 1.0
        elif feedback_type == 'thumbs_down':
            feedback_value = 0.0
        elif feedback_type == 'rating' and feedback_value is not None:
            feedback_value = max(0.0, min(1.0, feedback_value))
        
        cursor.execute('''
            INSERT INTO user_feedback
            (session_id, user_id, character_id, feedback_type, feedback_value, feedback_text)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, user_id, character_id, feedback_type, feedback_value, feedback_text))
        
        self.db.commit()
        
        # Update the conversation outcome with explicit feedback
        self._incorporate_feedback(session_id, feedback_value)
    
    def _incorporate_feedback(self, session_id: str, feedback_value: float):
        """Blend explicit feedback into the conversation outcome"""
        if feedback_value is None:
            return
        
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT satisfaction_estimate, signals_json, character_id
            FROM conversation_outcomes WHERE session_id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        if row:
            old_satisfaction = row[0] or 0.5
            signals = json.loads(row[1]) if row[1] else {}
            character_id = row[2]
            
            # Explicit feedback weighs 40%, auto-detected 60%
            new_satisfaction = old_satisfaction * 0.6 + feedback_value * 0.4
            signals['user_feedback'] = feedback_value
            
            cursor.execute('''
                UPDATE conversation_outcomes
                SET satisfaction_estimate = ?, signals_json = ?, analyzed_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            ''', (new_satisfaction, json.dumps(signals), session_id))
            
            self.db.commit()
            
            # Re-push to trait system
            if self.character_trait_system and character_id:
                self._update_character_effectiveness(character_id)
    
    # ================================================================
    # EFFECTIVENESS SCORING
    # ================================================================
    
    def _update_character_effectiveness(self, character_id: str):
        """Recalculate effectiveness from all recorded outcomes"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT AVG(satisfaction_estimate),
                   AVG(CASE WHEN goal_achieved THEN 1.0 ELSE 0.0 END),
                   AVG(CASE engagement_level
                       WHEN 'very_high' THEN 1.0
                       WHEN 'high' THEN 0.8
                       WHEN 'moderate' THEN 0.6
                       WHEN 'low' THEN 0.3
                       WHEN 'very_low' THEN 0.1
                       ELSE 0.5 END),
                   COUNT(*)
            FROM conversation_outcomes
            WHERE character_id = ?
        ''', (character_id,))
        
        row = cursor.fetchone()
        if not row or row[3] < 3:
            return  # Need at least 3 conversations
        
        avg_satisfaction = row[0] or 0.5
        avg_goal = row[1] or 0.5
        avg_engagement = row[2] or 0.5
        sample_size = row[3]
        
        # Weighted effectiveness: satisfaction 50%, goal 30%, engagement 20%
        effectiveness = (
            avg_satisfaction * 0.5 +
            avg_goal * 0.3 +
            avg_engagement * 0.2
        )
        
        # Update trait system
        if self.character_trait_system:
            self.character_trait_system.update_effectiveness(character_id, effectiveness)
        
        # Store snapshot for trend tracking
        cursor.execute('''
            INSERT INTO effectiveness_snapshots
            (character_id, effectiveness_score, sample_size,
             avg_satisfaction, avg_engagement, goal_rate)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (character_id, effectiveness, sample_size,
              avg_satisfaction, avg_engagement, avg_goal))
        
        self.db.commit()
    
    def get_character_effectiveness(self, character_id: str) -> Dict:
        """Get detailed effectiveness data for a character"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT AVG(satisfaction_estimate), 
                   AVG(CASE WHEN goal_achieved THEN 1.0 ELSE 0.0 END),
                   AVG(message_count), COUNT(*),
                   AVG(CASE engagement_level
                       WHEN 'very_high' THEN 1.0
                       WHEN 'high' THEN 0.8
                       WHEN 'moderate' THEN 0.6
                       WHEN 'low' THEN 0.3
                       WHEN 'very_low' THEN 0.1
                       ELSE 0.5 END)
            FROM conversation_outcomes
            WHERE character_id = ?
        ''', (character_id,))
        
        row = cursor.fetchone()
        if not row or row[3] == 0:
            return {
                'character_id': character_id,
                'total_conversations': 0,
                'effectiveness_score': 0.5,
                'avg_satisfaction': None,
                'avg_engagement': None,
                'goal_rate': None,
                'avg_messages': None,
                'sufficient_data': False
            }
        
        avg_sat = row[0] or 0.5
        goal_rate = row[1] or 0.0
        avg_msgs = row[2] or 0
        total = row[3]
        avg_eng = row[4] or 0.5
        
        effectiveness = avg_sat * 0.5 + goal_rate * 0.3 + avg_eng * 0.2
        
        # Per-situation breakdown
        cursor.execute('''
            SELECT situation_type, COUNT(*), AVG(satisfaction_estimate)
            FROM conversation_outcomes
            WHERE character_id = ?
            GROUP BY situation_type
            ORDER BY COUNT(*) DESC
        ''', (character_id,))
        
        situation_breakdown = {}
        for srow in cursor.fetchall():
            situation_breakdown[srow[0]] = {
                'count': srow[1],
                'avg_satisfaction': round(srow[2] or 0.5, 3)
            }
        
        return {
            'character_id': character_id,
            'total_conversations': total,
            'effectiveness_score': round(effectiveness, 3),
            'avg_satisfaction': round(avg_sat, 3),
            'avg_engagement': round(avg_eng, 3),
            'goal_rate': round(goal_rate, 3),
            'avg_messages': round(avg_msgs, 1),
            'sufficient_data': total >= 3,
            'situation_breakdown': situation_breakdown
        }
    
    # ================================================================
    # ANALYTICS
    # ================================================================
    
    def get_best_characters(self, situation_type: str = None, 
                           user_id: int = None, limit: int = 5) -> List[Dict]:
        """Get best-performing characters, optionally filtered by situation/user"""
        cursor = self.db.cursor()
        
        conditions = []
        params = []
        
        if situation_type:
            conditions.append("situation_type = ?")
            params.append(situation_type)
        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)
        
        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)
        
        cursor.execute(f'''
            SELECT character_id,
                   COUNT(*) as conversations,
                   AVG(satisfaction_estimate) as avg_sat,
                   AVG(CASE WHEN goal_achieved THEN 1.0 ELSE 0.0 END) as goal_rate,
                   AVG(CASE engagement_level
                       WHEN 'very_high' THEN 1.0 WHEN 'high' THEN 0.8
                       WHEN 'moderate' THEN 0.6 WHEN 'low' THEN 0.3
                       WHEN 'very_low' THEN 0.1 ELSE 0.5 END) as avg_eng
            FROM conversation_outcomes
            {where}
            GROUP BY character_id
            HAVING COUNT(*) >= 2
            ORDER BY (AVG(satisfaction_estimate) * 0.5 + 
                     AVG(CASE WHEN goal_achieved THEN 1.0 ELSE 0.0 END) * 0.3 +
                     AVG(CASE engagement_level
                         WHEN 'very_high' THEN 1.0 WHEN 'high' THEN 0.8
                         WHEN 'moderate' THEN 0.6 WHEN 'low' THEN 0.3
                         WHEN 'very_low' THEN 0.1 ELSE 0.5 END) * 0.2) DESC
            LIMIT ?
        ''', params + [limit])
        
        results = []
        for row in cursor.fetchall():
            eff = (row[2] or 0.5) * 0.5 + (row[3] or 0) * 0.3 + (row[4] or 0.5) * 0.2
            results.append({
                'character_id': row[0],
                'conversations': row[1],
                'avg_satisfaction': round(row[2] or 0.5, 3),
                'goal_rate': round(row[3] or 0, 3),
                'avg_engagement': round(row[4] or 0.5, 3),
                'effectiveness': round(eff, 3)
            })
        
        return results
    
    def get_user_engagement_stats(self, user_id: int) -> Dict:
        """Get engagement statistics for a specific user"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT COUNT(*), AVG(satisfaction_estimate), AVG(message_count),
                   AVG(CASE WHEN goal_achieved THEN 1.0 ELSE 0.0 END),
                   SUM(CASE WHEN engagement_level IN ('high', 'very_high') THEN 1 ELSE 0 END),
                   MIN(analyzed_at), MAX(analyzed_at)
            FROM conversation_outcomes
            WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        if not row or row[0] == 0:
            return {
                'user_id': user_id,
                'total_conversations': 0,
                'avg_satisfaction': None,
                'avg_messages': None,
                'goal_rate': None,
                'high_engagement_count': 0,
                'first_tracked': None,
                'last_tracked': None
            }
        
        # Engagement trend (last 7 days vs all time)
        cursor.execute('''
            SELECT AVG(satisfaction_estimate)
            FROM conversation_outcomes
            WHERE user_id = ? AND analyzed_at >= datetime('now', '-7 days')
        ''', (user_id,))
        recent_sat = cursor.fetchone()
        recent_satisfaction = recent_sat[0] if recent_sat and recent_sat[0] else None
        
        return {
            'user_id': user_id,
            'total_conversations': row[0],
            'avg_satisfaction': round(row[1], 3) if row[1] else None,
            'avg_messages': round(row[2], 1) if row[2] else None,
            'goal_rate': round(row[3], 3) if row[3] else None,
            'high_engagement_count': row[4] or 0,
            'first_tracked': row[5],
            'last_tracked': row[6],
            'recent_satisfaction': round(recent_satisfaction, 3) if recent_satisfaction else None,
            'trend': 'improving' if (recent_satisfaction and row[1] and recent_satisfaction > row[1]) else 'stable'
        }
    
    def get_effectiveness_trends(self, character_id: str, days: int = 30) -> List[Dict]:
        """Get effectiveness score trend for a character over time"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT effectiveness_score, sample_size, avg_satisfaction,
                   avg_engagement, goal_rate, snapshot_at
            FROM effectiveness_snapshots
            WHERE character_id = ? AND snapshot_at >= datetime('now', ? || ' days')
            ORDER BY snapshot_at ASC
        ''', (character_id, f'-{days}'))
        
        return [{
            'effectiveness': round(row[0], 3),
            'sample_size': row[1],
            'avg_satisfaction': round(row[2], 3) if row[2] else None,
            'avg_engagement': round(row[3], 3) if row[3] else None,
            'goal_rate': round(row[4], 3) if row[4] else None,
            'date': row[5]
        } for row in cursor.fetchall()]
    
    def get_system_stats(self) -> Dict:
        """Get overall system learning statistics"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT COUNT(*), AVG(satisfaction_estimate),
                   AVG(CASE WHEN goal_achieved THEN 1.0 ELSE 0.0 END),
                   COUNT(DISTINCT user_id), COUNT(DISTINCT character_id),
                   COUNT(DISTINCT situation_type)
            FROM conversation_outcomes
        ''')
        
        row = cursor.fetchone()
        
        # Feedback stats
        cursor.execute('SELECT COUNT(*), AVG(feedback_value) FROM user_feedback WHERE feedback_value IS NOT NULL')
        fb_row = cursor.fetchone()
        
        # Engagement distribution
        cursor.execute('''
            SELECT engagement_level, COUNT(*)
            FROM conversation_outcomes
            GROUP BY engagement_level
        ''')
        eng_dist = {r[0]: r[1] for r in cursor.fetchall()}
        
        return {
            'total_conversations_tracked': row[0] or 0,
            'avg_satisfaction': round(row[1], 3) if row[1] else None,
            'avg_goal_rate': round(row[2], 3) if row[2] else None,
            'unique_users': row[3] or 0,
            'unique_characters': row[4] or 0,
            'unique_situations': row[5] or 0,
            'total_feedback': fb_row[0] or 0,
            'avg_feedback_score': round(fb_row[1], 3) if fb_row[1] else None,
            'engagement_distribution': eng_dist
        }
    
    # ================================================================
    # SIGNAL CALCULATION (PRIVATE)
    # ================================================================
    
    def _calc_engagement(self, user_message_count: int) -> EngagementLevel:
        """Determine engagement level from user message count"""
        for level, (low, high) in self.ENGAGEMENT_THRESHOLDS.items():
            if low <= user_message_count <= high:
                return level
        return EngagementLevel.VERY_LOW
    
    def _engagement_to_score(self, level: EngagementLevel) -> float:
        """Convert engagement level to 0-1 score"""
        mapping = {
            EngagementLevel.VERY_LOW: 0.1,
            EngagementLevel.LOW: 0.3,
            EngagementLevel.MODERATE: 0.6,
            EngagementLevel.HIGH: 0.8,
            EngagementLevel.VERY_HIGH: 1.0
        }
        return mapping.get(level, 0.5)
    
    def _calc_length_trend(self, user_msgs: List[Dict]) -> float:
        """
        Calculate message length trend. Increasing length = more engaged (→ 1.0).
        Decreasing = less engaged (→ 0.0). Stable ≈ 0.5.
        """
        if len(user_msgs) < 2:
            return 0.5
        
        lengths = [len(m.get('content', '')) for m in user_msgs]
        
        # Simple linear trend
        n = len(lengths)
        if n < 2:
            return 0.5
        
        # Weighted recent vs early
        early = sum(lengths[:n//2]) / max(1, n//2)
        late = sum(lengths[n//2:]) / max(1, n - n//2)
        
        if early == 0:
            return 0.5
        
        ratio = late / early
        # Clamp to 0-1: ratio < 0.5 → 0, ratio 1.0 → 0.5, ratio > 1.5 → 1.0
        score = max(0.0, min(1.0, (ratio - 0.5) / 1.0))
        return score
    
    def _calc_emotional_trajectory(self, user_msgs: List[Dict]) -> float:
        """
        Estimate emotional trajectory: improving → 1.0, declining → 0.0.
        Uses simple keyword-based sentiment in first half vs second half.
        """
        if len(user_msgs) < 2:
            return 0.5
        
        n = len(user_msgs)
        first_half = user_msgs[:n//2]
        second_half = user_msgs[n//2:]
        
        first_sentiment = self._sentiment_score(first_half)
        second_sentiment = self._sentiment_score(second_half)
        
        # Improvement = second half more positive than first
        diff = second_sentiment - first_sentiment
        # Map diff from [-1, 1] to [0, 1]
        return max(0.0, min(1.0, 0.5 + diff * 0.5))
    
    def _sentiment_score(self, msgs: List[Dict]) -> float:
        """Simple keyword-based sentiment: -1 to 1"""
        if not msgs:
            return 0.0
        
        pos_count = 0
        neg_count = 0
        total_words = 0
        
        for m in msgs:
            text = m.get('content', '').lower()
            total_words += len(text.split())
            
            for pattern in self.POSITIVE_INDICATORS:
                pos_count += len(re.findall(pattern, text, re.IGNORECASE))
            
            for pattern in self.NEGATIVE_INDICATORS:
                neg_count += len(re.findall(pattern, text, re.IGNORECASE))
        
        if pos_count + neg_count == 0:
            return 0.0
        
        return (pos_count - neg_count) / (pos_count + neg_count)
    
    def _calc_goal_progress(self, user_msgs: List[Dict]) -> float:
        """Detect goal-setting or action-commitment language"""
        if not user_msgs:
            return 0.0
        
        goal_count = 0
        for m in user_msgs:
            text = m.get('content', '').lower()
            for pattern in self.GOAL_INDICATORS:
                if re.search(pattern, text, re.IGNORECASE):
                    goal_count += 1
                    break
        
        # Normalize: 0 goals → 0, 3+ goals → 1.0
        return min(1.0, goal_count / 3.0)
    
    def _calc_explicit_sentiment(self, user_msgs: List[Dict], positive: bool) -> float:
        """Calculate explicit positive or negative sentiment indicators"""
        if not user_msgs:
            return 0.0
        
        patterns = self.POSITIVE_INDICATORS if positive else self.NEGATIVE_INDICATORS
        count = 0
        
        for m in user_msgs:
            text = m.get('content', '').lower()
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    count += 1
                    break
        
        # Normalize: proportion of messages with the sentiment
        return min(1.0, count / max(1, len(user_msgs)))
    
    def _calc_satisfaction(self, signals: Dict[str, float]) -> float:
        """
        Composite satisfaction estimate from all signals.
        Weights: engagement 25%, length_trend 15%, emotion 25%, 
                 goal 15%, thanks 15%, frustration -15%
        """
        weights = {
            'engagement_depth': 0.25,
            'message_length_trend': 0.15,
            'emotional_trajectory': 0.25,
            'goal_progress': 0.15,
            'explicit_thanks': 0.15,
        }
        
        score = sum(signals.get(k, 0.5) * w for k, w in weights.items())
        
        # Subtract frustration penalty
        frustration = signals.get('explicit_frustration', 0.0)
        score -= frustration * 0.15
        
        return max(0.0, min(1.0, score))


    def detect_situation_type(self, messages: List[Dict]) -> str:
        """Auto-detect the situation type from conversation content"""
        all_text = ' '.join(
            m.get('content', '').lower() for m in messages if m.get('sender_type') == 'user'
        )
        
        if not all_text.strip():
            return 'general'
        
        scores = {}
        for situation, patterns in self.SITUATION_KEYWORDS.items():
            count = 0
            for pattern in patterns:
                count += len(re.findall(pattern, all_text, re.IGNORECASE))
            scores[situation] = count
        
        if not scores or max(scores.values()) == 0:
            return 'general'
        
        return max(scores, key=scores.get)


def create_effectiveness_learner(db: sqlite3.Connection, character_trait_system=None):
    """Factory function to create the effectiveness learner"""
    return CharacterEffectivenessLearner(db, character_trait_system)

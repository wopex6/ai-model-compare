"""
User Context Manager

Manages user preferences, goals, language patterns, and conversation summaries.
Implements both rule-based extraction (every message) and AI summarization (throttled).

Key principles:
1. Learn user's language - capture their phrases and communication style
2. Success = helpfulness + engagement - track what works
3. Adaptive context - different users, different signals
"""

import re
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum


class ContextPriority(Enum):
    """Priority levels for extracted context"""
    CRITICAL = "critical"    # Explicit user statements ("I prefer...", "Don't...")
    HIGH = "high"            # Strong signals (emotions, goals)
    NORMAL = "normal"        # Inferred patterns
    LOW = "low"              # Weak signals, tentative


@dataclass
class ExtractedFact:
    """A fact extracted from user message"""
    fact_type: str           # preference, goal, emotion, fact, language_pattern
    content: str             # The actual content
    priority: ContextPriority
    confidence: float        # 0.0 to 1.0
    source_phrase: str       # Original user phrase that triggered extraction
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    expires_at: Optional[str] = None  # Some facts expire (emotions)


@dataclass
class UserLanguagePattern:
    """Captures how the user communicates"""
    pattern_type: str        # greeting, sign_off, emphasis, question_style, etc.
    user_phrase: str         # What the user actually said
    frequency: int = 1       # How often they use this
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ConversationSummary:
    """Cached conversation summary"""
    character_id: str
    summary: str
    topics: List[str]
    user_goals_mentioned: List[str]
    emotional_arc: str       # e.g., "started anxious, became calmer"
    message_count: int       # Messages covered
    last_message_id: int     # Last message ID included
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_stale: bool = False


class RuleBasedExtractor:
    """
    Extracts structured information from user messages using patterns.
    Runs on EVERY message (cheap, no AI calls).
    """
    
    # Preference patterns - explicit user statements
    PREFERENCE_PATTERNS = [
        # Direct preferences
        (r"(?:please\s+)?(?:call me|my name is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", "name_preference", ContextPriority.CRITICAL),
        (r"(?:i\s+)?prefer\s+(.+?)(?:\.|$|,)", "preference", ContextPriority.CRITICAL),
        (r"(?:please\s+)?(?:keep it|be)\s+(short|brief|concise|detailed|thorough)", "response_length", ContextPriority.CRITICAL),
        (r"(?:i\s+)?(?:don't|do not)\s+(?:like|want)\s+(.+?)(?:\.|$|,)", "dislike", ContextPriority.CRITICAL),
        (r"(?:i\s+)?(?:like|love|enjoy)\s+(?:when you|it when you)\s+(.+?)(?:\.|$|,)", "like", ContextPriority.HIGH),
        (r"(?:can you|please)\s+(?:always|never)\s+(.+?)(?:\.|$|\?)", "instruction", ContextPriority.CRITICAL),
    ]
    
    # Goal patterns
    GOAL_PATTERNS = [
        (r"(?:my\s+)?goal\s+is\s+(?:to\s+)?(.+?)(?:\.|$|,)", "explicit_goal", ContextPriority.CRITICAL),
        (r"i(?:'m| am)\s+(?:trying|working|hoping)\s+to\s+(.+?)(?:\.|$|,)", "active_goal", ContextPriority.HIGH),
        (r"i\s+(?:want|need)\s+to\s+(.+?)(?:\.|$|,)", "desire", ContextPriority.HIGH),
        (r"i(?:'m| am)\s+(?:planning|going)\s+to\s+(.+?)(?:\.|$|,)", "plan", ContextPriority.HIGH),
        (r"(?:help me|i need help)\s+(?:to\s+|with\s+)?(.+?)(?:\.|$|\?)", "help_request", ContextPriority.HIGH),
    ]
    
    # Emotion/state patterns
    EMOTION_PATTERNS = [
        (r"i(?:'m| am|'ve been| have been)\s+(?:feeling\s+)?(stressed|anxious|worried|overwhelmed|burnt out|exhausted)", "negative_state", ContextPriority.HIGH),
        (r"i(?:'m| am|'ve been| have been)\s+(?:feeling\s+)?(happy|excited|motivated|hopeful|great|good|better)", "positive_state", ContextPriority.HIGH),
        (r"i(?:'m| am)\s+(?:so\s+)?(frustrated|angry|upset|disappointed|sad|confused)", "emotional_state", ContextPriority.HIGH),
        (r"(?:this is|it's)\s+(?:really\s+)?(hard|difficult|challenging|tough|easy|simple)", "situation_assessment", ContextPriority.NORMAL),
    ]
    
    # Fact patterns - things user states about themselves
    FACT_PATTERNS = [
        (r"i\s+(?:work|am working)\s+(?:as|in|at)\s+(.+?)(?:\.|$|,)", "occupation", ContextPriority.HIGH),
        (r"i\s+(?:have|got)\s+(\d+)\s+(kid|child|children|dog|cat|pet)", "family_info", ContextPriority.NORMAL),
        (r"i(?:'m| am)\s+(\d+)\s+(?:years old|yo)", "age", ContextPriority.NORMAL),
        (r"i\s+live\s+in\s+(.+?)(?:\.|$|,)", "location", ContextPriority.NORMAL),
        (r"my\s+(?:partner|wife|husband|spouse)\s+(.+?)(?:\.|$|,)", "relationship_info", ContextPriority.NORMAL),
    ]
    
    # Reference patterns - user referring to past conversation
    REFERENCE_PATTERNS = [
        r"(?:as|like)\s+(?:i|we)\s+(?:said|mentioned|discussed|talked about)\s+(?:earlier|before|previously)",
        r"(?:remember|recall)\s+(?:when|what)\s+(?:i|we)",
        r"(?:about|regarding)\s+(?:the|that)\s+(?:plan|thing|issue|topic)\s+(?:we|i)\s+(?:discussed|mentioned)",
        r"(?:going back to|returning to)\s+(?:what|the)",
        r"(?:you said|you mentioned)\s+(?:earlier|before|that)",
    ]
    
    # Language style patterns - how user communicates
    GREETING_PATTERNS = [
        r"^(hey|hi|hello|good morning|good afternoon|good evening|g'day|howdy|yo)[\s,!.]*",
    ]
    
    SIGN_OFF_PATTERNS = [
        r"(thanks|thank you|cheers|bye|goodbye|ttyl|talk soon|appreciate it|much appreciated)[\s,!.]*$",
    ]
    
    EMPHASIS_PATTERNS = [
        r"(really|very|super|extremely|absolutely|definitely|totally)",
    ]
    
    def extract_all(self, message: str) -> Dict[str, List[ExtractedFact]]:
        """Extract all structured information from a message"""
        message_lower = message.lower()
        
        results = {
            'preferences': [],
            'goals': [],
            'emotions': [],
            'facts': [],
            'references_past': False,
            'language_patterns': []
        }
        
        # Extract preferences
        for pattern, pref_type, priority in self.PREFERENCE_PATTERNS:
            matches = re.finditer(pattern, message_lower, re.IGNORECASE)
            for match in matches:
                results['preferences'].append(ExtractedFact(
                    fact_type=pref_type,
                    content=match.group(1).strip() if match.groups() else match.group(0),
                    priority=priority,
                    confidence=0.9,
                    source_phrase=match.group(0)
                ))
        
        # Extract goals
        for pattern, goal_type, priority in self.GOAL_PATTERNS:
            matches = re.finditer(pattern, message_lower, re.IGNORECASE)
            for match in matches:
                results['goals'].append(ExtractedFact(
                    fact_type=goal_type,
                    content=match.group(1).strip() if match.groups() else match.group(0),
                    priority=priority,
                    confidence=0.85,
                    source_phrase=match.group(0)
                ))
        
        # Extract emotions (with expiry - emotions are temporary)
        for pattern, emotion_type, priority in self.EMOTION_PATTERNS:
            matches = re.finditer(pattern, message_lower, re.IGNORECASE)
            for match in matches:
                # Emotions expire after 24 hours
                expires = (datetime.now() + timedelta(hours=24)).isoformat()
                results['emotions'].append(ExtractedFact(
                    fact_type=emotion_type,
                    content=match.group(1).strip() if match.groups() else match.group(0),
                    priority=priority,
                    confidence=0.9,
                    source_phrase=match.group(0),
                    expires_at=expires
                ))
        
        # Extract facts
        for pattern, fact_type, priority in self.FACT_PATTERNS:
            matches = re.finditer(pattern, message_lower, re.IGNORECASE)
            for match in matches:
                results['facts'].append(ExtractedFact(
                    fact_type=fact_type,
                    content=match.group(1).strip() if match.groups() else match.group(0),
                    priority=priority,
                    confidence=0.8,
                    source_phrase=match.group(0)
                ))
        
        # Check if user references past conversation
        for pattern in self.REFERENCE_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                results['references_past'] = True
                break
        
        # Extract language patterns
        results['language_patterns'] = self._extract_language_patterns(message)
        
        return results
    
    def _extract_language_patterns(self, message: str) -> List[UserLanguagePattern]:
        """Extract how the user communicates"""
        patterns = []
        
        # Greetings
        for pattern in self.GREETING_PATTERNS:
            match = re.match(pattern, message, re.IGNORECASE)
            if match:
                patterns.append(UserLanguagePattern(
                    pattern_type="greeting",
                    user_phrase=match.group(1)
                ))
        
        # Sign-offs
        for pattern in self.SIGN_OFF_PATTERNS:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                patterns.append(UserLanguagePattern(
                    pattern_type="sign_off",
                    user_phrase=match.group(1)
                ))
        
        # Emphasis words (track frequency)
        for pattern in self.EMPHASIS_PATTERNS:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                patterns.append(UserLanguagePattern(
                    pattern_type="emphasis",
                    user_phrase=match.lower()
                ))
        
        # Question style
        if message.strip().endswith('?'):
            if message.lower().startswith(('what', 'how', 'why', 'when', 'where', 'who')):
                patterns.append(UserLanguagePattern(
                    pattern_type="question_style",
                    user_phrase="open_ended"
                ))
            elif message.lower().startswith(('is', 'are', 'do', 'does', 'can', 'could', 'would', 'should')):
                patterns.append(UserLanguagePattern(
                    pattern_type="question_style",
                    user_phrase="yes_no"
                ))
        
        # Message length preference
        word_count = len(message.split())
        if word_count <= 5:
            patterns.append(UserLanguagePattern(
                pattern_type="message_length",
                user_phrase="very_brief"
            ))
        elif word_count <= 15:
            patterns.append(UserLanguagePattern(
                pattern_type="message_length",
                user_phrase="brief"
            ))
        elif word_count <= 50:
            patterns.append(UserLanguagePattern(
                pattern_type="message_length",
                user_phrase="moderate"
            ))
        else:
            patterns.append(UserLanguagePattern(
                pattern_type="message_length",
                user_phrase="detailed"
            ))
        
        return patterns


class UserContextManager:
    """
    Manages all user context: preferences, goals, language patterns, and summaries.
    Combines rule-based extraction (every message) with AI summarization (throttled).
    """
    
    # Throttling configuration
    SUMMARY_EVERY_N_MESSAGES = 8
    SUMMARY_MAX_AGE_HOURS = 24
    PROFILE_REFRESH_MESSAGES = 50
    PROFILE_MAX_AGE_DAYS = 7
    
    def __init__(self, db_connection: sqlite3.Connection, ai_client=None):
        self.db = db_connection
        self.ai_client = ai_client
        self.extractor = RuleBasedExtractor()
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create necessary database tables"""
        cursor = self.db.cursor()
        
        # User preferences and facts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                fact_type TEXT NOT NULL,
                content TEXT NOT NULL,
                priority TEXT DEFAULT 'normal',
                confidence REAL DEFAULT 0.8,
                source_phrase TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                is_active INTEGER DEFAULT 1,
                UNIQUE(user_id, fact_type, content)
            )
        ''')
        
        # User language patterns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_language_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                pattern_type TEXT NOT NULL,
                user_phrase TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, pattern_type, user_phrase)
            )
        ''')
        
        # Conversation summaries (cached)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                topics TEXT,
                goals_mentioned TEXT,
                emotional_arc TEXT,
                message_count INTEGER,
                last_message_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_stale INTEGER DEFAULT 0,
                UNIQUE(user_id, character_id)
            )
        ''')
        
        # User engagement metrics (for learning what works)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_engagement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character_id TEXT NOT NULL,
                session_date DATE DEFAULT CURRENT_DATE,
                message_count INTEGER DEFAULT 0,
                avg_response_length REAL,
                positive_signals INTEGER DEFAULT 0,
                negative_signals INTEGER DEFAULT 0,
                topics_discussed TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, character_id, session_date)
            )
        ''')
        
        # Indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_context_user ON user_context(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_context_active ON user_context(user_id, is_active)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_language_user ON user_language_patterns(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conv_summary_user ON conversation_summaries(user_id, character_id)')
        
        self.db.commit()
    
    def process_message(self, user_id: int, message: str, character_id: str,
                       message_id: int = None) -> Dict[str, Any]:
        """
        Process a user message: extract context, update patterns, check if summary needed.
        Returns context to be passed to AI.
        """
        # 1. Rule-based extraction (always runs)
        extracted = self.extractor.extract_all(message)
        
        # 2. Store extracted facts
        self._store_extracted_facts(user_id, extracted)
        
        # 3. Update language patterns
        self._update_language_patterns(user_id, extracted['language_patterns'])
        
        # 4. Update engagement metrics
        self._update_engagement(user_id, character_id, message, extracted)
        
        # 5. Check if summary refresh needed
        needs_summary_refresh = self._needs_summary_refresh(
            user_id, character_id, message_id, extracted['references_past']
        )
        
        # 6. Build context for AI
        context = self._build_ai_context(user_id, character_id)
        context['needs_summary_refresh'] = needs_summary_refresh
        context['references_past'] = extracted['references_past']
        
        return context
    
    def _store_extracted_facts(self, user_id: int, extracted: Dict):
        """Store extracted preferences, goals, emotions, facts"""
        cursor = self.db.cursor()
        
        all_facts = (
            extracted['preferences'] +
            extracted['goals'] +
            extracted['emotions'] +
            extracted['facts']
        )
        
        for fact in all_facts:
            try:
                # Upsert: update if exists, insert if new
                cursor.execute('''
                    INSERT INTO user_context 
                    (user_id, fact_type, content, priority, confidence, source_phrase, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, fact_type, content) DO UPDATE SET
                        confidence = MAX(confidence, excluded.confidence),
                        updated_at = CURRENT_TIMESTAMP,
                        is_active = 1
                ''', (
                    user_id, fact.fact_type, fact.content,
                    fact.priority.value, fact.confidence,
                    fact.source_phrase, fact.expires_at
                ))
            except Exception as e:
                print(f"Warning: Could not store fact: {e}")
        
        self.db.commit()
    
    def _update_language_patterns(self, user_id: int, patterns: List[UserLanguagePattern]):
        """Update user's language patterns with frequency tracking"""
        cursor = self.db.cursor()
        
        for pattern in patterns:
            try:
                cursor.execute('''
                    INSERT INTO user_language_patterns
                    (user_id, pattern_type, user_phrase, frequency)
                    VALUES (?, ?, ?, 1)
                    ON CONFLICT(user_id, pattern_type, user_phrase) DO UPDATE SET
                        frequency = frequency + 1,
                        last_seen = CURRENT_TIMESTAMP
                ''', (user_id, pattern.pattern_type, pattern.user_phrase))
            except Exception as e:
                print(f"Warning: Could not update language pattern: {e}")
        
        self.db.commit()
    
    def _update_engagement(self, user_id: int, character_id: str, 
                          message: str, extracted: Dict):
        """Track engagement metrics for learning what works"""
        cursor = self.db.cursor()
        
        # Determine positive/negative signals
        positive = 1 if any(e.fact_type == 'positive_state' for e in extracted['emotions']) else 0
        negative = 1 if any(e.fact_type in ('negative_state', 'emotional_state') for e in extracted['emotions']) else 0
        
        # Check for explicit positive feedback
        feedback_patterns = [
            r"(?:that's|this is)\s+(?:really\s+)?(?:helpful|useful|great|perfect)",
            r"thanks,?\s+(?:that|this)\s+(?:helps|worked|makes sense)",
            r"(?:exactly|yes|right)\s+(?:what i|that's what)",
        ]
        for pattern in feedback_patterns:
            if re.search(pattern, message.lower()):
                positive += 1
                break
        
        try:
            cursor.execute('''
                INSERT INTO user_engagement
                (user_id, character_id, message_count, positive_signals, negative_signals)
                VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(user_id, character_id, session_date) DO UPDATE SET
                    message_count = message_count + 1,
                    positive_signals = positive_signals + excluded.positive_signals,
                    negative_signals = negative_signals + excluded.negative_signals
            ''', (user_id, character_id, positive, negative))
            self.db.commit()
        except Exception as e:
            print(f"Warning: Could not update engagement: {e}")
    
    def _needs_summary_refresh(self, user_id: int, character_id: str,
                               message_id: int, references_past: bool) -> bool:
        """Determine if conversation summary needs refresh"""
        cursor = self.db.cursor()
        
        # Force refresh if user references past conversation
        if references_past:
            return True
        
        # Check existing summary
        cursor.execute('''
            SELECT message_count, last_message_id, created_at, is_stale
            FROM conversation_summaries
            WHERE user_id = ? AND character_id = ?
        ''', (user_id, character_id))
        
        row = cursor.fetchone()
        
        if not row:
            # No summary exists - need to create if we have enough messages
            cursor.execute('''
                SELECT COUNT(*) FROM history_primary
                WHERE user_id = ? AND character = ?
            ''', (user_id, character_id))
            msg_count = cursor.fetchone()[0]
            return msg_count >= self.SUMMARY_EVERY_N_MESSAGES
        
        msg_count, last_msg_id, created_at, is_stale = row
        
        # Check if stale
        if is_stale:
            return True
        
        # Check age
        if created_at:
            created = datetime.fromisoformat(created_at)
            if datetime.now() - created > timedelta(hours=self.SUMMARY_MAX_AGE_HOURS):
                return True
        
        # Check message count since last summary
        if message_id and last_msg_id:
            if message_id - last_msg_id >= self.SUMMARY_EVERY_N_MESSAGES:
                return True
        
        return False
    
    def _build_ai_context(self, user_id: int, character_id: str) -> Dict[str, Any]:
        """Build the context object to pass to AI"""
        cursor = self.db.cursor()
        context = {}
        
        # Get active preferences (non-expired, high confidence)
        cursor.execute('''
            SELECT fact_type, content, priority, confidence, source_phrase
            FROM user_context
            WHERE user_id = ? AND is_active = 1
              AND (expires_at IS NULL OR expires_at > datetime('now'))
            ORDER BY 
                CASE priority 
                    WHEN 'critical' THEN 1 
                    WHEN 'high' THEN 2 
                    WHEN 'normal' THEN 3 
                    ELSE 4 
                END,
                confidence DESC
            LIMIT 20
        ''', (user_id,))
        
        facts = cursor.fetchall()
        if facts:
            context['user_facts'] = [
                {'type': f[0], 'content': f[1], 'priority': f[2]}
                for f in facts
            ]
        
        # Get top language patterns (communication style)
        cursor.execute('''
            SELECT pattern_type, user_phrase, frequency
            FROM user_language_patterns
            WHERE user_id = ?
            ORDER BY frequency DESC
            LIMIT 10
        ''', (user_id,))
        
        patterns = cursor.fetchall()
        if patterns:
            context['user_language'] = {
                'greeting': next((p[1] for p in patterns if p[0] == 'greeting'), None),
                'sign_off': next((p[1] for p in patterns if p[0] == 'sign_off'), None),
                'preferred_length': next((p[1] for p in patterns if p[0] == 'message_length'), 'moderate'),
                'emphasis_words': [p[1] for p in patterns if p[0] == 'emphasis'][:3],
            }
        
        # Get conversation summary if exists
        cursor.execute('''
            SELECT summary, topics, goals_mentioned, emotional_arc
            FROM conversation_summaries
            WHERE user_id = ? AND character_id = ? AND is_stale = 0
        ''', (user_id, character_id))
        
        summary_row = cursor.fetchone()
        if summary_row:
            context['conversation_summary'] = summary_row[0]
            if summary_row[1]:
                context['recent_topics'] = json.loads(summary_row[1])
            if summary_row[2]:
                context['user_goals'] = json.loads(summary_row[2])
        
        return context
    
    def generate_summary(self, user_id: int, character_id: str,
                        recent_messages: List[Dict], message_id: int = None) -> Optional[str]:
        """
        Generate/refresh conversation summary using AI.
        Called only when throttling allows (not every message).
        """
        if not self.ai_client or not recent_messages:
            return None
        
        # Build conversation text
        conv_text = "\n".join([
            f"User: {m.get('user_message', '')}\nAssistant: {m.get('assistant_response', '')}"
            for m in recent_messages[-15:]  # Last 15 exchanges max
        ])
        
        summary_prompt = f"""Analyze this conversation and provide a brief summary (2-3 sentences max).
Focus on:
1. Main topics discussed
2. User's goals or concerns
3. Emotional trajectory (how user's mood changed)

Conversation:
{conv_text}

Respond in JSON format:
{{"summary": "...", "topics": ["topic1", "topic2"], "goals": ["goal1"], "emotional_arc": "brief description"}}"""

        try:
            # Use the AI client to generate summary
            response = self._call_ai_for_summary(summary_prompt)
            if response:
                # Parse and store
                try:
                    data = json.loads(response)
                    self._store_summary(
                        user_id, character_id,
                        data.get('summary', ''),
                        data.get('topics', []),
                        data.get('goals', []),
                        data.get('emotional_arc', ''),
                        len(recent_messages),
                        message_id
                    )
                    return data.get('summary')
                except json.JSONDecodeError:
                    # Store as plain text if not JSON
                    self._store_summary(
                        user_id, character_id, response,
                        [], [], '', len(recent_messages), message_id
                    )
                    return response
        except Exception as e:
            print(f"Warning: Could not generate summary: {e}")
        
        return None
    
    def _call_ai_for_summary(self, prompt: str) -> Optional[str]:
        """Call AI to generate summary using OpenAI (with budget control)"""
        # Try to use OpenAI for summarization
        try:
            from openai import OpenAI
            import os
            
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                print("[SUMMARY] No OpenAI API key available")
                return None
            
            # Check budget if ai_client has budget manager
            if self.ai_client and hasattr(self.ai_client, 'can_make_call'):
                if not self.ai_client.can_make_call():
                    print("[SUMMARY] AI budget exhausted, skipping summary")
                    return None
            
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes conversations concisely. Always respond in valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            
            # Log token usage
            if hasattr(response, 'usage') and response.usage:
                print(f"[SUMMARY] Tokens: {response.usage.prompt_tokens} in, {response.usage.completion_tokens} out")
            
            # Record in budget if available
            if self.ai_client and hasattr(self.ai_client, 'record_call'):
                self.ai_client.record_call(
                    purpose='conversation_summary',
                    success=True,
                    is_background=True
                )
            
            return result
            
        except Exception as e:
            print(f"[SUMMARY] AI call failed: {e}")
            return None
    
    def _store_summary(self, user_id: int, character_id: str, summary: str,
                      topics: List[str], goals: List[str], emotional_arc: str,
                      message_count: int, last_message_id: int):
        """Store conversation summary"""
        cursor = self.db.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO conversation_summaries
                (user_id, character_id, summary, topics, goals_mentioned, 
                 emotional_arc, message_count, last_message_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, character_id) DO UPDATE SET
                    summary = excluded.summary,
                    topics = excluded.topics,
                    goals_mentioned = excluded.goals_mentioned,
                    emotional_arc = excluded.emotional_arc,
                    message_count = excluded.message_count,
                    last_message_id = excluded.last_message_id,
                    created_at = CURRENT_TIMESTAMP,
                    is_stale = 0
            ''', (
                user_id, character_id, summary,
                json.dumps(topics), json.dumps(goals),
                emotional_arc, message_count, last_message_id
            ))
            self.db.commit()
        except Exception as e:
            print(f"Warning: Could not store summary: {e}")
    
    def get_user_greeting(self, user_id: int) -> Optional[str]:
        """Get user's preferred greeting style"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT user_phrase FROM user_language_patterns
            WHERE user_id = ? AND pattern_type = 'greeting'
            ORDER BY frequency DESC LIMIT 1
        ''', (user_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    
    def get_user_name(self, user_id: int) -> Optional[str]:
        """Get user's preferred name"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT content FROM user_context
            WHERE user_id = ? AND fact_type = 'name_preference' AND is_active = 1
            ORDER BY updated_at DESC LIMIT 1
        ''', (user_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    
    def format_context_for_prompt(self, context: Dict) -> str:
        """Format user context into a string for the system prompt"""
        parts = []
        
        # User facts
        if context.get('user_facts'):
            critical_facts = [f for f in context['user_facts'] if f['priority'] == 'critical']
            if critical_facts:
                parts.append("User preferences (important):")
                for f in critical_facts[:5]:
                    parts.append(f"- {f['type']}: {f['content']}")
        
        # User's communication style
        if context.get('user_language'):
            lang = context['user_language']
            style_parts = []
            if lang.get('greeting'):
                style_parts.append(f"greets with '{lang['greeting']}'")
            if lang.get('preferred_length') == 'brief' or lang.get('preferred_length') == 'very_brief':
                style_parts.append("prefers brief responses")
            elif lang.get('preferred_length') == 'detailed':
                style_parts.append("appreciates detailed responses")
            if style_parts:
                parts.append(f"User style: {', '.join(style_parts)}")
        
        # Conversation summary
        if context.get('conversation_summary'):
            parts.append(f"Recent context: {context['conversation_summary']}")
        
        # Active goals
        if context.get('user_goals'):
            parts.append(f"User's goals: {', '.join(context['user_goals'][:3])}")
        
        return "\n".join(parts) if parts else ""


def create_user_context_manager(db_connection: sqlite3.Connection, 
                                ai_client=None) -> UserContextManager:
    """Factory function to create UserContextManager"""
    return UserContextManager(db_connection, ai_client)

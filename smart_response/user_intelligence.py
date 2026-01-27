"""
User Intelligence System
========================

Inspired by social media recommendation engines (Instagram, YouTube, Facebook, TikTok),
this system learns user preferences through behavioral signals to provide highly
personalized and predictive experiences.

================================================================================
LIMITATIONS: CONVERSATION-ONLY VS RICH MEDIA
================================================================================

SOCIAL MEDIA HAS:                    THIS APP HAS:
─────────────────────────────────    ─────────────────────────────────
Videos (watch time, completion)      Text conversations only
Images (dwell time, zoom, save)      No visual content (yet)
Audio (listen time, skip rate)       No audio content (yet)
Scroll behavior                      Message-by-message interaction
Double-tap / swipe gestures          Click-based only
Ads engagement                       No ads (thankfully)
Passive consumption                  Active participation required

WHAT WE CAN'T MEASURE (YET):         WHAT WE CAN MEASURE INSTEAD:
─────────────────────────────────    ─────────────────────────────────
Watch time on video                  → Conversation duration
Video completion rate                → Topic resolution rate
Image dwell time                     → Message read-to-reply time
Scroll speed                         → Topic switching frequency
Pause/rewind behavior                → Return to previous topics
Visual attention                     → Emotional depth in text

================================================================================
CONVERSATION-SPECIFIC ADVANTAGES (Our Unique Signals)
================================================================================

1. EMOTIONAL JOURNEY - Track sentiment changes through conversation
   - Starting emotional state → ending emotional state
   - Emotional volatility vs stability
   - Resolution indicators ("that helps", "I feel better")

2. CONVERSATION DEPTH - Unlike passive video watching
   - Back-and-forth exchanges (dialogue depth)
   - Question complexity progression
   - Topic drilling vs topic hopping

3. NEED RESOLUTION - Did we actually help?
   - Explicit gratitude signals
   - Implicit resolution (session ended positively)
   - Return rate on same topic (unresolved = they come back)

4. ACTIVE ENGAGEMENT - Users invest effort
   - Message length = effort invested (unlike passive video watching)
   - Thoughtfulness indicators (detailed questions)
   - Follow-up questions = genuine interest

================================================================================
FUTURE EXTENSIBILITY: MEDIA TYPE ABSTRACTION
================================================================================

Designed for when videos/images/audio are added:

MEDIA_TYPE_HANDLERS = {
    'conversation': ConversationEngagementHandler,  # Current
    'video': VideoEngagementHandler,                # Future
    'image': ImageEngagementHandler,                # Future  
    'audio': AudioEngagementHandler,                # Future
    'document': DocumentEngagementHandler,          # Future (PDFs, etc.)
}

Each handler implements:
- get_engagement_signals(content_id) → List[Signal]
- calculate_engagement_score(signals) → float
- get_completion_rate(content_id) → float
- get_quality_indicators(content_id) → Dict

================================================================================
KEY LEARNINGS FROM SOCIAL MEDIA PLATFORMS
================================================================================

1. YOUTUBE - Watch Time & Engagement Depth
   - Tracks not just clicks, but HOW LONG users engage
   - Distinguishes between "tried and bounced" vs "deeply engaged"
   - Uses completion rate as quality signal
   → OUR EQUIVALENT: Conversation duration, topic completion

2. INSTAGRAM - Interaction Hierarchy
   - Weights actions: Save > Comment > Like > View
   - Tracks time spent on each post
   - Notes what users RETURN to view again
   → OUR EQUIVALENT: Highlight > Feedback > Suggestion click > Message

3. FACEBOOK - Social & Temporal Patterns
   - When users are active (time-of-day, day-of-week)
   - What contexts trigger engagement
   - Recency vs frequency balance
   → OUR EQUIVALENT: Peak conversation times, topic triggers

4. TIKTOK - Real-time Adaptation
   - Extremely fast feedback loops
   - "Explore vs Exploit" balance
   - Negative signals matter (skip, not interested)
   → OUR EQUIVALENT: Real-time tone adaptation, skipped suggestions

5. SPOTIFY - Collaborative Filtering
   - "Users like you also liked..."
   - Context-aware (workout, sleep, focus)
   - Taste profiles that evolve
   → OUR EQUIVALENT: Similar users' character preferences, mood-based routing

================================================================================
INNOVATIONS FOR AI COMPANION
================================================================================
- Emotional journey tracking (not just topics)
- Need fulfillment scoring (was the user actually helped?)
- Communication style matching (formal/casual, verbose/concise)
- Proactive outreach timing (optimal contact windows)
- Character-user chemistry scoring (which advisor works best)
- Conversation depth metrics (shallow chat vs deep exploration)
- Resolution rate tracking (did we solve their problem?)
"""

import json
import sqlite3
import math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict

DB_PATH = Path(__file__).parent.parent / 'integrated_users.db'


class UserIntelligenceSystem:
    """
    Comprehensive user understanding system inspired by social media algorithms.
    
    Core Components:
    1. Engagement Tracker - What users do and how deeply
    2. Behavioral Analyzer - Patterns in time, topics, style
    3. Interest Graph - Weighted preferences across dimensions
    4. Prediction Engine - Anticipate needs before they're expressed
    5. Feedback Loop - Continuous learning and adaptation
    """
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self._init_tables()
        
        # =================================================================
        # ENGAGEMENT WEIGHTS BY MEDIA TYPE
        # =================================================================
        # Designed to be extensible for future media types
        
        self.media_type = 'conversation'  # Current media type
        
        # CONVERSATION-SPECIFIC weights (current)
        self.engagement_weights = {
            # === BASIC SIGNALS ===
            'message_sent': 1.0,              # Basic engagement
            'message_received': 0.5,          # Passive (AI responded)
            
            # === EFFORT SIGNALS (conversation-specific) ===
            'long_message': 1.5,              # >100 chars = invested effort
            'very_long_message': 2.0,         # >300 chars = significant effort
            'detailed_question': 2.0,         # Complex question asked
            'follow_up_question': 2.5,        # Continued engagement
            
            # === INTEREST SIGNALS ===
            'suggestion_clicked': 2.0,        # Showed interest in follow-up
            'returned_to_topic': 3.0,         # Came back to same topic
            'topic_deep_dive': 3.5,           # Multiple exchanges on same topic
            
            # === VALUE SIGNALS (highest weight) ===
            'positive_feedback': 4.0,         # Explicit satisfaction
            'resolution_indicated': 4.5,      # "That helps", "I understand now"
            'saved_highlight': 5.0,           # Saved part of conversation
            'shared_content': 5.0,            # Shared advice (future)
            
            # === NEGATIVE SIGNALS ===
            'skipped_suggestion': -0.5,       # Ignored follow-up options
            'quick_exit': -1.0,               # Left quickly without resolution
            'topic_abandoned': -0.5,          # Started topic, never finished
            'negative_feedback': -2.0,        # Explicit dissatisfaction
            
            # === EMOTIONAL JOURNEY SIGNALS ===
            'emotional_improvement': 3.0,     # Sentiment got better
            'emotional_decline': -1.5,        # Sentiment got worse
            'emotional_stability': 1.0,       # Maintained stable state
        }
        
        # FUTURE: Video engagement weights (when videos are added)
        self.video_engagement_weights = {
            'video_started': 1.0,
            'video_25_percent': 1.5,
            'video_50_percent': 2.0,
            'video_75_percent': 2.5,
            'video_completed': 3.0,
            'video_rewatched': 4.0,
            'video_paused_resumed': 1.5,      # Indicates attention
            'video_skipped': -1.0,
            'video_saved': 5.0,
            'video_shared': 5.0,
        }
        
        # FUTURE: Image engagement weights (when images are added)
        self.image_engagement_weights = {
            'image_viewed': 1.0,
            'image_zoomed': 2.0,              # Looked closer
            'image_long_view': 2.5,           # >3 seconds
            'image_saved': 4.0,
            'image_shared': 5.0,
            'image_skipped': -0.5,
        }
        
        # FUTURE: Audio engagement weights (when audio is added)
        self.audio_engagement_weights = {
            'audio_started': 1.0,
            'audio_25_percent': 1.5,
            'audio_completed': 3.0,
            'audio_replayed': 3.5,
            'audio_skipped': -1.0,
            'audio_saved': 4.0,
        }
        
        # Decay factors for recency (Facebook-style)
        self.decay_half_life_days = 14  # Interest halves every 2 weeks
        
    def _init_tables(self):
        """Create comprehensive tracking tables."""
        if not self.db:
            return
            
        try:
            cursor = self.db.cursor()
            
            # ================================================================
            # ENGAGEMENT SIGNALS (YouTube/Instagram inspired)
            # ================================================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_engagement_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    signal_type TEXT NOT NULL,
                    signal_value REAL DEFAULT 1.0,
                    context_data TEXT,
                    character_id TEXT,
                    topic TEXT,
                    session_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Index for fast lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_engagement_user_time 
                ON user_engagement_signals (user_id, timestamp DESC)
            ''')
            
            # ================================================================
            # SESSION TRACKING (Spotify context-aware style)
            # ================================================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_id TEXT NOT NULL UNIQUE,
                    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ended_at DATETIME,
                    duration_seconds INTEGER,
                    message_count INTEGER DEFAULT 0,
                    characters_used TEXT,
                    topics_discussed TEXT,
                    emotional_journey TEXT,
                    satisfaction_score REAL,
                    context_type TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # ================================================================
            # INTEREST GRAPH (TikTok-style weighted preferences)
            # ================================================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_interest_graph (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    interest_type TEXT NOT NULL,
                    interest_key TEXT NOT NULL,
                    score REAL DEFAULT 0.0,
                    interaction_count INTEGER DEFAULT 0,
                    last_interaction DATETIME,
                    trend TEXT DEFAULT 'stable',
                    metadata TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, interest_type, interest_key),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # ================================================================
            # BEHAVIORAL PATTERNS (Facebook temporal patterns)
            # ================================================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_behavioral_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    confidence REAL DEFAULT 0.0,
                    sample_size INTEGER DEFAULT 0,
                    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_validated DATETIME,
                    UNIQUE(user_id, pattern_type),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # ================================================================
            # PREDICTIONS & OUTCOMES (Feedback loop)
            # ================================================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prediction_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    prediction_type TEXT NOT NULL,
                    predicted_value TEXT,
                    actual_value TEXT,
                    was_correct INTEGER,
                    confidence REAL,
                    context TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # ================================================================
            # CHARACTER CHEMISTRY (User-character affinity)
            # ================================================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_character_chemistry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    character_id TEXT NOT NULL,
                    affinity_score REAL DEFAULT 0.5,
                    total_interactions INTEGER DEFAULT 0,
                    positive_outcomes INTEGER DEFAULT 0,
                    avg_session_length REAL,
                    topics_discussed TEXT,
                    last_interaction DATETIME,
                    UNIQUE(user_id, character_id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # ================================================================
            # MEDIA CONTENT (Future-proof for videos/images/audio)
            # ================================================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS media_content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id TEXT NOT NULL UNIQUE,
                    media_type TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    duration_seconds INTEGER,
                    file_path TEXT,
                    url TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ================================================================
            # MEDIA ENGAGEMENT (Future-proof tracking)
            # ================================================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS media_engagement (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    content_id TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    engagement_type TEXT NOT NULL,
                    progress_percent REAL,
                    duration_seconds INTEGER,
                    context_data TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # ================================================================
            # CONVERSATION METRICS (Conversation-specific analytics)
            # ================================================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_id TEXT,
                    character_id TEXT,
                    topic TEXT,
                    start_sentiment REAL,
                    end_sentiment REAL,
                    emotional_journey TEXT,
                    exchange_count INTEGER DEFAULT 0,
                    avg_message_length REAL,
                    topic_depth_score REAL,
                    resolution_score REAL,
                    was_resolved INTEGER,
                    duration_seconds INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            self.db.commit()
            print("✓ User Intelligence System tables initialized")
            
        except Exception as e:
            print(f"Warning: Could not initialize user intelligence tables: {e}")
    
    # =========================================================================
    # 1. ENGAGEMENT SIGNAL TRACKING (YouTube/Instagram style)
    # =========================================================================
    
    def record_engagement(self, user_id: int, signal_type: str, 
                         context: Dict = None, character_id: str = None,
                         topic: str = None, session_id: str = None) -> None:
        """
        Record an engagement signal with appropriate weighting.
        
        Signal Types (weighted by value):
        - message_sent: User sent a message
        - suggestion_clicked: User clicked a follow-up suggestion
        - long_message: Message > 100 chars (effort invested)
        - follow_up_question: User asked a follow-up
        - returned_to_topic: User came back to discuss same topic
        - positive_feedback: Explicit positive reaction
        - saved_highlight: User saved part of conversation
        - skipped_suggestion: User ignored suggestions
        - quick_exit: Short session without resolution
        """
        if not self.db:
            return
            
        try:
            cursor = self.db.cursor()
            weight = self.engagement_weights.get(signal_type, 1.0)
            
            cursor.execute('''
                INSERT INTO user_engagement_signals 
                (user_id, signal_type, signal_value, context_data, character_id, topic, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                signal_type,
                weight,
                json.dumps(context) if context else None,
                character_id,
                topic,
                session_id
            ))
            
            self.db.commit()
            
            # Update interest graph based on this signal
            if topic:
                self._update_interest_score(user_id, 'topic', topic, weight)
            if character_id:
                self._update_interest_score(user_id, 'character', character_id, weight)
                self._update_character_chemistry(user_id, character_id, signal_type)
                
        except Exception as e:
            print(f"Warning: Could not record engagement: {e}")
    
    def get_engagement_summary(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get engagement metrics for a user (YouTube Analytics style)."""
        if not self.db:
            return {}
            
        try:
            cursor = self.db.cursor()
            cutoff = datetime.now() - timedelta(days=days)
            
            # Total engagement score
            cursor.execute('''
                SELECT 
                    SUM(signal_value) as total_engagement,
                    COUNT(*) as total_signals,
                    COUNT(DISTINCT DATE(timestamp)) as active_days
                FROM user_engagement_signals
                WHERE user_id = ? AND timestamp > ?
            ''', (user_id, cutoff.isoformat()))
            
            row = cursor.fetchone()
            
            # Engagement by type
            cursor.execute('''
                SELECT signal_type, SUM(signal_value), COUNT(*)
                FROM user_engagement_signals
                WHERE user_id = ? AND timestamp > ?
                GROUP BY signal_type
            ''', (user_id, cutoff.isoformat()))
            
            by_type = {r[0]: {'score': r[1], 'count': r[2]} for r in cursor.fetchall()}
            
            # Top topics
            cursor.execute('''
                SELECT topic, SUM(signal_value)
                FROM user_engagement_signals
                WHERE user_id = ? AND timestamp > ? AND topic IS NOT NULL
                GROUP BY topic
                ORDER BY SUM(signal_value) DESC
                LIMIT 5
            ''', (user_id, cutoff.isoformat()))
            
            top_topics = [(r[0], r[1]) for r in cursor.fetchall()]
            
            return {
                'total_engagement': row[0] or 0,
                'total_signals': row[1] or 0,
                'active_days': row[2] or 0,
                'engagement_by_type': by_type,
                'top_topics': top_topics,
                'engagement_rate': (row[2] or 0) / days if days > 0 else 0
            }
            
        except Exception as e:
            print(f"Warning: Could not get engagement summary: {e}")
            return {}
    
    # =========================================================================
    # 2. BEHAVIORAL PATTERN ANALYSIS (Facebook style)
    # =========================================================================
    
    def analyze_temporal_patterns(self, user_id: int) -> Dict[str, Any]:
        """
        Analyze when user is most active and receptive.
        Like Facebook's "best time to post" but for proactive outreach.
        """
        if not self.db:
            return {}
            
        try:
            cursor = self.db.cursor()
            
            # Get all engagement timestamps
            cursor.execute('''
                SELECT timestamp, signal_type, signal_value
                FROM user_engagement_signals
                WHERE user_id = ?
                ORDER BY timestamp
            ''', (user_id,))
            
            rows = cursor.fetchall()
            if not rows:
                return {'confidence': 0, 'message': 'Not enough data'}
            
            # Analyze by hour of day
            hour_engagement = defaultdict(float)
            hour_counts = defaultdict(int)
            
            # Analyze by day of week
            day_engagement = defaultdict(float)
            day_counts = defaultdict(int)
            
            for ts_str, signal_type, value in rows:
                try:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    hour = ts.hour
                    day = ts.strftime('%A')
                    
                    hour_engagement[hour] += value
                    hour_counts[hour] += 1
                    day_engagement[day] += value
                    day_counts[day] += 1
                except:
                    continue
            
            # Find peak times
            peak_hours = sorted(hour_engagement.items(), key=lambda x: x[1], reverse=True)[:3]
            peak_days = sorted(day_engagement.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Calculate average session gap (when do they typically return?)
            session_gaps = []
            prev_ts = None
            for ts_str, _, _ in rows:
                try:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    if prev_ts and (ts - prev_ts).total_seconds() > 3600:  # Gap > 1 hour
                        session_gaps.append((ts - prev_ts).total_seconds() / 3600)
                    prev_ts = ts
                except:
                    continue
            
            avg_return_hours = sum(session_gaps) / len(session_gaps) if session_gaps else None
            
            patterns = {
                'peak_hours': [{'hour': h, 'engagement': e} for h, e in peak_hours],
                'peak_days': [{'day': d, 'engagement': e} for d, e in peak_days],
                'avg_return_hours': avg_return_hours,
                'total_sessions': len(session_gaps) + 1,
                'confidence': min(len(rows) / 50, 1.0)  # Full confidence at 50+ signals
            }
            
            # Store patterns
            self._store_pattern(user_id, 'temporal', patterns)
            
            return patterns
            
        except Exception as e:
            print(f"Warning: Could not analyze temporal patterns: {e}")
            return {}
    
    def analyze_communication_style(self, user_id: int) -> Dict[str, Any]:
        """
        Analyze user's communication preferences.
        Helps match AI tone and response length.
        """
        if not self.db:
            return {}
            
        try:
            cursor = self.db.cursor()
            
            # Get user messages
            cursor.execute('''
                SELECT user_message, timestamp
                FROM history_primary
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 100
            ''', (user_id,))
            
            messages = cursor.fetchall()
            if not messages:
                return {'confidence': 0}
            
            # Analyze message characteristics
            lengths = []
            question_count = 0
            exclamation_count = 0
            emoji_count = 0
            formal_markers = 0
            casual_markers = 0
            
            formal_words = ['please', 'thank you', 'appreciate', 'kindly', 'regards']
            casual_words = ['hey', 'yeah', 'gonna', 'wanna', 'lol', 'haha', 'btw']
            
            for msg, _ in messages:
                if not msg:
                    continue
                msg_lower = msg.lower()
                lengths.append(len(msg))
                
                if '?' in msg:
                    question_count += 1
                if '!' in msg:
                    exclamation_count += 1
                    
                # Simple emoji detection
                emoji_count += sum(1 for c in msg if ord(c) > 127000)
                
                for word in formal_words:
                    if word in msg_lower:
                        formal_markers += 1
                for word in casual_words:
                    if word in msg_lower:
                        casual_markers += 1
            
            n = len(messages)
            avg_length = sum(lengths) / n if n > 0 else 0
            
            # Determine style
            formality = 'formal' if formal_markers > casual_markers else 'casual'
            if abs(formal_markers - casual_markers) < 3:
                formality = 'neutral'
            
            verbosity = 'verbose' if avg_length > 150 else 'concise' if avg_length < 50 else 'moderate'
            
            style = {
                'avg_message_length': avg_length,
                'question_rate': question_count / n if n > 0 else 0,
                'exclamation_rate': exclamation_count / n if n > 0 else 0,
                'uses_emoji': emoji_count > n * 0.1,
                'formality': formality,
                'verbosity': verbosity,
                'confidence': min(n / 30, 1.0),
                'sample_size': n
            }
            
            # Store pattern
            self._store_pattern(user_id, 'communication_style', style)
            
            return style
            
        except Exception as e:
            print(f"Warning: Could not analyze communication style: {e}")
            return {}
    
    def analyze_topic_patterns(self, user_id: int) -> Dict[str, Any]:
        """
        Analyze topic preferences and transitions.
        Like Spotify's taste profile.
        """
        if not self.db:
            return {}
            
        try:
            cursor = self.db.cursor()
            
            # Get topics from engagement signals
            cursor.execute('''
                SELECT topic, signal_type, timestamp
                FROM user_engagement_signals
                WHERE user_id = ? AND topic IS NOT NULL
                ORDER BY timestamp
            ''', (user_id,))
            
            rows = cursor.fetchall()
            if not rows:
                return {'confidence': 0}
            
            # Topic frequency
            topic_scores = defaultdict(float)
            topic_recency = {}
            
            now = datetime.now()
            for topic, signal_type, ts_str in rows:
                try:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    days_ago = (now - ts).days
                    
                    # Apply time decay (like YouTube's recency weighting)
                    decay = math.exp(-days_ago / self.decay_half_life_days * math.log(2))
                    weight = self.engagement_weights.get(signal_type, 1.0)
                    
                    topic_scores[topic] += weight * decay
                    topic_recency[topic] = ts
                except:
                    continue
            
            # Rank topics
            ranked_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Find topic transitions (what topics lead to what)
            transitions = defaultdict(lambda: defaultdict(int))
            prev_topic = None
            for topic, _, _ in rows:
                if prev_topic and prev_topic != topic:
                    transitions[prev_topic][topic] += 1
                prev_topic = topic
            
            return {
                'top_topics': [{'topic': t, 'score': round(s, 2)} for t, s in ranked_topics[:10]],
                'topic_count': len(topic_scores),
                'common_transitions': dict(transitions),
                'confidence': min(len(rows) / 30, 1.0)
            }
            
        except Exception as e:
            print(f"Warning: Could not analyze topic patterns: {e}")
            return {}
    
    # =========================================================================
    # 3. INTEREST GRAPH (TikTok-style weighted preferences)
    # =========================================================================
    
    def _update_interest_score(self, user_id: int, interest_type: str, 
                               interest_key: str, delta: float) -> None:
        """Update interest score with decay and trend tracking."""
        if not self.db:
            return
            
        try:
            cursor = self.db.cursor()
            
            # Get current state
            cursor.execute('''
                SELECT score, interaction_count, last_interaction
                FROM user_interest_graph
                WHERE user_id = ? AND interest_type = ? AND interest_key = ?
            ''', (user_id, interest_type, interest_key))
            
            row = cursor.fetchone()
            now = datetime.now()
            
            if row:
                old_score, count, last_ts = row
                
                # Apply time decay to old score
                if last_ts:
                    try:
                        last_dt = datetime.fromisoformat(last_ts.replace('Z', '+00:00'))
                        days_since = (now - last_dt).days
                        decay = math.exp(-days_since / self.decay_half_life_days * math.log(2))
                        old_score *= decay
                    except:
                        pass
                
                new_score = old_score + delta
                new_count = count + 1
                
                # Determine trend
                trend = 'rising' if delta > 0 else 'falling' if delta < 0 else 'stable'
                
                cursor.execute('''
                    UPDATE user_interest_graph
                    SET score = ?, interaction_count = ?, last_interaction = ?,
                        trend = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND interest_type = ? AND interest_key = ?
                ''', (new_score, new_count, now.isoformat(), trend,
                      user_id, interest_type, interest_key))
            else:
                cursor.execute('''
                    INSERT INTO user_interest_graph
                    (user_id, interest_type, interest_key, score, interaction_count, 
                     last_interaction, trend)
                    VALUES (?, ?, ?, ?, 1, ?, 'new')
                ''', (user_id, interest_type, interest_key, delta, now.isoformat()))
            
            self.db.commit()
            
        except Exception as e:
            print(f"Warning: Could not update interest score: {e}")
    
    def get_interest_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Get user's complete interest profile.
        Like TikTok's "For You" personalization data.
        """
        if not self.db:
            return {}
            
        try:
            cursor = self.db.cursor()
            
            # Get all interests grouped by type
            cursor.execute('''
                SELECT interest_type, interest_key, score, trend, interaction_count
                FROM user_interest_graph
                WHERE user_id = ?
                ORDER BY score DESC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            
            profile = defaultdict(list)
            for int_type, key, score, trend, count in rows:
                profile[int_type].append({
                    'key': key,
                    'score': round(score, 2),
                    'trend': trend,
                    'interactions': count
                })
            
            return dict(profile)
            
        except Exception as e:
            print(f"Warning: Could not get interest profile: {e}")
            return {}
    
    # =========================================================================
    # 4. CHARACTER CHEMISTRY (User-Character affinity)
    # =========================================================================
    
    def _update_character_chemistry(self, user_id: int, character_id: str,
                                    signal_type: str) -> None:
        """Update chemistry score between user and character."""
        if not self.db:
            return
            
        try:
            cursor = self.db.cursor()
            
            # Positive signals increase affinity
            positive_signals = ['positive_feedback', 'follow_up_question', 
                              'saved_highlight', 'returned_to_topic', 'long_message']
            negative_signals = ['quick_exit', 'skipped_suggestion']
            
            if signal_type in positive_signals:
                delta = 0.05
                is_positive = 1
            elif signal_type in negative_signals:
                delta = -0.03
                is_positive = 0
            else:
                delta = 0.01
                is_positive = 0
            
            cursor.execute('''
                INSERT INTO user_character_chemistry
                (user_id, character_id, affinity_score, total_interactions, 
                 positive_outcomes, last_interaction)
                VALUES (?, ?, ?, 1, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, character_id) DO UPDATE SET
                    affinity_score = MIN(1.0, MAX(0.0, affinity_score + ?)),
                    total_interactions = total_interactions + 1,
                    positive_outcomes = positive_outcomes + ?,
                    last_interaction = CURRENT_TIMESTAMP
            ''', (user_id, character_id, 0.5 + delta, is_positive, delta, is_positive))
            
            self.db.commit()
            
        except Exception as e:
            print(f"Warning: Could not update character chemistry: {e}")
    
    def get_character_recommendations(self, user_id: int, 
                                      context: Dict = None) -> List[Dict]:
        """
        Recommend best characters for user based on chemistry and context.
        Like Spotify's "Made for You" playlists.
        """
        if not self.db:
            return []
            
        try:
            cursor = self.db.cursor()
            
            cursor.execute('''
                SELECT character_id, affinity_score, total_interactions, 
                       positive_outcomes, last_interaction
                FROM user_character_chemistry
                WHERE user_id = ?
                ORDER BY affinity_score DESC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            
            recommendations = []
            for char_id, affinity, total, positive, last_ts in rows:
                success_rate = positive / total if total > 0 else 0.5
                
                recommendations.append({
                    'character_id': char_id,
                    'affinity_score': round(affinity, 2),
                    'success_rate': round(success_rate, 2),
                    'total_interactions': total,
                    'recommendation_reason': self._get_recommendation_reason(
                        affinity, success_rate, total
                    )
                })
            
            return recommendations
            
        except Exception as e:
            print(f"Warning: Could not get character recommendations: {e}")
            return []
    
    def _get_recommendation_reason(self, affinity: float, success_rate: float,
                                   interactions: int) -> str:
        """Generate human-readable recommendation reason."""
        if interactions < 3:
            return "Still getting to know you"
        elif affinity > 0.7 and success_rate > 0.7:
            return "Great chemistry - highly recommended"
        elif affinity > 0.6:
            return "Good match based on past conversations"
        elif success_rate > 0.6:
            return "Helpful in your past discussions"
        else:
            return "Available to help"
    
    # =========================================================================
    # 5. PREDICTION ENGINE (Proactive suggestions)
    # =========================================================================
    
    def predict_user_needs(self, user_id: int, context: Dict = None) -> Dict[str, Any]:
        """
        Predict what user might need next.
        Like YouTube's "Up Next" but for life guidance.
        """
        predictions = {
            'likely_topics': [],
            'suggested_characters': [],
            'optimal_outreach_time': None,
            'predicted_emotional_state': None,
            'recommended_actions': [],
            'confidence': 0
        }
        
        if not self.db:
            return predictions
            
        try:
            # Get recent patterns
            topic_patterns = self.analyze_topic_patterns(user_id)
            temporal_patterns = self.analyze_temporal_patterns(user_id)
            
            # Predict likely topics (based on history and transitions)
            if topic_patterns.get('top_topics'):
                predictions['likely_topics'] = [
                    t['topic'] for t in topic_patterns['top_topics'][:3]
                ]
            
            # Suggest optimal characters
            char_recs = self.get_character_recommendations(user_id, context)
            predictions['suggested_characters'] = char_recs[:3]
            
            # Optimal outreach time
            if temporal_patterns.get('peak_hours'):
                best_hour = temporal_patterns['peak_hours'][0]['hour']
                predictions['optimal_outreach_time'] = f"{best_hour:02d}:00"
            
            # Predict next need based on topic transitions
            if topic_patterns.get('common_transitions') and predictions['likely_topics']:
                current_topic = predictions['likely_topics'][0]
                transitions = topic_patterns['common_transitions'].get(current_topic, {})
                if transitions:
                    next_topic = max(transitions.items(), key=lambda x: x[1])[0]
                    predictions['recommended_actions'].append({
                        'action': 'explore_topic',
                        'topic': next_topic,
                        'reason': f'Users often explore {next_topic} after {current_topic}'
                    })
            
            predictions['confidence'] = min(
                topic_patterns.get('confidence', 0),
                temporal_patterns.get('confidence', 0)
            )
            
            return predictions
            
        except Exception as e:
            print(f"Warning: Could not predict user needs: {e}")
            return predictions
    
    def get_proactive_suggestions(self, user_id: int) -> List[Dict]:
        """
        Generate proactive outreach suggestions.
        Like Instagram's "Check out what you missed" notifications.
        """
        suggestions = []
        
        if not self.db:
            return suggestions
            
        try:
            cursor = self.db.cursor()
            
            # Check for unfinished topics (user engaged but didn't resolve)
            cursor.execute('''
                SELECT topic, MAX(timestamp) as last_seen
                FROM user_engagement_signals
                WHERE user_id = ? AND topic IS NOT NULL
                GROUP BY topic
                HAVING COUNT(*) BETWEEN 2 AND 5
                ORDER BY last_seen DESC
                LIMIT 3
            ''', (user_id,))
            
            for topic, last_seen in cursor.fetchall():
                suggestions.append({
                    'type': 'unfinished_topic',
                    'message': f"Would you like to continue exploring {topic}?",
                    'topic': topic,
                    'priority': 'medium'
                })
            
            # Check if user hasn't been active (re-engagement)
            cursor.execute('''
                SELECT MAX(timestamp) FROM user_engagement_signals
                WHERE user_id = ?
            ''', (user_id,))
            
            last_active = cursor.fetchone()[0]
            if last_active:
                try:
                    last_dt = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
                    days_inactive = (datetime.now() - last_dt).days
                    
                    if days_inactive >= 3:
                        suggestions.append({
                            'type': 're_engagement',
                            'message': "It's been a few days - how are things going?",
                            'days_inactive': days_inactive,
                            'priority': 'high' if days_inactive >= 7 else 'medium'
                        })
                except:
                    pass
            
            # Suggest based on successful past patterns
            cursor.execute('''
                SELECT character_id, COUNT(*) as success_count
                FROM user_engagement_signals
                WHERE user_id = ? AND signal_type = 'positive_feedback'
                GROUP BY character_id
                ORDER BY success_count DESC
                LIMIT 1
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row:
                suggestions.append({
                    'type': 'successful_character',
                    'message': f"Your conversations with {row[0]} have been helpful",
                    'character_id': row[0],
                    'priority': 'low'
                })
            
            return suggestions
            
        except Exception as e:
            print(f"Warning: Could not get proactive suggestions: {e}")
            return []
    
    # =========================================================================
    # 6. UNIFIED INTELLIGENCE CONTEXT (For AI prompts)
    # =========================================================================
    
    def build_intelligence_context(self, user_id: int, current_message: str = None,
                                   current_topic: str = None) -> Dict[str, Any]:
        """
        Build comprehensive user intelligence context for AI.
        This is the main integration point with the AI system.
        """
        context = {
            'user_id': user_id,
            'engagement': {},
            'patterns': {},
            'interests': {},
            'predictions': {},
            'recommendations': []
        }
        
        try:
            # Engagement summary
            context['engagement'] = self.get_engagement_summary(user_id, days=30)
            
            # Behavioral patterns
            context['patterns'] = {
                'temporal': self.analyze_temporal_patterns(user_id),
                'communication': self.analyze_communication_style(user_id),
                'topics': self.analyze_topic_patterns(user_id)
            }
            
            # Interest profile
            context['interests'] = self.get_interest_profile(user_id)
            
            # Predictions
            context['predictions'] = self.predict_user_needs(user_id)
            
            # Character recommendations
            context['recommendations'] = self.get_character_recommendations(user_id)
            
            return context
            
        except Exception as e:
            print(f"Warning: Could not build intelligence context: {e}")
            return context
    
    def get_ai_prompt_context(self, user_id: int) -> str:
        """
        Get formatted context string for AI system prompts.
        Integrates with AdaptiveCompanion and FollowUpSuggestions.
        """
        intel = self.build_intelligence_context(user_id)
        
        parts = []
        
        # Communication style adaptation
        comm = intel.get('patterns', {}).get('communication', {})
        if comm.get('confidence', 0) > 0.3:
            style_hints = []
            if comm.get('verbosity') == 'concise':
                style_hints.append("prefers brief, direct responses")
            elif comm.get('verbosity') == 'verbose':
                style_hints.append("appreciates detailed explanations")
            
            if comm.get('formality') == 'casual':
                style_hints.append("uses casual language")
            elif comm.get('formality') == 'formal':
                style_hints.append("prefers professional tone")
            
            if comm.get('uses_emoji'):
                style_hints.append("comfortable with emoji")
            
            if style_hints:
                parts.append(f"Communication style: This user {', '.join(style_hints)}.")
        
        # Topic interests
        interests = intel.get('interests', {}).get('topic', [])
        if interests:
            top_3 = [i['key'] for i in interests[:3]]
            parts.append(f"Primary interests: {', '.join(top_3)}.")
        
        # Engagement level
        engagement = intel.get('engagement', {})
        if engagement.get('active_days', 0) > 10:
            parts.append("This is a highly engaged user who visits frequently.")
        
        # Predictions
        preds = intel.get('predictions', {})
        if preds.get('likely_topics'):
            parts.append(f"May want to discuss: {', '.join(preds['likely_topics'][:2])}.")
        
        return "\n".join(parts) if parts else ""
    
    # =========================================================================
    # 7. CONVERSATION-SPECIFIC METRICS (Our Unique Advantage)
    # =========================================================================
    
    def analyze_conversation_depth(self, user_id: int, session_id: str = None) -> Dict[str, Any]:
        """
        Analyze conversation depth - our equivalent to YouTube's watch time.
        Unlike passive video watching, conversations show active engagement.
        """
        if not self.db:
            return {}
            
        try:
            cursor = self.db.cursor()
            
            # Get conversation exchanges
            query = '''
                SELECT user_message, assistant_response, timestamp, character
                FROM history_primary
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 100
            '''
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()
            
            if not rows:
                return {'confidence': 0, 'message': 'No conversation data'}
            
            # Calculate metrics
            total_exchanges = len(rows)
            total_user_chars = sum(len(r[0] or '') for r in rows)
            total_ai_chars = sum(len(r[1] or '') for r in rows)
            
            # Topic continuity (same character = same topic thread)
            topic_runs = []
            current_run = 1
            prev_char = None
            for _, _, _, char in rows:
                if char == prev_char:
                    current_run += 1
                else:
                    if prev_char:
                        topic_runs.append(current_run)
                    current_run = 1
                prev_char = char
            topic_runs.append(current_run)
            
            avg_topic_depth = sum(topic_runs) / len(topic_runs) if topic_runs else 0
            max_topic_depth = max(topic_runs) if topic_runs else 0
            
            # Question depth (follow-up questions indicate engagement)
            question_count = sum(1 for r in rows if r[0] and '?' in r[0])
            
            depth_metrics = {
                'total_exchanges': total_exchanges,
                'avg_message_length': total_user_chars / total_exchanges if total_exchanges else 0,
                'avg_response_length': total_ai_chars / total_exchanges if total_exchanges else 0,
                'avg_topic_depth': round(avg_topic_depth, 1),
                'max_topic_depth': max_topic_depth,
                'question_rate': question_count / total_exchanges if total_exchanges else 0,
                'depth_score': min(1.0, (avg_topic_depth / 5) * 0.4 + 
                                       (question_count / total_exchanges) * 0.3 +
                                       min(total_user_chars / (total_exchanges * 100), 1) * 0.3),
                'confidence': min(total_exchanges / 20, 1.0)
            }
            
            return depth_metrics
            
        except Exception as e:
            print(f"Warning: Could not analyze conversation depth: {e}")
            return {}
    
    def analyze_emotional_journey(self, user_id: int, recent_messages: int = 20) -> Dict[str, Any]:
        """
        Track emotional journey through conversation.
        Our equivalent to video engagement - but richer because it's active.
        """
        if not self.db:
            return {}
            
        try:
            cursor = self.db.cursor()
            
            cursor.execute('''
                SELECT user_message, timestamp
                FROM history_primary
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, recent_messages))
            
            messages = cursor.fetchall()
            if not messages:
                return {'confidence': 0}
            
            # Simple sentiment indicators
            positive_words = ['thank', 'helpful', 'great', 'better', 'understand', 
                            'appreciate', 'good', 'happy', 'relieved', 'clear']
            negative_words = ['confused', 'frustrated', 'angry', 'upset', 'worried',
                            'anxious', 'stressed', 'stuck', 'hopeless', 'lost']
            resolution_words = ['that helps', 'makes sense', 'i see', 'got it',
                              'i understand', 'feel better', 'thank you']
            
            journey = []
            for msg, ts in reversed(messages):  # Chronological
                if not msg:
                    continue
                msg_lower = msg.lower()
                
                pos_count = sum(1 for w in positive_words if w in msg_lower)
                neg_count = sum(1 for w in negative_words if w in msg_lower)
                has_resolution = any(r in msg_lower for r in resolution_words)
                
                sentiment = (pos_count - neg_count) / max(pos_count + neg_count, 1)
                journey.append({
                    'sentiment': sentiment,
                    'has_resolution': has_resolution
                })
            
            if not journey:
                return {'confidence': 0}
            
            # Calculate journey metrics
            start_sentiment = journey[0]['sentiment'] if journey else 0
            end_sentiment = journey[-1]['sentiment'] if journey else 0
            had_resolution = any(j['has_resolution'] for j in journey)
            
            # Emotional trajectory
            if end_sentiment > start_sentiment + 0.2:
                trajectory = 'improving'
            elif end_sentiment < start_sentiment - 0.2:
                trajectory = 'declining'
            else:
                trajectory = 'stable'
            
            return {
                'start_sentiment': round(start_sentiment, 2),
                'end_sentiment': round(end_sentiment, 2),
                'trajectory': trajectory,
                'had_resolution': had_resolution,
                'sentiment_change': round(end_sentiment - start_sentiment, 2),
                'journey_length': len(journey),
                'confidence': min(len(journey) / 10, 1.0)
            }
            
        except Exception as e:
            print(f"Warning: Could not analyze emotional journey: {e}")
            return {}
    
    def get_resolution_rate(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Calculate topic resolution rate - did we actually help?
        Our equivalent to video completion rate.
        """
        if not self.db:
            return {}
            
        try:
            cursor = self.db.cursor()
            cutoff = datetime.now() - timedelta(days=days)
            
            # Get all conversations
            cursor.execute('''
                SELECT user_message, character, timestamp
                FROM history_primary
                WHERE user_id = ? AND timestamp > ?
                ORDER BY timestamp
            ''', (user_id, cutoff.isoformat()))
            
            rows = cursor.fetchall()
            if not rows:
                return {'confidence': 0}
            
            resolution_indicators = ['thank', 'helpful', 'makes sense', 'got it',
                                    'understand', 'feel better', 'that helps']
            
            # Group by topic (character sessions)
            topics = defaultdict(list)
            for msg, char, ts in rows:
                topics[char].append(msg or '')
            
            resolved_topics = 0
            total_topics = len(topics)
            
            for char, messages in topics.items():
                # Check if any message indicates resolution
                for msg in messages:
                    if any(ind in msg.lower() for ind in resolution_indicators):
                        resolved_topics += 1
                        break
            
            resolution_rate = resolved_topics / total_topics if total_topics else 0
            
            return {
                'resolution_rate': round(resolution_rate, 2),
                'resolved_topics': resolved_topics,
                'total_topics': total_topics,
                'confidence': min(total_topics / 5, 1.0)
            }
            
        except Exception as e:
            print(f"Warning: Could not calculate resolution rate: {e}")
            return {}
    
    # =========================================================================
    # 8. FUTURE MEDIA HANDLERS (Extensibility)
    # =========================================================================
    
    def record_media_engagement(self, user_id: int, content_id: str, 
                                media_type: str, engagement_type: str,
                                progress_percent: float = None,
                                duration_seconds: int = None,
                                context: Dict = None) -> None:
        """
        Record engagement with any media type (future-proof).
        Ready for when videos/images/audio are added.
        """
        if not self.db:
            return
            
        try:
            cursor = self.db.cursor()
            
            # Get appropriate weight based on media type
            if media_type == 'video':
                weights = self.video_engagement_weights
            elif media_type == 'image':
                weights = self.image_engagement_weights
            elif media_type == 'audio':
                weights = self.audio_engagement_weights
            else:
                weights = self.engagement_weights
            
            weight = weights.get(engagement_type, 1.0)
            
            cursor.execute('''
                INSERT INTO media_engagement
                (user_id, content_id, media_type, engagement_type, 
                 progress_percent, duration_seconds, context_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, content_id, media_type, engagement_type,
                progress_percent, duration_seconds,
                json.dumps(context) if context else None
            ))
            
            self.db.commit()
            
            # Also update interest graph
            self._update_interest_score(user_id, f'{media_type}_content', content_id, weight)
            
        except Exception as e:
            print(f"Warning: Could not record media engagement: {e}")
    
    def get_media_engagement_summary(self, user_id: int, 
                                     media_type: str = None) -> Dict[str, Any]:
        """
        Get engagement summary for media content (future-proof).
        """
        if not self.db:
            return {}
            
        try:
            cursor = self.db.cursor()
            
            if media_type:
                cursor.execute('''
                    SELECT engagement_type, COUNT(*), AVG(progress_percent)
                    FROM media_engagement
                    WHERE user_id = ? AND media_type = ?
                    GROUP BY engagement_type
                ''', (user_id, media_type))
            else:
                cursor.execute('''
                    SELECT media_type, engagement_type, COUNT(*), AVG(progress_percent)
                    FROM media_engagement
                    WHERE user_id = ?
                    GROUP BY media_type, engagement_type
                ''', (user_id,))
            
            rows = cursor.fetchall()
            
            summary = defaultdict(dict)
            for row in rows:
                if media_type:
                    eng_type, count, avg_progress = row
                    summary[eng_type] = {
                        'count': count,
                        'avg_progress': round(avg_progress or 0, 1)
                    }
                else:
                    m_type, eng_type, count, avg_progress = row
                    summary[m_type][eng_type] = {
                        'count': count,
                        'avg_progress': round(avg_progress or 0, 1)
                    }
            
            return dict(summary)
            
        except Exception as e:
            print(f"Warning: Could not get media engagement summary: {e}")
            return {}
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _store_pattern(self, user_id: int, pattern_type: str, 
                       pattern_data: Dict) -> None:
        """Store a discovered behavioral pattern."""
        if not self.db:
            return
            
        try:
            cursor = self.db.cursor()
            cursor.execute('''
                INSERT INTO user_behavioral_patterns
                (user_id, pattern_type, pattern_data, confidence, sample_size)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, pattern_type) DO UPDATE SET
                    pattern_data = ?,
                    confidence = ?,
                    sample_size = ?,
                    last_validated = CURRENT_TIMESTAMP
            ''', (
                user_id, pattern_type, json.dumps(pattern_data),
                pattern_data.get('confidence', 0),
                pattern_data.get('sample_size', 0),
                json.dumps(pattern_data),
                pattern_data.get('confidence', 0),
                pattern_data.get('sample_size', 0)
            ))
            self.db.commit()
        except Exception as e:
            print(f"Warning: Could not store pattern: {e}")


# =========================================================================
# SINGLETON INSTANCE
# =========================================================================

_intelligence_system = None

def get_intelligence_system(db_connection=None) -> UserIntelligenceSystem:
    """Get or create the user intelligence system instance."""
    global _intelligence_system
    if _intelligence_system is None or db_connection is not None:
        _intelligence_system = UserIntelligenceSystem(db_connection)
    return _intelligence_system

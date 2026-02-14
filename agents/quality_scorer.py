"""
Conversation Quality Scorer Agent

Automatically grades every conversation on multiple dimensions:
- Coherence: Did the AI stay on topic and respond logically?
- Helpfulness: Did it address the user's actual concern?
- Character Consistency: Did it maintain character voice and style?
- Resolution: Did the conversation reach a natural conclusion?
- Engagement: Did the AI encourage continued dialogue?

Works by analyzing conversation transcripts from the database.
Can score historical conversations or subscribe to the Event Bus for real-time scoring.
"""

import sqlite3
import os
import re
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from collections import Counter


@dataclass
class QualityScore:
    """Quality score for a single conversation"""
    session_id: str
    coherence: float        # 0-1: logical flow, stayed on topic
    helpfulness: float      # 0-1: addressed user's needs
    engagement: float       # 0-1: encouraged continued dialogue
    resolution: float       # 0-1: reached natural conclusion
    consistency: float      # 0-1: maintained character voice
    overall: float = 0.0    # Weighted average
    character_id: str = ''  # Which character (domain or philosophy)
    character_type: str = ''  # 'domain' or 'philosophy' or 'unknown'
    flags: List[str] = field(default_factory=list)   # Quality issues detected
    details: Dict = field(default_factory=dict)
    scored_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self):
        # Weighted overall score
        self.overall = (
            self.coherence * 0.25 +
            self.helpfulness * 0.30 +
            self.engagement * 0.15 +
            self.resolution * 0.15 +
            self.consistency * 0.15
        )


@dataclass
class QualityReport:
    """Aggregate quality report across multiple conversations"""
    scores: List[QualityScore]
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def avg_overall(self) -> float:
        return sum(s.overall for s in self.scores) / max(1, len(self.scores))
    
    @property
    def avg_coherence(self) -> float:
        return sum(s.coherence for s in self.scores) / max(1, len(self.scores))
    
    @property
    def avg_helpfulness(self) -> float:
        return sum(s.helpfulness for s in self.scores) / max(1, len(self.scores))
    
    @property
    def avg_engagement(self) -> float:
        return sum(s.engagement for s in self.scores) / max(1, len(self.scores))
    
    @property
    def avg_resolution(self) -> float:
        return sum(s.resolution for s in self.scores) / max(1, len(self.scores))
    
    @property
    def avg_consistency(self) -> float:
        return sum(s.consistency for s in self.scores) / max(1, len(self.scores))
    
    @property
    def flagged_count(self) -> int:
        return sum(1 for s in self.scores if s.flags)
    
    def common_flags(self, top_n: int = 5) -> List[Tuple[str, int]]:
        all_flags = [f for s in self.scores for f in s.flags]
        return Counter(all_flags).most_common(top_n)
    
    def to_dict(self) -> Dict:
        return {
            'generated_at': self.generated_at,
            'conversations_scored': len(self.scores),
            'avg_overall': round(self.avg_overall, 3),
            'avg_coherence': round(self.avg_coherence, 3),
            'avg_helpfulness': round(self.avg_helpfulness, 3),
            'avg_engagement': round(self.avg_engagement, 3),
            'avg_resolution': round(self.avg_resolution, 3),
            'avg_consistency': round(self.avg_consistency, 3),
            'flagged_conversations': self.flagged_count,
            'common_flags': self.common_flags(),
        }


class ConversationQualityScorer:
    """Scores conversation quality using heuristic analysis"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.scores: List[QualityScore] = []
        self._init_table()
    
    def _init_table(self):
        """Create quality scores table if it doesn't exist"""
        if not os.path.exists(self.db_path):
            return
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS conversation_quality_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    character_id TEXT DEFAULT '',
                    character_type TEXT DEFAULT '',
                    coherence REAL,
                    helpfulness REAL,
                    engagement REAL,
                    resolution REAL,
                    consistency REAL,
                    overall REAL,
                    flags TEXT,
                    details TEXT,
                    scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_quality_session
                ON conversation_quality_scores(session_id)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_quality_character
                ON conversation_quality_scores(character_id)
            ''')
            # Migrate: add column if table already exists without it
            try:
                conn.execute('ALTER TABLE conversation_quality_scores ADD COLUMN character_id TEXT DEFAULT ""')
            except Exception:
                pass  # Column already exists
            try:
                conn.execute('ALTER TABLE conversation_quality_scores ADD COLUMN character_type TEXT DEFAULT ""')
            except Exception:
                pass  # Column already exists
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Could not create quality scores table: {e}")
    
    def get_conversation_messages(self, session_id: str) -> List[Dict]:
        """Fetch all messages for a conversation"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT m.sender_type, m.content, m.created_at
                FROM messages m
                JOIN ai_conversations c ON m.conversation_id = c.id
                WHERE c.session_id = ?
                ORDER BY m.created_at ASC
            ''', (session_id,))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'sender_type': row[0],
                    'content': row[1],
                    'created_at': row[2]
                })
            return messages
        except Exception as e:
            print(f"Error fetching messages: {e}")
            return []
        finally:
            conn.close()
    
    def get_recent_conversations(self, days: int = 7, limit: int = 50) -> List[Dict]:
        """Get session IDs + character info of recent conversations with enough messages"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT c.session_id, c.character_id, COUNT(m.id) as msg_count
                FROM ai_conversations c
                JOIN messages m ON m.conversation_id = c.id
                WHERE c.created_at > datetime('now', ?)
                GROUP BY c.session_id
                HAVING msg_count >= 4
                ORDER BY c.created_at DESC
                LIMIT ?
            ''', (f'-{days} days', limit))
            
            return [
                {'session_id': row[0], 'character_id': row[1] or ''}
                for row in cursor.fetchall()
            ]
        except Exception as e:
            print(f"Error fetching conversations: {e}")
            return []
        finally:
            conn.close()
    
    def _classify_character(self, character_id: str) -> str:
        """Classify character as 'domain', 'philosophy', or 'unknown'."""
        if not character_id:
            return 'unknown'
        domain_ids = {
            'coordinator', 'domain_work', 'domain_relationships',
            'domain_wellness', 'domain_growth', 'domain_creativity',
        }
        philosophy_ids = {
            'super_motivational_coach', 'wisdom_sage', 'stoic_philosopher',
            'psychologist', 'zen_master', 'business_coach', 'life_coach', 'scientist',
        }
        if character_id in domain_ids or character_id.startswith('domain_'):
            return 'domain'
        if character_id in philosophy_ids:
            return 'philosophy'
        return 'unknown'
    
    # ================================================================
    # SCORING HEURISTICS
    # ================================================================
    
    def score_coherence(self, messages: List[Dict]) -> Tuple[float, List[str]]:
        """Score how logically coherent the AI responses are.
        
        Checks:
        - Do AI responses relate to user messages?
        - Are there non-sequiturs or topic jumps?
        - Does the conversation flow naturally?
        """
        flags = []
        if len(messages) < 2:
            return 0.5, ['too_few_messages']
        
        user_msgs = [m for m in messages if m['sender_type'] == 'user']
        ai_msgs = [m for m in messages if m['sender_type'] == 'assistant']
        
        if not ai_msgs:
            return 0.0, ['no_ai_responses']
        
        score = 0.7  # Base score
        
        # Check keyword overlap between user messages and AI responses
        overlap_scores = []
        for i, msg in enumerate(messages):
            if msg['sender_type'] == 'assistant' and i > 0:
                # Find the preceding user message
                prev_user = None
                for j in range(i-1, -1, -1):
                    if messages[j]['sender_type'] == 'user':
                        prev_user = messages[j]
                        break
                
                if prev_user:
                    user_words = set(self._extract_keywords(prev_user['content']))
                    ai_words = set(self._extract_keywords(msg['content']))
                    
                    if user_words:
                        overlap = len(user_words & ai_words) / len(user_words)
                        overlap_scores.append(overlap)
        
        if overlap_scores:
            avg_overlap = sum(overlap_scores) / len(overlap_scores)
            # 0.1+ overlap is decent (AI rephrases, doesn't just echo)
            if avg_overlap >= 0.15:
                score += 0.2
            elif avg_overlap >= 0.05:
                score += 0.1
            else:
                score -= 0.1
                flags.append('low_topic_relevance')
        
        # Check for repetitive AI responses
        ai_contents = [m['content'] for m in ai_msgs]
        if len(ai_contents) >= 2:
            for i in range(1, len(ai_contents)):
                similarity = self._text_similarity(ai_contents[i], ai_contents[i-1])
                if similarity > 0.7:
                    score -= 0.15
                    flags.append('repetitive_responses')
                    break
        
        # Check for very short AI responses (less than 50 chars)
        short_responses = sum(1 for m in ai_msgs if len(m['content']) < 50)
        if short_responses > len(ai_msgs) * 0.5:
            score -= 0.1
            flags.append('many_short_responses')
        
        return max(0.0, min(1.0, score)), flags
    
    def score_helpfulness(self, messages: List[Dict]) -> Tuple[float, List[str]]:
        """Score how helpful the AI responses are.
        
        Checks:
        - Does AI provide actionable advice?
        - Does it acknowledge the user's feelings/situation?
        - Does it offer concrete suggestions?
        """
        flags = []
        ai_msgs = [m for m in messages if m['sender_type'] == 'assistant']
        
        if not ai_msgs:
            return 0.0, ['no_ai_responses']
        
        score = 0.5  # Base score
        
        # Check for empathy markers
        empathy_patterns = [
            r'understand', r'sorry to hear', r'must be', r'feel',
            r'normal to', r'valid', r'hear you', r'sounds like',
            r'that\'s tough', r'challenging', r'difficult'
        ]
        
        # Check for actionable advice markers
        action_patterns = [
            r'try', r'consider', r'suggest', r'could', r'might want to',
            r'step', r'approach', r'strategy', r'method', r'technique',
            r'start by', r'first', r'one way', r'tip'
        ]
        
        # Check for question-asking (shows engagement)
        question_patterns = [r'\?']
        
        all_ai_text = ' '.join(m['content'].lower() for m in ai_msgs)
        
        empathy_count = sum(1 for p in empathy_patterns if re.search(p, all_ai_text))
        action_count = sum(1 for p in action_patterns if re.search(p, all_ai_text))
        question_count = len(re.findall(r'\?', all_ai_text))
        
        # Empathy bonus
        if empathy_count >= 3:
            score += 0.15
        elif empathy_count >= 1:
            score += 0.08
        else:
            flags.append('lacks_empathy')
        
        # Actionable advice bonus
        if action_count >= 4:
            score += 0.2
        elif action_count >= 2:
            score += 0.1
        else:
            flags.append('lacks_actionable_advice')
        
        # Questions show engagement
        if question_count >= 2:
            score += 0.1
        
        # Check response length (too short = unhelpful)
        avg_len = sum(len(m['content']) for m in ai_msgs) / len(ai_msgs)
        if avg_len > 200:
            score += 0.05
        elif avg_len < 80:
            score -= 0.1
            flags.append('responses_too_brief')
        
        return max(0.0, min(1.0, score)), flags
    
    def score_engagement(self, messages: List[Dict]) -> Tuple[float, List[str]]:
        """Score how well the AI encourages continued dialogue.
        
        Checks:
        - Does AI ask follow-up questions?
        - Does conversation grow in depth?
        - Does user continue willingly (longer messages over time)?
        """
        flags = []
        user_msgs = [m for m in messages if m['sender_type'] == 'user']
        ai_msgs = [m for m in messages if m['sender_type'] == 'assistant']
        
        if len(user_msgs) < 2:
            return 0.5, ['too_few_user_messages']
        
        score = 0.5
        
        # Check if AI asks questions
        ai_questions = sum(1 for m in ai_msgs if '?' in m['content'])
        question_rate = ai_questions / max(1, len(ai_msgs))
        if question_rate >= 0.5:
            score += 0.2
        elif question_rate >= 0.25:
            score += 0.1
        else:
            flags.append('ai_rarely_asks_questions')
        
        # Check if user messages grow or maintain length (engagement signal)
        user_lengths = [len(m['content']) for m in user_msgs]
        if len(user_lengths) >= 3:
            first_half_avg = sum(user_lengths[:len(user_lengths)//2]) / max(1, len(user_lengths)//2)
            second_half_avg = sum(user_lengths[len(user_lengths)//2:]) / max(1, len(user_lengths) - len(user_lengths)//2)
            
            if second_half_avg >= first_half_avg * 0.8:
                score += 0.15  # User maintained or increased engagement
            else:
                score -= 0.05
                flags.append('user_engagement_declining')
        
        # More messages = more engaged
        if len(user_msgs) >= 6:
            score += 0.15
        elif len(user_msgs) >= 4:
            score += 0.05
        
        return max(0.0, min(1.0, score)), flags
    
    def score_resolution(self, messages: List[Dict]) -> Tuple[float, List[str]]:
        """Score whether the conversation reached a natural conclusion.
        
        Checks:
        - Does the last AI message provide closure?
        - Is there a summary or action plan?
        - Did the conversation end abruptly?
        """
        flags = []
        
        if not messages:
            return 0.0, ['empty_conversation']
        
        score = 0.5
        last_msg = messages[-1]
        
        # Better if last message is from AI (natural end)
        if last_msg['sender_type'] == 'assistant':
            score += 0.1
            
            last_content = last_msg['content'].lower()
            
            # Check for closing/summary patterns
            closing_patterns = [
                r'remember', r'in summary', r'to summarize', r'key takeaway',
                r'good luck', r'you\'ve got this', r'wish you', r'all the best',
                r'feel free to', r'come back', r'here .* you', r'let me know',
                r'hope this helps', r'take care'
            ]
            
            closing_count = sum(1 for p in closing_patterns if re.search(p, last_content))
            if closing_count >= 2:
                score += 0.2
            elif closing_count >= 1:
                score += 0.1
        else:
            # Ended on user message — might be abrupt
            last_content = last_msg['content'].lower()
            
            # Check if it's a thankful closing
            thanks_patterns = [r'thank', r'thanks', r'helpful', r'appreciate', r'great', r'bye']
            if any(re.search(p, last_content) for p in thanks_patterns):
                score += 0.15
            else:
                flags.append('ended_on_user_message')
                score -= 0.05
        
        # Check conversation length (very short = probably unresolved)
        if len(messages) >= 6:
            score += 0.1
        elif len(messages) <= 2:
            score -= 0.1
            flags.append('very_short_conversation')
        
        return max(0.0, min(1.0, score)), flags
    
    def score_consistency(self, messages: List[Dict]) -> Tuple[float, List[str]]:
        """Score character consistency across responses.
        
        Checks:
        - Consistent tone across responses
        - No personality shifts mid-conversation
        - Stable response length patterns
        """
        flags = []
        ai_msgs = [m for m in messages if m['sender_type'] == 'assistant']
        
        if len(ai_msgs) < 2:
            return 0.7, []  # Can't judge consistency with < 2 responses
        
        score = 0.7
        
        # Check tone consistency (formality level)
        formality_scores = []
        for msg in ai_msgs:
            formality = self._estimate_formality(msg['content'])
            formality_scores.append(formality)
        
        if formality_scores:
            formality_range = max(formality_scores) - min(formality_scores)
            if formality_range < 0.2:
                score += 0.2  # Very consistent tone
            elif formality_range < 0.4:
                score += 0.1
            else:
                flags.append('inconsistent_tone')
                score -= 0.1
        
        # Check response length consistency
        lengths = [len(m['content']) for m in ai_msgs]
        if len(lengths) >= 2:
            avg_len = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_len)**2 for l in lengths) / len(lengths)
            cv = (length_variance ** 0.5) / max(1, avg_len)  # Coefficient of variation
            
            if cv < 0.3:
                score += 0.1  # Consistent length
            elif cv > 0.8:
                flags.append('highly_variable_response_length')
                score -= 0.05
        
        return max(0.0, min(1.0, score)), flags
    
    # ================================================================
    # MAIN SCORING
    # ================================================================
    
    def score_conversation(self, session_id: str, save: bool = True) -> Optional[QualityScore]:
        """Score a single conversation by session_id"""
        messages = self.get_conversation_messages(session_id)
        
        if len(messages) < 2:
            return None
        
        coherence, c_flags = self.score_coherence(messages)
        helpfulness, h_flags = self.score_helpfulness(messages)
        engagement, e_flags = self.score_engagement(messages)
        resolution, r_flags = self.score_resolution(messages)
        consistency, s_flags = self.score_consistency(messages)
        
        all_flags = c_flags + h_flags + e_flags + r_flags + s_flags
        
        # Look up character_id for this session
        char_id = getattr(self, '_current_character_id', '') or ''
        char_type = self._classify_character(char_id)
        
        quality = QualityScore(
            session_id=session_id,
            coherence=round(coherence, 3),
            helpfulness=round(helpfulness, 3),
            engagement=round(engagement, 3),
            resolution=round(resolution, 3),
            consistency=round(consistency, 3),
            character_id=char_id,
            character_type=char_type,
            flags=all_flags,
            details={
                'message_count': len(messages),
                'user_messages': sum(1 for m in messages if m['sender_type'] == 'user'),
                'ai_messages': sum(1 for m in messages if m['sender_type'] == 'assistant'),
                'character_id': char_id,
                'character_type': char_type,
            }
        )
        
        if save:
            self._save_score(quality)
        
        self.scores.append(quality)
        return quality
    
    def score_recent(self, days: int = 7, limit: int = 50) -> QualityReport:
        """Score all recent conversations and generate a report"""
        conversations = self.get_recent_conversations(days=days, limit=limit)
        
        scores = []
        for convo in conversations:
            # Pass character_id through for this scoring cycle
            self._current_character_id = convo.get('character_id', '')
            score = self.score_conversation(convo['session_id'])
            if score:
                scores.append(score)
        self._current_character_id = ''
        
        return QualityReport(scores=scores)
    
    def _save_score(self, score: QualityScore):
        """Save quality score to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            conn.execute('''
                INSERT INTO conversation_quality_scores
                (session_id, character_id, character_type, coherence, helpfulness,
                 engagement, resolution, consistency, overall, flags, details, scored_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                score.session_id, score.character_id, score.character_type,
                score.coherence, score.helpfulness,
                score.engagement, score.resolution, score.consistency,
                score.overall, json.dumps(score.flags), json.dumps(score.details),
                score.scored_at
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Could not save quality score: {e}")
    
    # ================================================================
    # UTILITY METHODS
    # ================================================================
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'shall', 'to', 'of',
            'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
            'about', 'like', 'through', 'after', 'over', 'between', 'out',
            'and', 'or', 'but', 'not', 'no', 'so', 'if', 'than', 'too',
            'very', 'just', 'that', 'this', 'it', 'its', 'my', 'your',
            'i', 'me', 'we', 'you', 'he', 'she', 'they', 'them', 'what',
            'which', 'who', 'when', 'where', 'how', 'all', 'each', 'any',
            'some', 'more', 'most', 'other', 'also', 'up', 'down', 'then',
        }
        words = re.findall(r'\b[a-z]+\b', text.lower())
        return [w for w in words if len(w) > 3 and w not in stop_words]
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple Jaccard similarity between two texts"""
        words1 = set(self._extract_keywords(text1))
        words2 = set(self._extract_keywords(text2))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / max(1, union)
    
    def _estimate_formality(self, text: str) -> float:
        """Estimate formality level (0=casual, 1=formal)"""
        text_lower = text.lower()
        
        formal_markers = [
            'furthermore', 'moreover', 'consequently', 'therefore',
            'however', 'nevertheless', 'additionally', 'specifically',
            'regarding', 'concerning', 'essential', 'significant'
        ]
        
        casual_markers = [
            'hey', 'hi there', 'yeah', 'yep', 'nope', 'cool',
            'awesome', 'totally', 'super', 'gonna', 'wanna',
            'btw', 'lol', 'omg', '!!'
        ]
        
        formal_count = sum(1 for m in formal_markers if m in text_lower)
        casual_count = sum(1 for m in casual_markers if m in text_lower)
        
        total = formal_count + casual_count
        if total == 0:
            return 0.5
        
        return formal_count / total
    
    def print_report(self, report: QualityReport):
        """Pretty-print a quality report"""
        print(f"\n{'='*60}")
        print(f"CONVERSATION QUALITY REPORT")
        print(f"Generated: {report.generated_at}")
        print(f"{'='*60}")
        
        print(f"\n  Conversations scored: {len(report.scores)}")
        print(f"  Flagged:             {report.flagged_count}")
        
        print(f"\n  Average Scores:")
        print(f"    Overall:       {report.avg_overall:.3f}")
        print(f"    Coherence:     {report.avg_coherence:.3f}")
        print(f"    Helpfulness:   {report.avg_helpfulness:.3f}")
        print(f"    Engagement:    {report.avg_engagement:.3f}")
        print(f"    Resolution:    {report.avg_resolution:.3f}")
        print(f"    Consistency:   {report.avg_consistency:.3f}")
        
        # Quality distribution
        if report.scores:
            excellent = sum(1 for s in report.scores if s.overall >= 0.8)
            good = sum(1 for s in report.scores if 0.6 <= s.overall < 0.8)
            fair = sum(1 for s in report.scores if 0.4 <= s.overall < 0.6)
            poor = sum(1 for s in report.scores if s.overall < 0.4)
            
            print(f"\n  Quality Distribution:")
            print(f"    Excellent (>=0.8): {excellent}")
            print(f"    Good (0.6-0.8):    {good}")
            print(f"    Fair (0.4-0.6):    {fair}")
            print(f"    Poor (<0.4):       {poor}")
        
        common = report.common_flags()
        if common:
            print(f"\n  Common Issues:")
            for flag, count in common:
                print(f"    {flag:35s} ({count}x)")
        
        # Show worst conversations
        worst = sorted(report.scores, key=lambda s: s.overall)[:3]
        if worst:
            print(f"\n  Lowest-Scoring Conversations:")
            for s in worst:
                print(f"    {s.session_id[:20]:20s} overall={s.overall:.3f} "
                      f"[C:{s.coherence:.2f} H:{s.helpfulness:.2f} E:{s.engagement:.2f}] "
                      f"flags={', '.join(s.flags[:3])}")


# ================================================================
# CLI
# ================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Conversation Quality Scorer')
    parser.add_argument('--db', default=None, help='Database path')
    parser.add_argument('--days', type=int, default=7, help='Score conversations from last N days')
    parser.add_argument('--limit', type=int, default=50, help='Max conversations to score')
    parser.add_argument('--session', default=None, help='Score a specific session ID')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    db = args.db or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'integrated_users.db'
    )
    
    scorer = ConversationQualityScorer(db)
    
    if args.session:
        score = scorer.score_conversation(args.session)
        if score:
            if args.json:
                print(json.dumps({
                    'session_id': score.session_id,
                    'overall': score.overall,
                    'coherence': score.coherence,
                    'helpfulness': score.helpfulness,
                    'engagement': score.engagement,
                    'resolution': score.resolution,
                    'consistency': score.consistency,
                    'flags': score.flags,
                    'details': score.details,
                }, indent=2))
            else:
                print(f"Session: {score.session_id}")
                print(f"Overall: {score.overall:.3f}")
                print(f"  Coherence:   {score.coherence:.3f}")
                print(f"  Helpfulness: {score.helpfulness:.3f}")
                print(f"  Engagement:  {score.engagement:.3f}")
                print(f"  Resolution:  {score.resolution:.3f}")
                print(f"  Consistency: {score.consistency:.3f}")
                if score.flags:
                    print(f"  Flags: {', '.join(score.flags)}")
        else:
            print("No scorable conversation found for that session.")
    else:
        report = scorer.score_recent(days=args.days, limit=args.limit)
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            scorer.print_report(report)


if __name__ == '__main__':
    main()

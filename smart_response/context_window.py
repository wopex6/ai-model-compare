"""
Enhanced Context Window Management
Provides better context management for AI conversations.
"""
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import json
import re


@dataclass
class ContextItem:
    """Single context item with metadata"""
    content: str
    source: str  # 'user', 'assistant', 'system', 'memory'
    importance: float  # 0-1, higher = more important
    timestamp: float
    tokens_estimate: int
    tags: List[str] = field(default_factory=list)


class ContextWindow:
    """
    Manages conversation context with intelligent pruning.
    
    Features:
    - Token-aware context management
    - Importance-based retention
    - Summarization of old context
    - Memory integration
    """
    
    MAX_TOKENS = 4000  # Maximum context tokens
    TOKENS_PER_CHAR = 0.25  # Rough estimate
    
    def __init__(self, max_tokens: int = None):
        self.max_tokens = max_tokens or self.MAX_TOKENS
        self._items: List[ContextItem] = []
        self._summaries: List[str] = []
        self._total_tokens = 0
    
    def add(self, content: str, source: str = 'user', 
            importance: float = 0.5, tags: List[str] = None) -> None:
        """Add item to context window"""
        tokens = self._estimate_tokens(content)
        
        item = ContextItem(
            content=content,
            source=source,
            importance=importance,
            timestamp=time.time(),
            tokens_estimate=tokens,
            tags=tags or []
        )
        
        self._items.append(item)
        self._total_tokens += tokens
        
        # Prune if over limit
        if self._total_tokens > self.max_tokens:
            self._prune()
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        return int(len(text) * self.TOKENS_PER_CHAR)
    
    def _prune(self) -> None:
        """Remove low-importance items to stay within token limit"""
        # Keep at least the last 5 messages
        if len(self._items) <= 5:
            return
        
        # Sort by importance (keep high importance)
        # But always keep recent messages
        now = time.time()
        
        def score(item: ContextItem) -> float:
            recency = max(0, 1 - (now - item.timestamp) / 3600)  # Decay over 1 hour
            return item.importance * 0.6 + recency * 0.4
        
        # Score all but last 3 messages
        scored = [(score(item), i, item) for i, item in enumerate(self._items[:-3])]
        scored.sort(key=lambda x: x[0])
        
        # Remove lowest scored items until under limit
        removed_tokens = 0
        remove_indices = []
        
        for score_val, idx, item in scored:
            if self._total_tokens - removed_tokens <= self.max_tokens * 0.8:
                break
            removed_tokens += item.tokens_estimate
            remove_indices.append(idx)
        
        # Create summary of removed content
        if remove_indices:
            removed_content = [self._items[i].content for i in remove_indices]
            summary = self._summarize(removed_content)
            if summary:
                self._summaries.append(summary)
        
        # Remove items (in reverse order to maintain indices)
        for idx in sorted(remove_indices, reverse=True):
            self._total_tokens -= self._items[idx].tokens_estimate
            del self._items[idx]
    
    def _summarize(self, contents: List[str]) -> str:
        """Create a brief summary of removed content"""
        if not contents:
            return ""
        
        # Simple summarization - extract key points
        combined = " ".join(contents)
        
        # Extract sentences with important keywords
        important_patterns = [
            r'(?:i want|i need|my goal|important|please|help)',
            r'(?:problem|issue|question|concern)',
            r'(?:decision|choose|option)',
        ]
        
        sentences = re.split(r'[.!?]+', combined)
        key_sentences = []
        
        for sentence in sentences[:10]:  # Check first 10
            sentence = sentence.strip()
            if len(sentence) > 20:
                for pattern in important_patterns:
                    if re.search(pattern, sentence.lower()):
                        key_sentences.append(sentence)
                        break
        
        if key_sentences:
            return "Earlier context: " + ". ".join(key_sentences[:3])
        return ""
    
    def get_context(self, include_summaries: bool = True) -> List[Dict]:
        """Get current context for AI prompt"""
        context = []
        
        # Add summaries first
        if include_summaries and self._summaries:
            context.append({
                'role': 'system',
                'content': "\n".join(self._summaries[-3:])  # Last 3 summaries
            })
        
        # Add current items
        for item in self._items:
            role = 'user' if item.source == 'user' else 'assistant'
            if item.source == 'system':
                role = 'system'
            
            context.append({
                'role': role,
                'content': item.content
            })
        
        return context
    
    def get_token_usage(self) -> Dict:
        """Get token usage statistics"""
        return {
            'current_tokens': self._total_tokens,
            'max_tokens': self.max_tokens,
            'usage_percent': round(self._total_tokens / self.max_tokens * 100, 1),
            'item_count': len(self._items),
            'summary_count': len(self._summaries)
        }
    
    def clear(self) -> None:
        """Clear context window"""
        self._items.clear()
        self._summaries.clear()
        self._total_tokens = 0


class MultiTurnMemory:
    """
    Long-term memory across conversation sessions.
    
    Features:
    - Key fact extraction
    - User preference tracking
    - Cross-session continuity
    """
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self._memory: Dict[int, Dict] = {}  # user_id -> memories
        self._init_db()
    
    def _init_db(self):
        """Initialize memory table"""
        if self.db:
            try:
                cursor = self.db.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_memories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        memory_type TEXT NOT NULL,
                        key TEXT NOT NULL,
                        value TEXT NOT NULL,
                        confidence REAL DEFAULT 1.0,
                        source TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, memory_type, key)
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_memories ON user_memories(user_id)')
                self.db.commit()
            except:
                pass
    
    def remember(self, user_id: int, memory_type: str, key: str, 
                 value: str, confidence: float = 1.0, source: str = None) -> None:
        """Store a memory about the user"""
        if self.db:
            try:
                cursor = self.db.cursor()
                cursor.execute('''
                    INSERT INTO user_memories (user_id, memory_type, key, value, confidence, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, memory_type, key) 
                    DO UPDATE SET value=?, confidence=?, updated_at=CURRENT_TIMESTAMP
                ''', (user_id, memory_type, key, value, confidence, source, value, confidence))
                self.db.commit()
            except Exception as e:
                print(f"Memory store error: {e}")
        
        # Also cache in memory
        if user_id not in self._memory:
            self._memory[user_id] = {}
        self._memory[user_id][f"{memory_type}:{key}"] = {
            'value': value,
            'confidence': confidence,
            'source': source
        }
    
    def recall(self, user_id: int, memory_type: str = None) -> Dict:
        """Recall memories about a user"""
        memories = {}
        
        if self.db:
            try:
                cursor = self.db.cursor()
                if memory_type:
                    cursor.execute('''
                        SELECT memory_type, key, value, confidence 
                        FROM user_memories 
                        WHERE user_id = ? AND memory_type = ?
                        ORDER BY updated_at DESC
                    ''', (user_id, memory_type))
                else:
                    cursor.execute('''
                        SELECT memory_type, key, value, confidence 
                        FROM user_memories 
                        WHERE user_id = ?
                        ORDER BY updated_at DESC
                    ''', (user_id,))
                
                for row in cursor.fetchall():
                    mtype, key, value, confidence = row
                    if mtype not in memories:
                        memories[mtype] = {}
                    memories[mtype][key] = {'value': value, 'confidence': confidence}
            except:
                pass
        
        return memories
    
    def forget(self, user_id: int, memory_type: str = None, key: str = None) -> int:
        """Remove memories"""
        count = 0
        if self.db:
            try:
                cursor = self.db.cursor()
                if key:
                    cursor.execute('''
                        DELETE FROM user_memories 
                        WHERE user_id = ? AND memory_type = ? AND key = ?
                    ''', (user_id, memory_type, key))
                elif memory_type:
                    cursor.execute('''
                        DELETE FROM user_memories 
                        WHERE user_id = ? AND memory_type = ?
                    ''', (user_id, memory_type))
                else:
                    cursor.execute('DELETE FROM user_memories WHERE user_id = ?', (user_id,))
                count = cursor.rowcount
                self.db.commit()
            except:
                pass
        
        return count
    
    def extract_facts(self, message: str) -> List[Tuple[str, str, str]]:
        """Extract memorable facts from a message"""
        facts = []
        message_lower = message.lower()
        
        # Preference patterns
        preference_patterns = [
            (r"i (?:really )?(?:like|love|enjoy|prefer) (.+?)(?:\.|,|$)", "preference", "likes"),
            (r"i (?:don't|do not|hate|dislike) (.+?)(?:\.|,|$)", "preference", "dislikes"),
            (r"my favorite (.+?) is (.+?)(?:\.|,|$)", "preference", "favorite"),
        ]
        
        # Personal info patterns
        personal_patterns = [
            (r"my name is (.+?)(?:\.|,|$)", "personal", "name"),
            (r"i(?:'m| am) (?:a |an )?(.+?) (?:by profession|professionally)", "personal", "profession"),
            (r"i work (?:as|at|in) (.+?)(?:\.|,|$)", "personal", "work"),
            (r"i live in (.+?)(?:\.|,|$)", "personal", "location"),
        ]
        
        # Goal patterns
        goal_patterns = [
            (r"my goal is to (.+?)(?:\.|,|$)", "goal", "current_goal"),
            (r"i want to (.+?)(?:\.|,|$)", "goal", "want"),
            (r"i(?:'m| am) trying to (.+?)(?:\.|,|$)", "goal", "trying"),
        ]
        
        all_patterns = preference_patterns + personal_patterns + goal_patterns
        
        for pattern, memory_type, key in all_patterns:
            match = re.search(pattern, message_lower)
            if match:
                value = match.group(1).strip()
                if len(value) > 2 and len(value) < 100:
                    facts.append((memory_type, key, value))
        
        return facts


class CharacterSwitcher:
    """
    Manages dynamic character switching based on conversation context.
    
    Features:
    - Context-aware character recommendation
    - Smooth transition handling
    - Character effectiveness tracking
    """
    
    # Character traits for matching
    CHARACTER_TRAITS = {
        'life_coach': {
            'domains': ['goals', 'motivation', 'productivity', 'habits'],
            'emotional_states': ['unmotivated', 'stuck', 'ambitious'],
            'keywords': ['goal', 'achieve', 'success', 'habit', 'routine', 'motivation']
        },
        'psychologist': {
            'domains': ['emotions', 'relationships', 'mental_health', 'self_understanding'],
            'emotional_states': ['anxious', 'depressed', 'confused', 'stressed'],
            'keywords': ['feel', 'anxiety', 'depression', 'relationship', 'therapy', 'emotion']
        },
        'stoic_philosopher': {
            'domains': ['philosophy', 'resilience', 'perspective', 'acceptance'],
            'emotional_states': ['frustrated', 'angry', 'overwhelmed'],
            'keywords': ['stoic', 'accept', 'control', 'virtue', 'wisdom', 'philosophy']
        },
        'career_mentor': {
            'domains': ['career', 'work', 'professional', 'business'],
            'emotional_states': ['uncertain', 'ambitious'],
            'keywords': ['job', 'career', 'work', 'boss', 'promotion', 'salary', 'interview']
        },
        'spiritual_guide': {
            'domains': ['spirituality', 'meaning', 'purpose', 'meditation'],
            'emotional_states': ['lost', 'searching', 'peaceful'],
            'keywords': ['meaning', 'purpose', 'meditation', 'spiritual', 'soul', 'peace']
        },
        'health_coach': {
            'domains': ['health', 'fitness', 'nutrition', 'wellness'],
            'emotional_states': ['tired', 'unhealthy'],
            'keywords': ['health', 'exercise', 'diet', 'sleep', 'fitness', 'weight', 'energy']
        },
        'financial_advisor': {
            'domains': ['money', 'finance', 'investing', 'budgeting'],
            'emotional_states': ['worried', 'planning'],
            'keywords': ['money', 'budget', 'invest', 'save', 'debt', 'financial', 'retire']
        },
        'creative_muse': {
            'domains': ['creativity', 'art', 'writing', 'innovation'],
            'emotional_states': ['inspired', 'blocked', 'creative'],
            'keywords': ['create', 'art', 'write', 'idea', 'creative', 'inspiration', 'design']
        }
    }
    
    def suggest_character(self, message: str, current_character: str = None,
                         user_context: Dict = None) -> Tuple[str, float, str]:
        """
        Suggest best character for the current message.
        
        Returns:
            (character_id, confidence, reason)
        """
        message_lower = message.lower()
        scores = {}
        
        for char_id, traits in self.CHARACTER_TRAITS.items():
            score = 0
            
            # Keyword matching
            for keyword in traits['keywords']:
                if keyword in message_lower:
                    score += 1
            
            # Normalize by keyword count
            if traits['keywords']:
                score = score / len(traits['keywords'])
            
            scores[char_id] = score
        
        # Get top character
        if scores:
            best = max(scores.items(), key=lambda x: x[1])
            char_id, confidence = best
            
            # Only suggest switch if confidence is high enough
            if confidence > 0.2 and char_id != current_character:
                reason = f"Your message seems related to {char_id.replace('_', ' ')}'s expertise"
                return char_id, confidence, reason
        
        return current_character or 'life_coach', 0.0, "Continuing with current character"
    
    def get_transition_prompt(self, from_char: str, to_char: str) -> str:
        """Generate smooth transition message"""
        transitions = {
            'psychologist': "I sense this touches on deeper emotional aspects. Let me approach this with more psychological insight.",
            'stoic_philosopher': "This situation calls for a stoic perspective. Let me share some timeless wisdom.",
            'career_mentor': "This is really a career matter. Let me put on my professional advisor hat.",
            'spiritual_guide': "There's a deeper meaning here. Let me explore this with you spiritually.",
            'health_coach': "Your wellbeing is at the core of this. Let's focus on your health.",
            'financial_advisor': "Money matters require careful thought. Let me help you think this through financially.",
            'creative_muse': "This calls for creative thinking! Let's explore possibilities.",
        }
        
        return transitions.get(to_char, f"Let me approach this from the perspective of a {to_char.replace('_', ' ')}.")


# Factory functions
def create_context_window(max_tokens: int = None) -> ContextWindow:
    return ContextWindow(max_tokens)


def create_multi_turn_memory(db_connection=None) -> MultiTurnMemory:
    return MultiTurnMemory(db_connection)


def create_character_switcher() -> CharacterSwitcher:
    return CharacterSwitcher()

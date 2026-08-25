# AI Life Companion - Architecture Overview
 
> Technical architecture for the multi-character coordinator system
 
**Last Updated:** June 26, 2026  
**Version:** 2.0  
**Status:** Production Ready

---

## Table of Contents
 
1. [System Architecture](#system-architecture)
2. [Character System](#character-system)
3. [Context Engine](#context-engine)
4. [User Context & Personalization Layer](#user-context--personalization-layer)
5. [Prompt Construction, Context Window, and Token Monitoring](#prompt-construction-context-window-and-token-monitoring)
6. [AI Summarization (Throttled)](#ai-summarization-throttled)
7. [Proactive Clarification System](#proactive-clarification-system)
8. [Character Trait System (12D Matching)](#character-trait-system-12d-matching)
9. [Roles & Privileges (Admin vs Developer)](#roles--privileges-admin-vs-developer)
10. [Developer Analytics APIs](#developer-analytics-apis)
11. [Threshold & Activation System](#threshold--activation-system)
12. [Notification System](#notification-system)
13. [Feedback Loop System](#feedback-loop-system)
14. [Database Schema](#database-schema)
15. [Testing Guide (How to Feel It Working)](#testing-guide-how-to-feel-it-working)
16. [Implementation Guide](#implementation-guide)

---

## 🚀 **2026 IMPLEMENTATION STATUS**

### **Production-Ready Components**

#### ✅ **Core Intelligence Layer (COMPLETE)**
- **PersonalityAwareContextInterpreter** - Interprets events through personality lens
- **DualLayerHistorySystem** - Raw data + analytical interpretation
- **AIBudgetManager** - Cost control with circuit breaker protection
- **ExplicitContextHandler** - User statements with CRITICAL priority
- **ProactiveClarificationSystem** - Question generation when uncertain

#### ✅ **Character System (COMPLETE)**
- **CharacterTraitSystem** - 12-dimensional trait vectors
- **Dynamic Character Matching** - Situation-based selection
- **CharacterExpansionSystem** - AI-powered character generation
- **CharacterEffectivenessLearner** - Outcome-based optimization
- **Character Collaboration** - Multi-character coordination

#### ✅ **Smart Response System (COMPLETE)**
- **Centralized Handler** - Response management and routing
- **Multi-Provider Support** - OpenAI, Anthropic, fallbacks
- **Context Window Management** - Efficient token usage
- **Response Need Classification** - Categorize user requirements
- **Format Preference Detection** - Adapt to user communication style

#### ✅ **User Management (COMPLETE)**
- **Multi-User Authentication** - JWT-based secure sessions
- **Role-Based Access Control** - guest, user, paid, admin, developer
- **User Analytics** - Comprehensive usage tracking
- **Admin Dashboard** - Real-time metrics and controls

#### ✅ **Advanced Features (COMPLETE)**
- **Avatar System** - Interactive SVG avatars with expressions
- **File Upload System** - Video, audio, image support (50MB limit)
- **Admin Chat System** - Real-time admin-user communication
- **Background Tasks** - Scheduled maintenance and analysis
- **Notification System** - Budget warnings and system alerts

### **System Metrics**
- **Python Files:** 65+ modules in smart_response/
- **Documentation:** 100+ comprehensive markdown files
- **Database Tables:** 15+ implemented schemas
- **API Endpoints:** 50+ documented and functional
- **Test Coverage:** Comprehensive automated testing

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      ConversationBox Module                          │    │
│  │  - Unified message interface for all characters                      │    │
│  │  - Style adaptation per character                                    │    │
│  │  - Multi-response aggregation                                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Notification UI                                 │    │
│  │  - Desktop real-time notifications                                   │    │
│  │  - Auto-integration into conversation                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              APPLICATION LAYER                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Character Router                                │    │
│  │  - Routes messages to appropriate characters                         │    │
│  │  - Manages threshold-based activation                                │    │
│  │  - Handles coordinator fallback                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Character Manager                               │    │
│  │  - Manages all character instances                                   │    │
│  │  - Handles character-to-character communication                      │    │
│  │  - Orchestrates multi-character responses                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Proactive Engine                                │    │
│  │  - Monitors for proactive opportunities                              │    │
│  │  - Triggers notifications and check-ins                              │    │
│  │  - Manages engagement timing                                         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INTELLIGENCE LAYER                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Context Engine                                  │    │
│  │  - Flexible context storage                                          │    │
│  │  - Dynamic context matching                                          │    │
│  │  - Per-character interpretation                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Threshold Calculator                            │    │
│  │  - Calculates concern levels per character                           │    │
│  │  - Determines which characters should respond                        │    │
│  │  - Adaptive thresholds based on feedback                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Feedback Processor                              │    │
│  │  - Processes explicit, implicit, and direct feedback                 │    │
│  │  - Updates character behavior                                        │    │
│  │  - Improves context matching                                         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Shared Context Store                            │    │
│  │  - Full sharing: All characters see all data                         │    │
│  │  - Multi-year retention                                              │    │
│  │  - Character interpretations stored separately                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      User Data Store                                 │    │
│  │  - User profiles and preferences                                     │    │
│  │  - Feedback history                                                  │    │
│  │  - Notification preferences                                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Character System

### Character Types

#### 1. Philosophy/Approach Characters (Existing)

These provide different philosophical perspectives on any topic:

```python
PHILOSOPHY_CHARACTERS = {
    "super_motivational_coach": {
        "display_name": "Coach Max",
        "approach": "High-energy motivation",
        "perspective": "You can do anything!"
    },
    "wisdom_sage": {
        "display_name": "Sage Wei",
        "approach": "Ancient wisdom",
        "perspective": "What does tradition teach?"
    },
    "stoic_philosopher": {
        "display_name": "Marcus",
        "approach": "Stoic philosophy",
        "perspective": "What can you control?"
    },
    "psychologist": {
        "display_name": "Dr. Elena",
        "approach": "Psychology",
        "perspective": "What patterns exist?"
    },
    "zen_master": {
        "display_name": "Master Kai",
        "approach": "Zen mindfulness",
        "perspective": "What is, simply is"
    },
    "business_coach": {
        "display_name": "Coach Ryan",
        "approach": "Business strategy",
        "perspective": "What's the ROI?"
    },
    "life_coach": {
        "display_name": "Coach Jordan",
        "approach": "Life coaching",
        "perspective": "What do you truly want?"
    },
    "scientist": {
        "display_name": "Dr. Nova",
        "approach": "Scientific thinking",
        "perspective": "What does evidence show?"
    }
}
```

#### 2. Domain Characters (New)

These specialize in specific life areas:

```python
DOMAIN_CHARACTERS = {
    "coordinator": {
        "display_name": "Aria",  # or user-chosen name
        "domain": "all",
        "role": "Synthesizes insights from all domains",
        "special_privileges": [
            "can_see_all_conversations",
            "can_request_domain_input",
            "can_synthesize_multi_domain"
        ]
    },
    "domain_work": {
        "display_name": "Work Advisor",
        "domain": "work",
        "focus_areas": ["career", "productivity", "decisions", "growth", "workplace"]
    },
    "domain_relationships": {
        "display_name": "Relationship Guide",
        "domain": "relationships",
        "focus_areas": ["family", "friends", "romantic", "social", "communication"]
    },
    "domain_mental_health": {
        "display_name": "Mind Wellness",
        "domain": "mental_health",
        "focus_areas": ["emotions", "stress", "anxiety", "mindfulness", "self-care"]
    },
    "domain_physical_health": {
        "display_name": "Body Advisor",
        "domain": "physical_health",
        "focus_areas": ["fitness", "nutrition", "sleep", "energy", "habits"]
    },
    "domain_finance": {
        "display_name": "Finance Guide",
        "domain": "finance",
        "focus_areas": ["budgeting", "investing", "decisions", "planning", "goals"]
    },
    "domain_learning": {
        "display_name": "Learning Mentor",
        "domain": "learning",
        "focus_areas": ["skills", "education", "curiosity", "knowledge", "growth"]
    },
    "domain_creativity": {
        "display_name": "Creative Muse",
        "domain": "creativity",
        "focus_areas": ["art", "hobbies", "expression", "innovation", "play"]
    }
}
```

### Character Base Classes

```python
# smart_response/characters/base.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class CharacterResponse:
    """Response from a character"""
    character_id: str
    content: str
    concern_level: float  # 0.0 to 1.0
    interpretation: Dict[str, Any]
    should_display: bool  # Based on threshold
    metadata: Dict[str, Any]

class BaseCharacter(ABC):
    """Base class for all characters"""
    
    def __init__(self, character_id: str, config: Dict):
        self.character_id = character_id
        self.config = config
        self.display_name = config.get("display_name", character_id)
    
    @abstractmethod
    def analyze_context(self, message: str, context: Dict) -> float:
        """Analyze message and return concern level (0.0 to 1.0)"""
        pass
    
    @abstractmethod
    def generate_response(self, message: str, context: Dict) -> CharacterResponse:
        """Generate a response to the message"""
        pass
    
    @abstractmethod
    def interpret_context(self, context: Dict) -> Dict:
        """Generate this character's interpretation of the context"""
        pass
    
    def should_respond(self, concern_level: float, threshold: float = 0.7) -> bool:
        """Determine if character should respond based on threshold"""
        return concern_level >= threshold


class DomainCharacter(BaseCharacter):
    """Base class for domain-specific characters"""
    
    def __init__(self, character_id: str, config: Dict):
        super().__init__(character_id, config)
        self.domain = config.get("domain", "general")
        self.focus_areas = config.get("focus_areas", [])
    
    def is_domain_relevant(self, message: str, context: Dict) -> bool:
        """Check if message is relevant to this domain"""
        # Implement domain-specific relevance checking
        pass


class CoordinatorCharacter(BaseCharacter):
    """Special coordinator character"""
    
    def __init__(self, character_id: str, config: Dict, character_manager):
        super().__init__(character_id, config)
        self.character_manager = character_manager
    
    def synthesize_perspectives(self, responses: List[CharacterResponse]) -> str:
        """Synthesize multiple character perspectives into unified view"""
        pass
    
    def request_domain_input(self, domain: str, message: str, context: Dict) -> CharacterResponse:
        """Request input from a specific domain character"""
        pass
```

### Character Manager

```python
# smart_response/characters/manager.py

from typing import Dict, List, Optional
from .base import BaseCharacter, CharacterResponse, DomainCharacter, CoordinatorCharacter

class CharacterManager:
    """Manages all characters and coordinates their responses"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.characters: Dict[str, BaseCharacter] = {}
        self.coordinator: Optional[CoordinatorCharacter] = None
        self._load_characters()
    
    def _load_characters(self):
        """Load all character instances"""
        # Load philosophy characters
        for char_id, config in PHILOSOPHY_CHARACTERS.items():
            self.characters[char_id] = self._create_philosophy_character(char_id, config)
        
        # Load domain characters
        for char_id, config in DOMAIN_CHARACTERS.items():
            if char_id == "coordinator":
                self.coordinator = CoordinatorCharacter(char_id, config, self)
                self.characters[char_id] = self.coordinator
            else:
                self.characters[char_id] = DomainCharacter(char_id, config)
    
    def route_message(self, message: str, context: Dict, 
                      requested_character: Optional[str] = None) -> List[CharacterResponse]:
        """
        Route message to appropriate characters
        
        Rules:
        1. If user requests specific character -> that character responds
        2. Characters above threshold respond (critical concern)
        3. If no one responds -> coordinator synthesizes or requests domain input
        4. Others remain silent observers (store interpretation)
        """
        responses = []
        
        # Rule 1: User requested specific character
        if requested_character and requested_character in self.characters:
            response = self.characters[requested_character].generate_response(message, context)
            response.should_display = True
            responses.append(response)
            return responses
        
        # Rule 2: Check all characters for threshold triggers
        for char_id, character in self.characters.items():
            concern_level = character.analyze_context(message, context)
            
            if character.should_respond(concern_level):
                response = character.generate_response(message, context)
                response.should_display = True
                responses.append(response)
            else:
                # Silent observer - store interpretation
                interpretation = character.interpret_context(context)
                self._store_interpretation(char_id, context, interpretation, concern_level)
        
        # Rule 3: If no responses, coordinator handles
        if not responses and self.coordinator:
            response = self.coordinator.generate_response(message, context)
            response.should_display = True
            responses.append(response)
        
        return responses
    
    def _store_interpretation(self, char_id: str, context: Dict, 
                             interpretation: Dict, concern_level: float):
        """Store character's interpretation even if not responding"""
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO character_interpretations 
            (primary_history_id, character_id, interpretation, concern_level)
            VALUES (?, ?, ?, ?)
        ''', (context.get('history_id'), char_id, 
              json.dumps(interpretation), concern_level))
        self.db.commit()
    
    def get_all_interpretations(self, history_id: int) -> Dict[str, Dict]:
        """Get all character interpretations for a conversation"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT character_id, interpretation, concern_level
            FROM character_interpretations
            WHERE primary_history_id = ?
        ''', (history_id,))
        
        return {
            row[0]: {
                'interpretation': json.loads(row[1]),
                'concern_level': row[2]
            }
            for row in cursor.fetchall()
        }
```

---

## Context Engine

### Flexible Context Storage

```python
# smart_response/context/engine.py

from typing import Dict, List, Any, Optional
from datetime import datetime
import json

class ContextEngine:
    """
    Flexible context storage and dynamic matching.
    
    Key Principles:
    - Same information can be interpreted differently by different characters/users
    - Context is stored flexibly (JSON-based)
    - Matching is dynamic based on current situation
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def store_context(self, user_id: int, context_type: str, 
                     context_data: Dict, source: str = "conversation"):
        """
        Store flexible context data
        
        Args:
            user_id: User ID
            context_type: Type of context (goal, emotion, event, preference, etc.)
            context_data: Flexible JSON data
            source: Where this context came from
        """
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO flexible_context 
            (user_id, context_type, context_data, source, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, context_type, json.dumps(context_data), 
              source, datetime.now()))
        self.db.commit()
        return cursor.lastrowid
    
    def get_relevant_context(self, user_id: int, message: str,
                            character_id: Optional[str] = None) -> Dict:
        """
        Dynamically match and retrieve relevant context
        
        The matching considers:
        - Message content and intent
        - Character's perspective (if specified)
        - Recency and relevance scoring
        """
        # Get all user context
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT id, context_type, context_data, source, created_at
            FROM flexible_context
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1000
        ''', (user_id,))
        
        all_context = cursor.fetchall()
        
        # Dynamic matching based on message
        relevant = self._match_context(message, all_context, character_id)
        
        return {
            'matched_contexts': relevant,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }
    
    def _match_context(self, message: str, contexts: List, 
                       character_id: Optional[str]) -> List[Dict]:
        """
        Dynamic context matching algorithm
        
        Factors:
        - Keyword relevance
        - Semantic similarity (future: embeddings)
        - Recency weighting
        - Character perspective weighting
        """
        matched = []
        
        for ctx in contexts:
            ctx_id, ctx_type, ctx_data_str, source, created_at = ctx
            ctx_data = json.loads(ctx_data_str)
            
            # Calculate relevance score
            score = self._calculate_relevance(
                message, ctx_type, ctx_data, created_at, character_id
            )
            
            if score > 0.3:  # Minimum relevance threshold
                matched.append({
                    'id': ctx_id,
                    'type': ctx_type,
                    'data': ctx_data,
                    'source': source,
                    'relevance_score': score,
                    'created_at': created_at
                })
        
        # Sort by relevance
        matched.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return matched[:20]  # Top 20 most relevant
    
    def _calculate_relevance(self, message: str, ctx_type: str,
                            ctx_data: Dict, created_at: datetime,
                            character_id: Optional[str]) -> float:
        """Calculate relevance score for a context item"""
        score = 0.0
        
        # Keyword matching (simple for now, can add embeddings later)
        message_lower = message.lower()
        ctx_text = json.dumps(ctx_data).lower()
        
        # Check for keyword overlap
        message_words = set(message_lower.split())
        ctx_words = set(ctx_text.split())
        overlap = len(message_words & ctx_words)
        if overlap > 0:
            score += min(overlap * 0.1, 0.5)
        
        # Recency boost
        days_old = (datetime.now() - created_at).days if created_at else 0
        recency_factor = max(0, 1 - (days_old / 365))  # Decay over a year
        score += recency_factor * 0.3
        
        # Context type relevance (can be character-specific)
        if character_id:
            type_relevance = self._get_type_relevance(ctx_type, character_id)
            score += type_relevance * 0.2
        
        return min(score, 1.0)
    
    def _get_type_relevance(self, ctx_type: str, character_id: str) -> float:
        """Get how relevant a context type is to a specific character"""
        # Domain character relevance mapping
        relevance_map = {
            "domain_work": {"career": 1.0, "productivity": 1.0, "goal": 0.8},
            "domain_relationships": {"relationship": 1.0, "family": 1.0, "emotion": 0.8},
            "domain_mental_health": {"emotion": 1.0, "stress": 1.0, "mood": 1.0},
            "domain_physical_health": {"health": 1.0, "fitness": 1.0, "sleep": 1.0},
            "domain_finance": {"finance": 1.0, "budget": 1.0, "goal": 0.6},
            "domain_learning": {"learning": 1.0, "skill": 1.0, "education": 1.0},
            "domain_creativity": {"creative": 1.0, "hobby": 1.0, "art": 1.0},
            "coordinator": {"all": 0.8}  # Coordinator finds all types relevant
        }
        
        char_map = relevance_map.get(character_id, {})
        return char_map.get(ctx_type, 0.5)
    
    def store_character_interpretation(self, context_id: int, character_id: str,
                                       interpretation: Dict):
        """Store how a character interprets a piece of context"""
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO context_interpretations
            (context_id, character_id, interpretation, created_at)
            VALUES (?, ?, ?, ?)
        ''', (context_id, character_id, json.dumps(interpretation), datetime.now()))
        self.db.commit()
```

---

## User Context & Personalization Layer

The system includes a dedicated user context management subsystem designed to:

- **Always-on extraction (rule-based)** on every user message (low cost, deterministic)
- **Throttled AI summarization** for deeper, compact context (higher cost, controlled)
- **User language learning** (capture and re-use user phrasing/tone preferences)
- **Engagement tracking** (signals and lightweight metrics)

### Key Files

- `smart_response/user_context_manager.py`
- `app.py` (integration in `/api/domain-characters/route`)
- `smart_response/characters/ai_integration.py` (system prompt injection)
- `smart_response/ai_budget_manager.py` (budget gating + usage logging)

### Runtime Integration (Current Wiring)

In `app.py`, the `/api/domain-characters/route` endpoint runs this pipeline:

- Store the raw user message first to create a stable `history_id`.
- Call `user_context_mgr.process_message(..., message_id=history_id)`.
- Merge returned fields into the shared `context` dict.
- Set `context['user_profile']` to `user_context_mgr.format_context_for_prompt(...)`.

Observable runtime logs:

- `[USER_CONTEXT] Added user profile for AI`
- `[USER_CONTEXT] User references past conversation - expanding context`

### What Gets Extracted (Rule-Based)

- preferences
- goals
- emotions
- stable user facts (e.g., name preference)
- language patterns (greeting, sign-off, emphasis words, message length)
- references to past conversation

### Prompt-Level Personalization (“Mirror User Language”)

The formatted user profile includes explicit instructions to mirror:

- greeting style
- brevity/detailed preference
- sign-off style
- emphasis words

---

## Prompt Construction, Context Window, and Token Monitoring

### Configurable History Window

The number of prior exchanges included for AI context is controlled by:

- `AI_CONTEXT_EXCHANGES` (default `5`)

When the user references past conversation, the system expands the window:

- `context_exchanges = base_exchanges * 2`

### Token Estimation Logging

The system estimates history tokens with:

- `len(text) // 4` (approximate)

Logged as:

- `[CONTEXT] Added N history messages (~X tokens)`

---

## AI Summarization (Throttled)

The system generates a compact conversation summary using AI, but only when needed.

### Trigger Policy

A summary refresh can be requested when:

- message count crosses a threshold (default policy: every ~8 user messages)
- the user references past conversation
- the existing summary is stale

### Budget Control & Logging

Summarization is treated as a **background AI call** and is budget-gated via `AIBudgetManager`.

The system logs summary calls to `ai_usage_log` with:

- `purpose = 'conversation_summary'`
- `is_background = 1`

Summaries are stored per `(user_id, character_id)` in `conversation_summaries`.

---

## Proactive Clarification System

The proactive clarification subsystem detects uncertainty and suggests up to **2** clarifying questions.

Key file:

- `smart_response/proactive_clarification.py`

Database tables:

- `clarification_history`
- `context_gaps`

### Runtime Integration Status

This system is **initialized in `app.py`** but is not yet injected into the assistant response pipeline.

Current state:

- Implemented: confidence scoring, question generation (max 2), DB persistence, formatting
- Available for manual testing: `python demo_features.py`

---

## Character Trait System (12D Matching)

The trait system provides a continuous “trait space” for matching situations to characters.

Key file:

- `smart_response/character_traits.py`

Tables:

- `character_library`
- `character_usage_outcomes`
- `situation_analysis_cache`

### Runtime Integration Status

This system is **initialized in `app.py`** but is not yet used to override routing in the main chat flow.

Current state:

- Implemented: situation analysis + matching + effectiveness learning tables
- Available for manual testing: `python demo_features.py`

---

## Roles & Privileges (Admin vs Developer)

The `users.user_role` field controls access.

Roles include:

- `guest`
- `user`
- `paid`
- `administrator`
- `developer`

Admin can change user roles via:

- `POST /api/admin/users/<user_id>/role`

Developer-only endpoints require `user_role == 'developer'`.

---

## Developer Analytics APIs

Developer-only endpoints provide deeper observability and research tools.

Endpoints:

- `GET /api/developer/metrics`
- `GET /api/developer/ai-calls`
- `GET /api/developer/user-context`
- `GET /api/developer/character-effectiveness`
- `GET /api/developer/clarification-stats`
- `GET /api/developer/export/<table>`
- `POST /api/developer/query` (SELECT-only)
- `GET /api/developer/debug`
- `POST /api/developer/health-snapshot`
- `GET /api/developer/health-history`
- `GET /api/developer/access-log`

All developer access is recorded in `developer_access_log`.

---

## Testing Guide (How to Feel It Working)

### A. Live UI Test (User Context + Summaries + Token Logs)

Send a signal-rich message (example):

- call me Alex
- I prefer brief answers
- I'm feeling stressed about work
- my goal is to save money

Expected logs:

- `[USER_CONTEXT] Added user profile for AI`
- `[CONTEXT] Added ... history messages (~... tokens)`
- `[SUMMARY] Generated conversation summary` (after summary triggers)

Expected DB writes:

- `user_context`
- `user_language_patterns`
- `user_engagement`
- `conversation_summaries`
- `ai_usage_log` (summary purpose)

### B. Scripted Demo (All New Systems)

Run:

- `python demo_features.py`

This demonstrates:

- language extraction + prompt mirroring output
- clarification confidence + up to 2 questions
- 12D trait matching
- developer analytics metrics gathering

---

## Threshold & Activation System

### Threshold Calculator

```python
# smart_response/threshold/calculator.py

from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ThresholdConfig:
    """Configuration for a character's activation threshold"""
    base_threshold: float = 0.7
    domain_keywords: List[str] = None
    emotional_triggers: List[str] = None
    urgency_multiplier: float = 1.0
    user_preference_weight: float = 0.2

class ThresholdCalculator:
    """
    Calculates whether a character should respond based on context
    
    A character responds when:
    1. User explicitly requests them
    2. Concern level exceeds threshold (critical to their domain)
    3. Coordinator requests their input (no other responders)
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.configs: Dict[str, ThresholdConfig] = self._load_configs()
    
    def _load_configs(self) -> Dict[str, ThresholdConfig]:
        """Load threshold configurations for all characters"""
        return {
            "domain_work": ThresholdConfig(
                base_threshold=0.7,
                domain_keywords=["job", "career", "work", "boss", "promotion", 
                                "deadline", "project", "colleague", "salary"],
                emotional_triggers=["stressed about work", "hate my job", "fired"],
                urgency_multiplier=1.2
            ),
            "domain_relationships": ThresholdConfig(
                base_threshold=0.7,
                domain_keywords=["relationship", "partner", "family", "friend", 
                                "marriage", "divorce", "dating", "lonely"],
                emotional_triggers=["breakup", "fight", "hurt", "betrayed"],
                urgency_multiplier=1.3
            ),
            "domain_mental_health": ThresholdConfig(
                base_threshold=0.6,  # Lower threshold - mental health is critical
                domain_keywords=["anxious", "depressed", "stressed", "overwhelmed",
                                "panic", "worried", "sad", "hopeless"],
                emotional_triggers=["suicidal", "self-harm", "can't cope", "breaking down"],
                urgency_multiplier=1.5
            ),
            "domain_physical_health": ThresholdConfig(
                base_threshold=0.7,
                domain_keywords=["health", "sick", "pain", "tired", "exercise",
                                "diet", "sleep", "weight", "fitness"],
                emotional_triggers=["chronic pain", "can't sleep", "exhausted"],
                urgency_multiplier=1.1
            ),
            "domain_finance": ThresholdConfig(
                base_threshold=0.7,
                domain_keywords=["money", "budget", "debt", "savings", "invest",
                                "salary", "expenses", "financial", "afford"],
                emotional_triggers=["broke", "bankruptcy", "can't pay", "debt crisis"],
                urgency_multiplier=1.2
            ),
            "domain_learning": ThresholdConfig(
                base_threshold=0.7,
                domain_keywords=["learn", "study", "course", "skill", "education",
                                "knowledge", "training", "certification"],
                emotional_triggers=["failing", "can't understand", "stuck"],
                urgency_multiplier=1.0
            ),
            "domain_creativity": ThresholdConfig(
                base_threshold=0.7,
                domain_keywords=["creative", "art", "hobby", "music", "writing",
                                "design", "craft", "inspiration"],
                emotional_triggers=["blocked", "no inspiration", "lost creativity"],
                urgency_multiplier=1.0
            ),
            "coordinator": ThresholdConfig(
                base_threshold=0.5,  # Coordinator has lower threshold
                domain_keywords=[],  # Responds to everything
                urgency_multiplier=1.0
            )
        }
    
    def calculate_concern_level(self, character_id: str, message: str,
                                context: Dict) -> float:
        """
        Calculate how concerned a character is about this message
        
        Returns: 0.0 (not concerned) to 1.0 (highly concerned)
        """
        config = self.configs.get(character_id, ThresholdConfig())
        
        concern = 0.0
        message_lower = message.lower()
        
        # Check domain keywords
        keyword_matches = sum(1 for kw in (config.domain_keywords or []) 
                             if kw in message_lower)
        if keyword_matches > 0:
            concern += min(keyword_matches * 0.15, 0.5)
        
        # Check emotional triggers (high priority)
        trigger_matches = sum(1 for trigger in (config.emotional_triggers or [])
                             if trigger in message_lower)
        if trigger_matches > 0:
            concern += min(trigger_matches * 0.3, 0.6)
        
        # Apply urgency multiplier
        concern *= config.urgency_multiplier
        
        # Factor in user preferences (from feedback history)
        user_preference = self._get_user_preference(
            context.get('user_id'), character_id
        )
        concern += user_preference * config.user_preference_weight
        
        return min(concern, 1.0)
    
    def should_respond(self, character_id: str, concern_level: float) -> bool:
        """Determine if character should respond based on concern level"""
        config = self.configs.get(character_id, ThresholdConfig())
        return concern_level >= config.base_threshold
    
    def _get_user_preference(self, user_id: int, character_id: str) -> float:
        """Get user's preference weight for this character (from feedback)"""
        if not user_id:
            return 0.0
        
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT AVG(CASE 
                WHEN feedback_value = 'positive' THEN 1.0
                WHEN feedback_value = 'negative' THEN -0.5
                ELSE 0.0
            END) as preference
            FROM user_feedback
            WHERE user_id = ? AND character_id = ?
            AND timestamp > datetime('now', '-30 days')
        ''', (user_id, character_id))
        
        result = cursor.fetchone()
        return result[0] if result and result[0] else 0.0
    
    def adapt_threshold(self, character_id: str, user_id: int, 
                       feedback: str, adjustment: float = 0.05):
        """Adapt threshold based on user feedback"""
        # Store adaptation in database for this user-character pair
        pass  # Implementation for adaptive thresholds
```

---

## Notification System

### Desktop Notification Manager

```python
# smart_response/notifications/manager.py

from typing import Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass
import json

@dataclass
class Notification:
    """A notification to be sent to the user"""
    id: int
    user_id: int
    character_id: str
    notification_type: str  # check_in, insight, reminder, alert
    title: str
    message: str
    priority: str  # low, medium, high, critical
    conversation_context: Optional[Dict] = None
    created_at: datetime = None
    delivered_at: datetime = None
    acknowledged_at: datetime = None

class NotificationManager:
    """
    Manages proactive notifications to users
    
    Features:
    - Desktop real-time notifications
    - Auto-integration into conversations
    - User preference respect
    """
    
    def __init__(self, db_connection, websocket_manager=None):
        self.db = db_connection
        self.ws_manager = websocket_manager
    
    def create_notification(self, user_id: int, character_id: str,
                           notification_type: str, title: str, message: str,
                           priority: str = "medium",
                           conversation_context: Dict = None) -> Notification:
        """Create and queue a notification"""
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO notifications 
            (user_id, character_id, notification_type, title, message, 
             priority, conversation_context, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, character_id, notification_type, title, message,
              priority, json.dumps(conversation_context) if conversation_context else None,
              datetime.now()))
        self.db.commit()
        
        notification = Notification(
            id=cursor.lastrowid,
            user_id=user_id,
            character_id=character_id,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            conversation_context=conversation_context,
            created_at=datetime.now()
        )
        
        # Send real-time if websocket available
        if self.ws_manager:
            self._send_realtime(notification)
        
        return notification
    
    def _send_realtime(self, notification: Notification):
        """Send real-time desktop notification via WebSocket"""
        payload = {
            'type': 'notification',
            'data': {
                'id': notification.id,
                'character_id': notification.character_id,
                'notification_type': notification.notification_type,
                'title': notification.title,
                'message': notification.message,
                'priority': notification.priority,
                'timestamp': notification.created_at.isoformat()
            }
        }
        self.ws_manager.send_to_user(notification.user_id, payload)
    
    def add_to_conversation(self, notification_id: int, user_id: int,
                           character_id: str):
        """
        Add notification to conversation history
        (Notifications automatically appear in chat)
        """
        cursor = self.db.cursor()
        
        # Get notification details
        cursor.execute('SELECT title, message FROM notifications WHERE id = ?', 
                       (notification_id,))
        notif = cursor.fetchone()
        
        if notif:
            title, message = notif
            # Add to conversation as system message from character
            cursor.execute('''
                INSERT INTO history_primary 
                (user_id, character, user_message, ai_response, 
                 session_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, character_id, 
                  "[Proactive Check-in]",  # Marker for proactive message
                  f"**{title}**\n\n{message}",
                  f"notification_{notification_id}",
                  json.dumps({'notification_id': notification_id, 
                             'is_proactive': True})))
            self.db.commit()
    
    def get_user_preferences(self, user_id: int) -> Dict:
        """Get user's notification preferences"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT preferences FROM user_notification_preferences
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        if result:
            return json.loads(result[0])
        
        # Default preferences
        return {
            'desktop_enabled': True,
            'check_in_frequency': 'daily',
            'quiet_hours': {'start': '22:00', 'end': '08:00'},
            'priority_threshold': 'medium',
            'domains_enabled': ['all']
        }
    
    def should_send(self, user_id: int, notification: Notification) -> bool:
        """Check if notification should be sent based on user preferences"""
        prefs = self.get_user_preferences(user_id)
        
        # Check if desktop notifications enabled
        if not prefs.get('desktop_enabled', True):
            return False
        
        # Check quiet hours
        quiet_hours = prefs.get('quiet_hours', {})
        if quiet_hours:
            now = datetime.now().strftime('%H:%M')
            start = quiet_hours.get('start', '22:00')
            end = quiet_hours.get('end', '08:00')
            if self._in_quiet_hours(now, start, end):
                return notification.priority == 'critical'
        
        # Check priority threshold
        priority_levels = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
        threshold = prefs.get('priority_threshold', 'medium')
        if priority_levels.get(notification.priority, 1) < priority_levels.get(threshold, 1):
            return False
        
        return True
    
    def _in_quiet_hours(self, now: str, start: str, end: str) -> bool:
        """Check if current time is in quiet hours"""
        # Handle overnight quiet hours (e.g., 22:00 to 08:00)
        if start > end:
            return now >= start or now < end
        return start <= now < end
```

---

## Feedback Loop System

### Feedback Processor

```python
# smart_response/feedback/processor.py

from typing import Dict, Optional, List
from datetime import datetime
from enum import Enum
import json

class FeedbackType(Enum):
    EXPLICIT = "explicit"      # Thumbs up/down, ratings
    IMPLICIT = "implicit"      # Engagement time, return visits
    DIRECT = "direct_teaching" # "Remember I prefer X"

class FeedbackProcessor:
    """
    Processes all types of user feedback to improve the system
    
    Types:
    1. Explicit: Thumbs up/down, ratings, reactions
    2. Implicit: Engagement time, return visits, topic avoidance
    3. Direct Teaching: User explicitly teaches the system
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    # ==================== EXPLICIT FEEDBACK ====================
    
    def record_explicit_feedback(self, user_id: int, message_id: int,
                                 character_id: str, feedback_value: str,
                                 context: Dict = None):
        """
        Record explicit feedback (thumbs up/down, rating)
        
        feedback_value: "positive", "negative", or numeric rating
        """
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO user_feedback 
            (user_id, message_id, character_id, feedback_type, 
             feedback_value, context, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, message_id, character_id, FeedbackType.EXPLICIT.value,
              feedback_value, json.dumps(context) if context else None,
              datetime.now()))
        self.db.commit()
        
        # Immediately apply to character threshold
        self._apply_explicit_feedback(character_id, user_id, feedback_value)
    
    def _apply_explicit_feedback(self, character_id: str, user_id: int,
                                 feedback_value: str):
        """Apply explicit feedback to improve character responses"""
        # Update character preference for this user
        adjustment = 0.05 if feedback_value == "positive" else -0.03
        
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO user_character_preferences (user_id, character_id, preference_score)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, character_id) DO UPDATE SET
            preference_score = preference_score + ?
        ''', (user_id, character_id, adjustment, adjustment))
        self.db.commit()
    
    # ==================== IMPLICIT FEEDBACK ====================
    
    def record_implicit_feedback(self, user_id: int, event_type: str,
                                 event_data: Dict):
        """
        Record implicit feedback from user behavior
        
        event_type: "engagement", "return_visit", "topic_avoidance", 
                    "conversation_length", "response_time"
        """
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO user_feedback 
            (user_id, feedback_type, feedback_value, context, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, FeedbackType.IMPLICIT.value, event_type,
              json.dumps(event_data), datetime.now()))
        self.db.commit()
        
        # Process based on event type
        if event_type == "engagement":
            self._process_engagement(user_id, event_data)
        elif event_type == "topic_avoidance":
            self._process_topic_avoidance(user_id, event_data)
    
    def _process_engagement(self, user_id: int, event_data: Dict):
        """Process engagement metrics"""
        # Long engagement = positive signal
        # Short engagement = might be negative
        engagement_seconds = event_data.get('duration_seconds', 0)
        character_id = event_data.get('character_id')
        
        if engagement_seconds > 120:  # More than 2 minutes = good engagement
            self._apply_explicit_feedback(character_id, user_id, "positive")
    
    def _process_topic_avoidance(self, user_id: int, event_data: Dict):
        """Process topic avoidance (user changes topic or leaves)"""
        topic = event_data.get('topic')
        character_id = event_data.get('character_id')
        
        # Store avoided topic
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO user_topic_preferences (user_id, topic, preference)
            VALUES (?, ?, 'avoid')
            ON CONFLICT(user_id, topic) DO UPDATE SET preference = 'avoid'
        ''', (user_id, topic))
        self.db.commit()
    
    # ==================== DIRECT TEACHING ====================
    
    def record_direct_teaching(self, user_id: int, teaching_type: str,
                               teaching_content: str, context: Dict = None):
        """
        Record direct teaching from user
        
        teaching_type: "preference", "correction", "instruction", "boundary"
        
        Examples:
        - "Remember I prefer short responses"
        - "Don't bring up my ex"
        - "I like practical advice, not philosophical"
        """
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO user_feedback 
            (user_id, feedback_type, feedback_value, context, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, FeedbackType.DIRECT.value, teaching_type,
              json.dumps({
                  'teaching_content': teaching_content,
                  'context': context
              }), datetime.now()))
        self.db.commit()
        
        # Store as high-priority user context
        self._store_teaching_as_context(user_id, teaching_type, teaching_content)
    
    def _store_teaching_as_context(self, user_id: int, teaching_type: str,
                                   teaching_content: str):
        """Store direct teaching as priority context"""
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO explicit_context 
            (user_id, character, context_type, context_key, context_value,
             confidence, active, extracted_via)
            VALUES (?, 'all', ?, 'user_teaching', ?, 1.0, 1, 'direct_teaching')
        ''', (user_id, teaching_type, teaching_content))
        self.db.commit()
    
    # ==================== FEEDBACK ANALYSIS ====================
    
    def get_user_learning_summary(self, user_id: int) -> Dict:
        """Get summary of what system has learned about user"""
        cursor = self.db.cursor()
        
        # Get character preferences
        cursor.execute('''
            SELECT character_id, preference_score
            FROM user_character_preferences
            WHERE user_id = ?
        ''', (user_id,))
        character_prefs = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get topic preferences
        cursor.execute('''
            SELECT topic, preference
            FROM user_topic_preferences
            WHERE user_id = ?
        ''', (user_id,))
        topic_prefs = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get direct teachings
        cursor.execute('''
            SELECT context FROM user_feedback
            WHERE user_id = ? AND feedback_type = 'direct_teaching'
            ORDER BY timestamp DESC LIMIT 20
        ''', (user_id,))
        teachings = [json.loads(row[0]) for row in cursor.fetchall()]
        
        return {
            'character_preferences': character_prefs,
            'topic_preferences': topic_prefs,
            'direct_teachings': teachings,
            'total_feedback_count': self._get_feedback_count(user_id)
        }
    
    def _get_feedback_count(self, user_id: int) -> int:
        """Get total feedback count for user"""
        cursor = self.db.cursor()
        cursor.execute('SELECT COUNT(*) FROM user_feedback WHERE user_id = ?', 
                       (user_id,))
        return cursor.fetchone()[0]
```

---

## Database Schema

### Complete Schema for New Systems

```sql
-- ============================================================
-- DOMAIN CHARACTERS
-- ============================================================

CREATE TABLE IF NOT EXISTS domain_characters (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    domain TEXT NOT NULL,
    threshold_config TEXT,  -- JSON: base_threshold, keywords, triggers
    style_config TEXT,      -- JSON: tone, formality, emoji_usage, etc.
    system_prompt TEXT,
    active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- CHARACTER INTERPRETATIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS character_interpretations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    primary_history_id INTEGER,
    character_id TEXT NOT NULL,
    interpretation TEXT,     -- JSON: character's view of the context
    concern_level REAL DEFAULT 0.0,
    responded INTEGER DEFAULT 0,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (primary_history_id) REFERENCES history_primary(id)
);

CREATE INDEX IF NOT EXISTS idx_char_interp_history 
ON character_interpretations(primary_history_id);

CREATE INDEX IF NOT EXISTS idx_char_interp_character 
ON character_interpretations(character_id);

-- ============================================================
-- FLEXIBLE CONTEXT STORAGE
-- ============================================================

CREATE TABLE IF NOT EXISTS flexible_context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    context_type TEXT NOT NULL,  -- goal, emotion, event, preference, etc.
    context_data TEXT NOT NULL,  -- JSON: flexible structure
    source TEXT,                 -- conversation, proactive, user_input
    retention_years INTEGER DEFAULT 10,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_flex_context_user 
ON flexible_context(user_id, context_type);

CREATE INDEX IF NOT EXISTS idx_flex_context_created 
ON flexible_context(created_at);

-- Context interpretations per character
CREATE TABLE IF NOT EXISTS context_interpretations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    context_id INTEGER NOT NULL,
    character_id TEXT NOT NULL,
    interpretation TEXT,  -- JSON: character's interpretation
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (context_id) REFERENCES flexible_context(id) ON DELETE CASCADE
);

-- ============================================================
-- NOTIFICATIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    character_id TEXT,
    notification_type TEXT NOT NULL,  -- check_in, insight, reminder, alert
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    priority TEXT DEFAULT 'medium',   -- low, medium, high, critical
    conversation_context TEXT,        -- JSON: related context
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    delivered_at DATETIME,
    acknowledged_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_notifications_user 
ON notifications(user_id, created_at);

-- User notification preferences
CREATE TABLE IF NOT EXISTS user_notification_preferences (
    user_id INTEGER PRIMARY KEY,
    preferences TEXT NOT NULL,  -- JSON: all preference settings
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- FEEDBACK SYSTEM
-- ============================================================

-- Extended user feedback table
CREATE TABLE IF NOT EXISTS user_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    message_id INTEGER,
    character_id TEXT,
    feedback_type TEXT NOT NULL,  -- explicit, implicit, direct_teaching
    feedback_value TEXT,
    context TEXT,                 -- JSON: additional context
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_feedback_user 
ON user_feedback(user_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_feedback_character 
ON user_feedback(character_id);

-- User-character preference scores
CREATE TABLE IF NOT EXISTS user_character_preferences (
    user_id INTEGER NOT NULL,
    character_id TEXT NOT NULL,
    preference_score REAL DEFAULT 0.0,
    interaction_count INTEGER DEFAULT 0,
    last_interaction DATETIME,
    PRIMARY KEY (user_id, character_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- User topic preferences
CREATE TABLE IF NOT EXISTS user_topic_preferences (
    user_id INTEGER NOT NULL,
    topic TEXT NOT NULL,
    preference TEXT NOT NULL,  -- prefer, avoid, neutral
    strength REAL DEFAULT 1.0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, topic),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- PROACTIVE ENGAGEMENT
-- ============================================================

CREATE TABLE IF NOT EXISTS proactive_triggers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    trigger_type TEXT NOT NULL,  -- goal_check, mood_check, milestone, opportunity
    character_id TEXT,
    trigger_config TEXT,         -- JSON: when to trigger
    last_triggered DATETIME,
    next_scheduled DATETIME,
    active INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_proactive_user 
ON proactive_triggers(user_id, active);

CREATE INDEX IF NOT EXISTS idx_proactive_next 
ON proactive_triggers(next_scheduled);

-- ============================================================
-- USER CONTEXT (PERSONALIZATION LAYER)
-- ============================================================

CREATE TABLE IF NOT EXISTS user_context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    fact_type TEXT NOT NULL,
    content TEXT NOT NULL,
    priority TEXT DEFAULT 'normal',
    confidence REAL DEFAULT 0.7,
    source_phrase TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    expires_at DATETIME,
    UNIQUE(user_id, fact_type, content)
);

CREATE INDEX IF NOT EXISTS idx_user_context_user ON user_context(user_id);

CREATE INDEX IF NOT EXISTS idx_user_context_active ON user_context(user_id, is_active);

CREATE TABLE IF NOT EXISTS user_language_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    pattern_type TEXT NOT NULL,
    user_phrase TEXT NOT NULL,
    frequency INTEGER DEFAULT 1,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, pattern_type, user_phrase)
);

CREATE INDEX IF NOT EXISTS idx_user_language_user ON user_language_patterns(user_id);

CREATE TABLE IF NOT EXISTS conversation_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    character_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    topics TEXT,
    goals_mentioned TEXT,
    emotional_arc TEXT,
    message_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_stale INTEGER DEFAULT 0,
    UNIQUE(user_id, character_id)
);

CREATE INDEX IF NOT EXISTS idx_conv_summary_user ON conversation_summaries(user_id, character_id);

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
);

-- ============================================================
-- PROACTIVE CLARIFICATION SYSTEM
-- ============================================================

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
);

CREATE TABLE IF NOT EXISTS context_gaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    character_id TEXT NOT NULL,
    gap_type TEXT NOT NULL,
    gap_description TEXT,
    resolved BOOLEAN DEFAULT 0,
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME
);

-- ============================================================
-- CHARACTER TRAIT SYSTEM (12D)
-- ============================================================

CREATE TABLE IF NOT EXISTS character_library (
    character_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    traits_json TEXT NOT NULL,
    domain TEXT DEFAULT 'general',
    description TEXT,
    philosophical_lens TEXT,
    effectiveness_score REAL DEFAULT 0.5,
    usage_count INTEGER DEFAULT 0,
    is_base BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS character_usage_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    character_id TEXT NOT NULL,
    situation_json TEXT,
    conversation_length INTEGER,
    user_satisfaction REAL,
    goal_achieved BOOLEAN,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS situation_analysis_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    character_id TEXT NOT NULL,
    analysis_json TEXT NOT NULL,
    matched_character TEXT,
    match_score REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- DEVELOPER ANALYTICS
-- ============================================================

CREATE TABLE IF NOT EXISTS developer_access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    endpoint TEXT,
    parameters TEXT,
    result_summary TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_health_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metrics_json TEXT NOT NULL,
    snapshot_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## Implementation Guide

### Phase 1 Implementation Order

1. **Week 1-2: Database Schema**
   ```bash
   python migrate_all_tables.py  # Updated with new tables
   ```

2. **Week 3-4: Base Character Classes**
   - Create `smart_response/characters/` directory
   - Implement `base.py` with character classes
   - Implement `manager.py` with CharacterManager

3. **Week 5-6: Domain Characters**
   - Create configuration for each domain character
   - Implement domain-specific logic
   - Create Coordinator character

4. **Week 7-8: Context Engine**
   - Create `smart_response/context/` directory
   - Implement flexible context storage
   - Implement dynamic matching

5. **Week 9-10: Threshold System**
   - Create `smart_response/threshold/` directory
   - Implement threshold calculator
   - Integrate with character manager

6. **Week 11-12: ConversationBox Updates**
   - Extend for multi-character responses
   - Add character style adaptation
   - Update frontend components

### File Structure

```
smart_response/
├── characters/
│   ├── __init__.py
│   ├── base.py           # BaseCharacter, DomainCharacter, Coordinator
│   ├── manager.py        # CharacterManager
│   ├── philosophy/       # Existing philosophy characters
│   │   ├── coach.py
│   │   ├── sage.py
│   │   └── ...
│   └── domain/           # New domain characters
│       ├── work.py
│       ├── relationships.py
│       ├── mental_health.py
│       ├── physical_health.py
│       ├── finance.py
│       ├── learning.py
│       ├── creativity.py
│       └── coordinator.py
├── context/
│   ├── __init__.py
│   ├── engine.py         # ContextEngine
│   └── matching.py       # Dynamic matching algorithms
├── threshold/
│   ├── __init__.py
│   └── calculator.py     # ThresholdCalculator
├── notifications/
│   ├── __init__.py
│   └── manager.py        # NotificationManager
├── feedback/
│   ├── __init__.py
│   └── processor.py      # FeedbackProcessor
└── proactive/
    ├── __init__.py
    └── engine.py         # ProactiveEngine
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Dec 14, 2025 | Initial architecture document |
| 1.1 | Dec 16, 2025 | Added user context personalization layer, throttled summaries, configurable history window + token estimation, proactive clarification system, 12D character trait matching, developer role + analytics APIs |

---

*This architecture document complements PRODUCT_ROADMAP.md and provides technical implementation details.*

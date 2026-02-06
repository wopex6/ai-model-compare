# 🤝 Character Collaboration System Design
## Moltbook-Inspired Multi-Agent Collaboration

**Date:** February 6, 2025  
**Status:** Design Phase  
**Roadmap Position:** Phase 6.5 (between Character-Specific Context and Outcome Tracking)

---

## 📍 Roadmap Integration

```
EXISTING ROADMAP (Track A):
├── ✅ Phase 1: Foundation (Dual-Layer History + AI Budget)
├── ✅ Phase 2: Explicit Context & Trust
├── ✅ Phase 3: Personality Integration (3.1, 3.2 complete)
├── ⏸️ Phase 4: Proactive Clarification (paused)
├── 🔜 Phase 5: Character Trait System ← PREREQUISITE
├── 🔜 Phase 6: Character-Specific Context ← BUILDS ON THIS
├── 🆕 Phase 6.5: CHARACTER COLLABORATION ← NEW (Moltbook-inspired)
├── 🔜 Phase 7: Outcome Tracking
└── ⏸️ Phase 8: AI Character Generation

DEPENDENCIES:
Phase 5 (Trait System) → Phase 6 (Context) → Phase 6.5 (Collaboration)
```

---

## 🎯 Core Design Principle: No Hardcoding

### Database-Driven Architecture

```python
# ❌ WRONG - Hardcoded characters
CHARACTERS = ["coach", "sage", "psychologist"]  # Inflexible

# ✅ RIGHT - Database-driven
class CollaborationSystem:
    def get_relevant_collaborators(self, message_context: Dict) -> List[Dict]:
        """
        Dynamically find relevant characters based on:
        - Trait vectors (from character_library table)
        - Domain relevance (computed, not hardcoded)
        - Historical effectiveness (from outcomes table)
        """
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT id, character_name, trait_vector, effectiveness_score
            FROM character_library
            WHERE effectiveness_score > ?
        ''', (self.min_effectiveness_threshold,))
        
        # Filter by relevance to message context
        return self._filter_by_relevance(cursor.fetchall(), message_context)
```

### Flexible Configuration Tables

```sql
-- Characters are data, not code
CREATE TABLE character_library (
    id INTEGER PRIMARY KEY,
    character_name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    trait_vector TEXT NOT NULL,  -- JSON: 12+ dimensions
    domains TEXT,  -- JSON array: ["work", "relationships", ...] or NULL for all
    can_collaborate BOOLEAN DEFAULT 1,
    collaboration_style TEXT,  -- 'advisory', 'debate', 'synthesis'
    effectiveness_score FLOAT DEFAULT 0.5
);

-- Collaboration rules are configurable
CREATE TABLE collaboration_rules (
    id INTEGER PRIMARY KEY,
    rule_name TEXT NOT NULL,
    trigger_condition TEXT NOT NULL,  -- JSON: conditions to trigger
    min_collaborators INTEGER DEFAULT 2,
    max_collaborators INTEGER DEFAULT 4,
    collaboration_mode TEXT DEFAULT 'silent',  -- 'silent', 'visible', 'debate'
    priority INTEGER DEFAULT 50
);

-- Domain definitions are data
CREATE TABLE domain_definitions (
    id INTEGER PRIMARY KEY,
    domain_name TEXT UNIQUE NOT NULL,
    keywords TEXT NOT NULL,  -- JSON array
    emotional_triggers TEXT,  -- JSON array
    related_domains TEXT  -- JSON array
);
```

---

## 🔄 Collaboration Modes

### Mode 1: Silent Collaboration (Default)
```
User sees: Single unified response
Backend: Multiple characters contribute context

Flow:
1. User message → Coordinator
2. Coordinator queries relevant characters (by trait distance)
3. Each character provides perspective (internal only)
4. Coordinator synthesizes into single response
5. User sees rich, multi-perspective answer
```

### Mode 2: Visible Attribution
```
User sees: Response with expandable perspectives

UI Example:
┌─────────────────────────────────────────┐
│ Aria's Response:                        │
│ "Based on what you've shared..."        │
│                                         │
│ ▼ See contributing perspectives         │
│   ├─ Work Advisor: "From a career..."   │
│   └─ Mind Wellness: "Emotionally..."    │
└─────────────────────────────────────────┘
```

### Mode 3: Full Debate (Moltbook-style)
```
User sees: Character dialogue/discussion

UI Example:
┌─────────────────────────────────────────┐
│ 🎭 Character Discussion                 │
│                                         │
│ Coach: "I see this as an opportunity!" │
│ Stoic: "Focus on what you control."    │
│ Sage: "What does your intuition say?"  │
│                                         │
│ 💡 Synthesis: "Considering all views..." │
└─────────────────────────────────────────┘
```

---

## 🏗️ Implementation Architecture

### Core Classes (Flexible, Not Hardcoded)

```python
class CharacterCollaborationSystem:
    """
    Orchestrates multi-character collaboration
    All characters/rules loaded from database
    """
    
    def __init__(self, db_connection, trait_system: CharacterTraitSystem,
                 budget_manager: AIBudgetManager):
        self.db = db_connection
        self.trait_system = trait_system
        self.budget_manager = budget_manager
        self._init_tables()
    
    def _init_tables(self):
        """Create collaboration tracking tables"""
        cursor = self.db.cursor()
        
        # Track collaboration events
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collaboration_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER NOT NULL,
                trigger_message TEXT NOT NULL,
                collaboration_mode TEXT NOT NULL,
                participating_characters TEXT NOT NULL,  -- JSON array of IDs
                coordinator_id INTEGER,
                final_response TEXT,
                user_satisfaction INTEGER,
                FOREIGN KEY (coordinator_id) REFERENCES character_library(id)
            )
        ''')
        
        # Track individual character contributions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS character_contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collaboration_event_id INTEGER NOT NULL,
                character_id INTEGER NOT NULL,
                contribution_type TEXT NOT NULL,  -- 'perspective', 'question', 'synthesis'
                contribution_content TEXT NOT NULL,
                relevance_score FLOAT,
                was_included_in_final BOOLEAN DEFAULT 1,
                FOREIGN KEY (collaboration_event_id) REFERENCES collaboration_events(id),
                FOREIGN KEY (character_id) REFERENCES character_library(id)
            )
        ''')
        
        self.db.commit()
    
    def should_collaborate(self, message: str, user_context: Dict) -> Tuple[bool, str]:
        """
        Determine if collaboration is needed
        Rules loaded from database, not hardcoded
        """
        # Load active rules
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT rule_name, trigger_condition, collaboration_mode
            FROM collaboration_rules
            WHERE active = 1
            ORDER BY priority DESC
        ''')
        
        rules = cursor.fetchall()
        
        for rule_name, trigger_json, mode in rules:
            trigger = json.loads(trigger_json)
            if self._evaluate_trigger(message, user_context, trigger):
                return True, mode
        
        return False, None
    
    def _evaluate_trigger(self, message: str, context: Dict, 
                         trigger: Dict) -> bool:
        """
        Evaluate if trigger condition is met
        
        Trigger examples:
        - {"multi_domain": True, "min_domains": 2}
        - {"keywords": ["work", "family"], "match_mode": "all"}
        - {"emotional_intensity": ">0.7"}
        - {"user_preference": "collaboration_enabled"}
        """
        # Multi-domain check
        if trigger.get('multi_domain'):
            detected_domains = self._detect_domains(message)
            if len(detected_domains) >= trigger.get('min_domains', 2):
                return True
        
        # Keyword check
        if 'keywords' in trigger:
            keywords = trigger['keywords']
            match_mode = trigger.get('match_mode', 'any')
            message_lower = message.lower()
            
            if match_mode == 'all':
                return all(kw in message_lower for kw in keywords)
            else:
                return any(kw in message_lower for kw in keywords)
        
        # Emotional intensity check
        if 'emotional_intensity' in trigger:
            threshold = float(trigger['emotional_intensity'].replace('>', ''))
            intensity = context.get('emotional_intensity', 0)
            return intensity > threshold
        
        return False
    
    def _detect_domains(self, message: str) -> List[str]:
        """
        Detect relevant domains from message
        Domain definitions loaded from database
        """
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT domain_name, keywords, emotional_triggers
            FROM domain_definitions
        ''')
        
        detected = []
        message_lower = message.lower()
        
        for domain_name, keywords_json, triggers_json in cursor.fetchall():
            keywords = json.loads(keywords_json)
            triggers = json.loads(triggers_json) if triggers_json else []
            
            # Check keywords
            if any(kw in message_lower for kw in keywords):
                detected.append(domain_name)
                continue
            
            # Check emotional triggers
            if any(t in message_lower for t in triggers):
                detected.append(domain_name)
        
        return detected
    
    def orchestrate_collaboration(self, message: str, user_id: int,
                                  context: Dict, mode: str) -> Dict:
        """
        Main collaboration orchestration
        
        Returns:
            {
                'response': str,  # Final synthesized response
                'contributions': List[Dict],  # Individual perspectives
                'mode': str,
                'participating_characters': List[str]
            }
        """
        # Find relevant characters by trait distance
        relevant_characters = self._find_relevant_characters(message, context)
        
        if len(relevant_characters) < 2:
            # Not enough for collaboration, single character response
            return None
        
        # Budget check for multi-character collaboration
        allowed, reason = self.budget_manager.request_ai_call(
            call_type='collaboration',
            purpose=f'Multi-character collaboration ({len(relevant_characters)} chars)',
            user_id=user_id,
            is_background=False
        )
        
        if not allowed:
            # Fall back to single character
            return None
        
        # Collect perspectives
        contributions = []
        for char in relevant_characters[:4]:  # Max 4 collaborators
            perspective = self._get_character_perspective(
                char, message, context
            )
            contributions.append({
                'character_id': char['id'],
                'character_name': char['display_name'],
                'perspective': perspective,
                'relevance_score': char['relevance_score']
            })
        
        # Synthesize based on mode
        if mode == 'silent':
            response = self._synthesize_silent(contributions, message, context)
        elif mode == 'visible':
            response = self._synthesize_visible(contributions, message, context)
        else:  # debate
            response = self._synthesize_debate(contributions, message, context)
        
        # Log collaboration event
        self._log_collaboration(user_id, message, mode, contributions, response)
        
        return {
            'response': response['final_text'],
            'contributions': contributions if mode != 'silent' else [],
            'mode': mode,
            'participating_characters': [c['character_name'] for c in contributions]
        }
    
    def _find_relevant_characters(self, message: str, 
                                  context: Dict) -> List[Dict]:
        """
        Find characters relevant to this message
        Uses trait-based matching, not hardcoded lists
        """
        # Determine ideal traits for this situation
        ideal_traits = self.trait_system._determine_ideal_traits({
            'message': message,
            'user_emotional_state': context.get('emotional_state', 'neutral'),
            'challenge_type': context.get('challenge_type', 'general')
        })
        
        # Get all characters
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT id, character_name, display_name, trait_vector, 
                   domains, effectiveness_score
            FROM character_library
            WHERE can_collaborate = 1
        ''')
        
        candidates = []
        detected_domains = self._detect_domains(message)
        
        for row in cursor.fetchall():
            char_id, name, display, traits_json, domains_json, effectiveness = row
            traits = json.loads(traits_json)
            domains = json.loads(domains_json) if domains_json else None
            
            # Calculate trait relevance
            trait_distance = self.trait_system._calculate_trait_distance(
                ideal_traits, traits
            )
            trait_relevance = 1.0 - trait_distance
            
            # Calculate domain relevance
            if domains is None:
                domain_relevance = 0.5  # Universal character
            elif any(d in domains for d in detected_domains):
                domain_relevance = 1.0  # Domain match
            else:
                domain_relevance = 0.2  # No domain match
            
            # Combined relevance score
            relevance = (trait_relevance * 0.5 + 
                        domain_relevance * 0.3 + 
                        effectiveness * 0.2)
            
            candidates.append({
                'id': char_id,
                'character_name': name,
                'display_name': display,
                'traits': traits,
                'relevance_score': relevance
            })
        
        # Sort by relevance and return top characters
        candidates.sort(key=lambda x: x['relevance_score'], reverse=True)
        return candidates
    
    def _get_character_perspective(self, character: Dict, 
                                   message: str, context: Dict) -> str:
        """
        Get a character's perspective on the message
        Uses trait-based interpretation, not hardcoded responses
        """
        # This would call the CharacterSpecificContext system
        # from Phase 6 to get the interpretation
        pass  # Implemented in Phase 6
    
    def _synthesize_silent(self, contributions: List[Dict],
                          message: str, context: Dict) -> Dict:
        """Combine perspectives into single unified response"""
        pass  # AI synthesis
    
    def _synthesize_visible(self, contributions: List[Dict],
                           message: str, context: Dict) -> Dict:
        """Create response with expandable perspective sections"""
        pass  # Structured response
    
    def _synthesize_debate(self, contributions: List[Dict],
                          message: str, context: Dict) -> Dict:
        """Create dialogue-style multi-character response"""
        pass  # Dialogue format
```

---

## 🔗 Integration Points

### With Existing Systems

```python
# In app.py or routing layer

def process_message_with_collaboration(message: str, user_id: int, 
                                       character_id: str):
    """
    Enhanced message processing with optional collaboration
    """
    # 1. Build context (existing)
    context = context_manager.build_context(user_id, message)
    
    # 2. Check if collaboration needed (NEW)
    should_collab, mode = collaboration_system.should_collaborate(
        message, context
    )
    
    if should_collab:
        # 3a. Multi-character collaboration
        result = collaboration_system.orchestrate_collaboration(
            message, user_id, context, mode
        )
        if result:
            return result
    
    # 3b. Single character response (fallback/default)
    return single_character_response(message, user_id, character_id, context)
```

### With Character Trait System (Phase 5)

```
Character Trait System provides:
├── Character library (database)
├── Trait vectors (12 dimensions)
├── Distance calculations
└── Situation-to-traits mapping

Collaboration System uses:
├── Trait-based character selection
├── Relevance scoring
└── Dynamic character discovery
```

### With Character-Specific Context (Phase 6)

```
Character Context provides:
├── Philosophical interpretation
├── Lens-based reframing
└── Multi-perspective storage

Collaboration System adds:
├── Active perspective gathering
├── Synthesis across perspectives
└── Attribution tracking
```

---

## 📊 Configuration Examples

### Default Collaboration Rules (inserted as data)

```sql
INSERT INTO collaboration_rules (rule_name, trigger_condition, collaboration_mode, priority) VALUES
-- Multi-domain messages trigger collaboration
('multi_domain_trigger', 
 '{"multi_domain": true, "min_domains": 2}', 
 'visible', 80),

-- High emotional intensity
('emotional_crisis',
 '{"emotional_intensity": ">0.8"}',
 'silent', 90),

-- User explicitly requests multiple perspectives
('explicit_request',
 '{"keywords": ["different perspectives", "what do you all think", "multiple views"], "match_mode": "any"}',
 'debate', 100),

-- Complex life decisions
('life_decision',
 '{"keywords": ["should I", "big decision", "life changing"], "match_mode": "any"}',
 'visible', 70);
```

### Domain Definitions (data, not code)

```sql
INSERT INTO domain_definitions (domain_name, keywords, emotional_triggers, related_domains) VALUES
('work', 
 '["job", "career", "boss", "promotion", "deadline", "project", "colleague"]',
 '["burnout", "fired", "hate my job", "overworked"]',
 '["finance", "learning"]'),

('relationships',
 '["partner", "family", "friend", "marriage", "dating", "love"]', 
 '["breakup", "lonely", "betrayed", "rejected"]',
 '["mental_health"]'),

('mental_health',
 '["anxious", "depressed", "stressed", "overwhelmed", "emotions"]',
 '["panic", "breakdown", "can''t cope"]',
 '["relationships", "physical_health"]');
```

---

## 🎯 Success Criteria

### Phase 6.5 Complete When:

- [ ] Collaboration triggers loaded from database (not hardcoded)
- [ ] Character selection uses trait vectors (dynamic)
- [ ] Domain detection uses configurable keywords
- [ ] Silent mode synthesizes multiple perspectives
- [ ] Visible mode shows attributions
- [ ] Debate mode creates dialogue
- [ ] All within AI budget limits
- [ ] Collaboration events logged for learning

---

## 📅 Implementation Timeline

| Step | Task | Dependencies | Time |
|------|------|--------------|------|
| 1 | Phase 5: Character Trait System | None | 4-5h |
| 2 | Phase 6: Character-Specific Context | Phase 5 | 2-3h |
| 3 | Collaboration tables & rules | Phase 5, 6 | 1-2h |
| 4 | Trigger evaluation system | Step 3 | 2h |
| 5 | Character selection (trait-based) | Steps 3, 4 | 2h |
| 6 | Silent collaboration mode | Step 5 | 2-3h |
| 7 | Visible attribution mode | Step 6 | 2h |
| 8 | Debate mode (Moltbook-style) | Step 7 | 3h |
| 9 | Frontend UI for modes | Step 8 | 3-4h |

**Total:** ~22-26 hours (after Phase 5 & 6)

---

## 🔑 Key Flexibility Points

1. **Characters** → Database, not code constants
2. **Domains** → Configurable definitions table
3. **Triggers** → Rule-based with JSON conditions
4. **Modes** → Pluggable synthesis strategies
5. **Scoring** → Algorithmic (trait distance), not manual
6. **Expansion** → New characters auto-participate if `can_collaborate=1`

This ensures the system works with:
- Current 16 characters
- Future AI-generated characters
- Any new domains added
- Changed collaboration rules (no code deploy needed)

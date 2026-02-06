"""
Character Collaboration System (Phase 6.5)
Moltbook-inspired multi-agent collaboration.

Database-driven architecture - NO hardcoded characters or rules.
All characters, domains, and triggers loaded from database.
"""

import sqlite3
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

from .character_traits import CharacterTraitSystem, CharacterProfile, TraitVector, SituationAnalysis
from .character_specific_context import CharacterSpecificContext, CharacterInterpretation


@dataclass
class CollaborationResult:
    """Result of a multi-character collaboration"""
    response: str
    mode: str  # 'silent', 'visible', 'debate'
    contributions: List[Dict]
    participating_characters: List[str]
    event_id: int


class CharacterCollaborationSystem:
    """
    Orchestrates multi-character collaboration.
    All characters/rules loaded from database - NO hardcoding.
    """
    
    # Default collaboration rules (will be stored in DB)
    DEFAULT_RULES = [
        {
            'rule_name': 'multi_domain',
            'trigger_condition': {'multi_domain': True, 'min_domains': 2},
            'collaboration_mode': 'visible',
            'min_collaborators': 2,
            'max_collaborators': 4,
            'priority': 100
        },
        {
            'rule_name': 'high_emotional_intensity',
            'trigger_condition': {'emotional_intensity': '>0.7'},
            'collaboration_mode': 'silent',
            'min_collaborators': 2,
            'max_collaborators': 3,
            'priority': 80
        },
        {
            'rule_name': 'complex_problem',
            'trigger_condition': {'keywords': ['help me decide', 'what should i do', 'torn between', 'confused about'], 'match_mode': 'any'},
            'collaboration_mode': 'debate',
            'min_collaborators': 2,
            'max_collaborators': 3,
            'priority': 70
        }
    ]
    
    # Default domains will be derived from DOMAIN_CHARACTER_CONFIGS at runtime
    # This eliminates redundancy - domain definitions come from character configs
    DEFAULT_DOMAINS = None  # Set dynamically in _seed_default_data()
    
    @classmethod
    def _derive_domains_from_configs(cls) -> list:
        """Derive domain definitions from DOMAIN_CHARACTER_CONFIGS - single source of truth"""
        try:
            from .characters.configs import DOMAIN_CHARACTER_CONFIGS
            
            domains = []
            for char_id, config in DOMAIN_CHARACTER_CONFIGS.items():
                domain_name = config.get('domain', 'general')
                if domain_name == 'all':  # Skip coordinator
                    continue
                    
                # Extract keywords from threshold_config
                threshold_config = config.get('threshold_config', {})
                keywords = threshold_config.get('domain_keywords', [])
                emotional_triggers = threshold_config.get('emotional_triggers', [])
                
                # Only add if we have keywords
                if keywords:
                    domains.append({
                        'domain_name': domain_name,
                        'keywords': keywords,
                        'emotional_triggers': emotional_triggers,
                        'related_domains': []  # Can be extended if needed
                    })
            
            return domains
        except ImportError:
            # Fallback if configs not available
            return [
                {'domain_name': 'work', 'keywords': ['job', 'career', 'work'], 'emotional_triggers': [], 'related_domains': []},
                {'domain_name': 'relationships', 'keywords': ['relationship', 'partner', 'family'], 'emotional_triggers': [], 'related_domains': []},
                {'domain_name': 'mental_health', 'keywords': ['anxious', 'stressed', 'emotions'], 'emotional_triggers': [], 'related_domains': []},
                {'domain_name': 'finance', 'keywords': ['money', 'budget', 'debt'], 'emotional_triggers': [], 'related_domains': []},
                {'domain_name': 'learning', 'keywords': ['learn', 'study', 'skill'], 'emotional_triggers': [], 'related_domains': []}
            ]
    
    def __init__(
        self, 
        db_connection: sqlite3.Connection,
        trait_system: CharacterTraitSystem,
        context_system: CharacterSpecificContext,
        ai_budget_manager = None
    ):
        self.db = db_connection
        self.trait_system = trait_system
        self.context_system = context_system
        self.budget_manager = ai_budget_manager
        self._init_tables()
        self._seed_default_data()
    
    def _init_tables(self):
        """Create collaboration tracking tables"""
        cursor = self.db.cursor()
        
        # Collaboration rules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collaboration_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT UNIQUE NOT NULL,
                trigger_condition TEXT NOT NULL,
                collaboration_mode TEXT DEFAULT 'silent',
                min_collaborators INTEGER DEFAULT 2,
                max_collaborators INTEGER DEFAULT 4,
                priority INTEGER DEFAULT 50,
                active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Domain definitions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS domain_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain_name TEXT UNIQUE NOT NULL,
                keywords TEXT NOT NULL,
                emotional_triggers TEXT,
                related_domains TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Collaboration events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collaboration_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                trigger_message TEXT NOT NULL,
                collaboration_mode TEXT NOT NULL,
                participating_characters TEXT NOT NULL,
                triggered_rule TEXT,
                detected_domains TEXT,
                final_response TEXT,
                user_satisfaction INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Character contributions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS character_contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collaboration_event_id INTEGER NOT NULL,
                character_id TEXT NOT NULL,
                character_name TEXT NOT NULL,
                contribution_type TEXT NOT NULL,
                contribution_content TEXT NOT NULL,
                relevance_score FLOAT,
                was_included_in_final INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (collaboration_event_id) REFERENCES collaboration_events(id)
            )
        ''')
        
        # Indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_collab_events_user ON collaboration_events(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_collab_contrib_event ON character_contributions(collaboration_event_id)')
        
        self.db.commit()
    
    def _seed_default_data(self):
        """Seed default rules and domains if tables are empty"""
        cursor = self.db.cursor()
        
        # Seed rules
        cursor.execute('SELECT COUNT(*) FROM collaboration_rules')
        if cursor.fetchone()[0] == 0:
            for rule in self.DEFAULT_RULES:
                cursor.execute('''
                    INSERT OR IGNORE INTO collaboration_rules 
                    (rule_name, trigger_condition, collaboration_mode, min_collaborators, max_collaborators, priority)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    rule['rule_name'],
                    json.dumps(rule['trigger_condition']),
                    rule['collaboration_mode'],
                    rule['min_collaborators'],
                    rule['max_collaborators'],
                    rule['priority']
                ))
        
        # Seed domains - derived from DOMAIN_CHARACTER_CONFIGS (single source of truth)
        cursor.execute('SELECT COUNT(*) FROM domain_definitions')
        if cursor.fetchone()[0] == 0:
            derived_domains = self._derive_domains_from_configs()
            for domain in derived_domains:
                cursor.execute('''
                    INSERT OR IGNORE INTO domain_definitions
                    (domain_name, keywords, emotional_triggers, related_domains)
                    VALUES (?, ?, ?, ?)
                ''', (
                    domain['domain_name'],
                    json.dumps(domain['keywords']),
                    json.dumps(domain.get('emotional_triggers', [])),
                    json.dumps(domain.get('related_domains', []))
                ))
        
        self.db.commit()
    
    def should_collaborate(self, message: str, user_context: Dict = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Determine if collaboration is needed.
        Rules loaded from database, not hardcoded.
        
        Returns: (should_collaborate, mode, rule_name)
        """
        if user_context is None:
            user_context = {}
        
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
                return True, mode, rule_name
        
        return False, None, None
    
    def _evaluate_trigger(self, message: str, context: Dict, trigger: Dict) -> bool:
        """
        Evaluate if trigger condition is met.
        
        Trigger types:
        - {"multi_domain": True, "min_domains": 2}
        - {"keywords": ["word1", "word2"], "match_mode": "any"|"all"}
        - {"emotional_intensity": ">0.7"}
        """
        # Multi-domain check
        if trigger.get('multi_domain'):
            detected_domains = self._detect_domains(message)
            min_domains = trigger.get('min_domains', 2)
            if len(detected_domains) >= min_domains:
                return True
        
        # Keyword check
        if 'keywords' in trigger:
            keywords = trigger['keywords']
            match_mode = trigger.get('match_mode', 'any')
            message_lower = message.lower()
            
            if match_mode == 'all':
                if all(kw.lower() in message_lower for kw in keywords):
                    return True
            else:  # any
                if any(kw.lower() in message_lower for kw in keywords):
                    return True
        
        # Emotional intensity check
        if 'emotional_intensity' in trigger:
            threshold_str = trigger['emotional_intensity']
            threshold = float(threshold_str.replace('>', '').replace('<', ''))
            intensity = context.get('emotional_intensity', 0.5)
            
            if '>' in threshold_str and intensity > threshold:
                return True
            elif '<' in threshold_str and intensity < threshold:
                return True
        
        return False
    
    def _detect_domains(self, message: str) -> List[str]:
        """
        Detect relevant domains from message.
        Domain definitions loaded from database.
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
            if any(kw.lower() in message_lower for kw in keywords):
                detected.append(domain_name)
                continue
            
            # Check emotional triggers
            if any(t.lower() in message_lower for t in triggers):
                detected.append(domain_name)
        
        return detected
    
    def _find_relevant_characters(self, message: str, context: Dict) -> List[Dict]:
        """
        Find characters relevant to this message.
        Uses trait-based matching, not hardcoded lists.
        """
        # Analyze the situation to get ideal traits
        situation = self.trait_system.analyze_situation(message)
        ideal_traits = situation.get_ideal_traits()
        
        # Get detected domains
        detected_domains = self._detect_domains(message)
        
        # Score all characters
        candidates = []
        for char_id, char in self.trait_system.characters.items():
            # Calculate trait relevance (distance from ideal)
            trait_distance = char.traits.distance_to(ideal_traits)
            trait_relevance = 1.0 - min(trait_distance, 1.0)
            
            # Calculate domain relevance
            if char.domain:
                if char.domain.lower() in [d.lower() for d in detected_domains]:
                    domain_relevance = 1.0
                elif char.domain.lower() == 'general':
                    domain_relevance = 0.5
                else:
                    domain_relevance = 0.3
            else:
                domain_relevance = 0.5  # Universal character
            
            # Combined relevance score
            relevance = (
                trait_relevance * 0.5 + 
                domain_relevance * 0.3 + 
                char.effectiveness_score * 0.2
            )
            
            candidates.append({
                'id': char_id,
                'character_id': char.character_id,
                'display_name': char.display_name,
                'traits': char.traits,
                'domain': char.domain,
                'relevance_score': relevance,
                'profile': char
            })
        
        # Sort by relevance
        candidates.sort(key=lambda x: x['relevance_score'], reverse=True)
        return candidates
    
    def orchestrate_collaboration(
        self, 
        message: str, 
        user_id: int,
        context: Dict = None,
        mode: str = 'silent',
        rule_name: str = None
    ) -> Optional[CollaborationResult]:
        """
        Main collaboration orchestration.
        """
        if context is None:
            context = {}
        
        # Find relevant characters
        relevant_characters = self._find_relevant_characters(message, context)
        
        if len(relevant_characters) < 2:
            return None  # Not enough for collaboration
        
        # Get detected domains
        detected_domains = self._detect_domains(message)
        
        # Limit collaborators
        max_collabs = 4
        cursor = self.db.cursor()
        if rule_name:
            cursor.execute('SELECT max_collaborators FROM collaboration_rules WHERE rule_name = ?', (rule_name,))
            row = cursor.fetchone()
            if row:
                max_collabs = row[0]
        
        selected_characters = relevant_characters[:max_collabs]
        
        # Collect perspectives using Phase 6 context system
        contributions = []
        for char in selected_characters:
            interpretation = self.context_system.interpret_event_as_character(
                message, char['profile'], context
            )
            contributions.append({
                'character_id': char['character_id'],
                'character_name': char['display_name'],
                'interpretation': interpretation.interpretation,
                'emotional_framing': interpretation.emotional_framing,
                'action_suggestion': interpretation.action_suggestion,
                'philosophical_lens': interpretation.philosophical_lens,
                'relevance_score': char['relevance_score'],
                'dominant_traits': interpretation.dominant_traits
            })
        
        # Synthesize response based on mode
        if mode == 'silent':
            response = self._synthesize_silent(contributions, message, context)
        elif mode == 'visible':
            response = self._synthesize_visible(contributions, message, context)
        else:  # debate
            response = self._synthesize_debate(contributions, message, context)
        
        # Log the collaboration event
        event_id = self._log_collaboration(
            user_id, message, mode, rule_name,
            detected_domains, contributions, response
        )
        
        return CollaborationResult(
            response=response,
            mode=mode,
            contributions=contributions,
            participating_characters=[c['character_name'] for c in contributions],
            event_id=event_id
        )
    
    def _synthesize_silent(self, contributions: List[Dict], message: str, context: Dict) -> str:
        """Combine perspectives into single unified response (user sees one voice)"""
        # Find the most relevant character's base response
        if not contributions:
            return "I'm here to help."
        
        primary = contributions[0]
        secondary_insights = []
        
        for c in contributions[1:]:
            # Extract unique action suggestions
            if c['action_suggestion'] != primary['action_suggestion']:
                secondary_insights.append(c['action_suggestion'])
        
        # Build unified response
        response = primary['interpretation']
        
        if secondary_insights:
            response += "\n\n" + primary['emotional_framing']
            response += "\n\n" + primary['action_suggestion']
            if secondary_insights:
                response += " " + secondary_insights[0][:100]
        else:
            response += "\n\n" + primary['action_suggestion']
        
        return response
    
    def _synthesize_visible(self, contributions: List[Dict], message: str, context: Dict) -> str:
        """Create response with visible character attributions"""
        if not contributions:
            return "I'm here to help."
        
        primary = contributions[0]
        
        # Main response from primary character
        response = f"**{primary['character_name']}:** {primary['interpretation']}\n\n"
        response += f"{primary['action_suggestion']}\n\n"
        
        # Add other perspectives
        if len(contributions) > 1:
            response += "---\n**Other Perspectives:**\n\n"
            for c in contributions[1:]:
                response += f"*{c['character_name']}* ({c['philosophical_lens']}): "
                response += f"{c['interpretation'][:150]}...\n\n"
        
        return response
    
    def _synthesize_debate(self, contributions: List[Dict], message: str, context: Dict) -> str:
        """Create dialogue-style multi-character response (Moltbook-style)"""
        if not contributions:
            return "I'm here to help."
        
        # Character dialogue format
        response = "🎭 **Character Discussion:**\n\n"
        
        for c in contributions:
            response += f"**{c['character_name']}:** \"{c['interpretation']}\"\n\n"
        
        # Synthesis
        response += "---\n💡 **Synthesis:** "
        
        # Combine key points
        key_points = []
        for c in contributions:
            key_points.append(c['action_suggestion'].split('.')[0])
        
        response += "Considering these perspectives: " + "; ".join(key_points[:3]) + "."
        
        return response
    
    def _log_collaboration(
        self,
        user_id: int,
        message: str,
        mode: str,
        rule_name: str,
        detected_domains: List[str],
        contributions: List[Dict],
        response: str
    ) -> int:
        """Log collaboration event and contributions"""
        cursor = self.db.cursor()
        
        # Log main event
        cursor.execute('''
            INSERT INTO collaboration_events
            (user_id, trigger_message, collaboration_mode, participating_characters, 
             triggered_rule, detected_domains, final_response)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            message,
            mode,
            json.dumps([c['character_id'] for c in contributions]),
            rule_name,
            json.dumps(detected_domains),
            response
        ))
        
        event_id = cursor.lastrowid
        
        # Log individual contributions
        for c in contributions:
            cursor.execute('''
                INSERT INTO character_contributions
                (collaboration_event_id, character_id, character_name, 
                 contribution_type, contribution_content, relevance_score)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                event_id,
                c['character_id'],
                c['character_name'],
                'perspective',
                json.dumps({
                    'interpretation': c['interpretation'],
                    'emotional_framing': c['emotional_framing'],
                    'action_suggestion': c['action_suggestion']
                }),
                c['relevance_score']
            ))
        
        self.db.commit()
        return event_id
    
    def get_collaboration_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get user's collaboration history"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT id, trigger_message, collaboration_mode, participating_characters,
                   triggered_rule, detected_domains, created_at
            FROM collaboration_events
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'event_id': row[0],
                'message': row[1],
                'mode': row[2],
                'characters': json.loads(row[3]),
                'rule': row[4],
                'domains': json.loads(row[5]) if row[5] else [],
                'timestamp': row[6]
            })
        
        return history
    
    def get_collaboration_stats(self) -> Dict:
        """Get collaboration statistics"""
        cursor = self.db.cursor()
        
        # Total collaborations
        cursor.execute('SELECT COUNT(*) FROM collaboration_events')
        total = cursor.fetchone()[0]
        
        # By mode
        cursor.execute('''
            SELECT collaboration_mode, COUNT(*) 
            FROM collaboration_events 
            GROUP BY collaboration_mode
        ''')
        by_mode = {row[0]: row[1] for row in cursor.fetchall()}
        
        # By rule
        cursor.execute('''
            SELECT triggered_rule, COUNT(*) 
            FROM collaboration_events 
            WHERE triggered_rule IS NOT NULL
            GROUP BY triggered_rule
        ''')
        by_rule = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Most used characters
        cursor.execute('''
            SELECT character_name, COUNT(*) as uses
            FROM character_contributions
            GROUP BY character_id
            ORDER BY uses DESC
            LIMIT 10
        ''')
        top_characters = [{
            'character': row[0],
            'uses': row[1]
        } for row in cursor.fetchall()]
        
        return {
            'total_collaborations': total,
            'by_mode': by_mode,
            'by_rule': by_rule,
            'top_characters': top_characters
        }
    
    def get_rules(self) -> List[Dict]:
        """Get all collaboration rules"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT id, rule_name, trigger_condition, collaboration_mode,
                   min_collaborators, max_collaborators, priority, active
            FROM collaboration_rules
            ORDER BY priority DESC
        ''')
        
        return [{
            'id': row[0],
            'rule_name': row[1],
            'trigger_condition': json.loads(row[2]),
            'mode': row[3],
            'min_collaborators': row[4],
            'max_collaborators': row[5],
            'priority': row[6],
            'active': bool(row[7])
        } for row in cursor.fetchall()]
    
    def get_domains(self) -> List[Dict]:
        """Get all domain definitions"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT id, domain_name, keywords, emotional_triggers, related_domains
            FROM domain_definitions
        ''')
        
        return [{
            'id': row[0],
            'domain_name': row[1],
            'keywords': json.loads(row[2]),
            'emotional_triggers': json.loads(row[3]) if row[3] else [],
            'related_domains': json.loads(row[4]) if row[4] else []
        } for row in cursor.fetchall()]


def create_collaboration_system(
    db_connection: sqlite3.Connection,
    trait_system: CharacterTraitSystem,
    context_system: CharacterSpecificContext,
    budget_manager = None
) -> CharacterCollaborationSystem:
    """Factory function to create CharacterCollaborationSystem"""
    return CharacterCollaborationSystem(
        db_connection, trait_system, context_system, budget_manager
    )

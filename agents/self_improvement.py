"""
Self-Improvement Agent
======================
Analyzes conversation quality scores and effectiveness data to automatically
suggest and apply improvements to character prompts, trait vectors, and configs.

Feedback loop:
  SimUsers → Conversations → QualityScorer → SelfImprovement → Better Prompts → Repeat

Tunable parameters:
  - Character trait vectors (12-dimensional)
  - System prompt additions (append learned guidelines)
  - Style config (tone, response_length, emoji_usage)
  - Threshold config (base_threshold, urgency_multiplier)

Safety:
  - All changes are logged with before/after snapshots
  - Changes are small (max ±0.05 per trait per cycle)
  - Requires minimum sample size before acting
  - Dry-run mode for review before applying

Usage:
    python agents/self_improvement.py --db smart_response.db --dry-run
    python agents/self_improvement.py --db smart_response.db --apply
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class ImprovementSuggestion:
    """A single suggested improvement."""
    character_id: str
    parameter: str          # 'trait_vector', 'style_config', 'system_prompt_addon'
    field: str              # e.g. 'empathy', 'response_length', etc.
    current_value: any
    suggested_value: any
    reason: str
    confidence: float       # 0-1 how confident we are
    evidence: Dict = field(default_factory=dict)


@dataclass
class ImprovementReport:
    """Full improvement analysis report."""
    generated_at: str
    character_analyses: Dict[str, Dict]
    suggestions: List[ImprovementSuggestion]
    applied: List[ImprovementSuggestion]
    skipped: List[Tuple[ImprovementSuggestion, str]]  # (suggestion, skip_reason)


class SelfImprovementAgent:
    """Analyzes conversation data and suggests/applies character improvements."""
    
    # Minimum conversations to analyze before suggesting changes
    MIN_SAMPLE_SIZE = 5
    # Maximum trait adjustment per cycle
    MAX_TRAIT_DELTA = 0.05
    # Minimum confidence to auto-apply
    MIN_AUTO_APPLY_CONFIDENCE = 0.7
    # Quality score threshold — below this triggers improvement
    QUALITY_THRESHOLD = 0.55
    
    def __init__(self, db_path: str = None, event_bus=None):
        self.db_path = db_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'smart_response.db'
        )
        self.event_bus = event_bus
        self.improvement_log: List[Dict] = []
    
    def analyze(self, days: int = 14, min_convos: int = None) -> ImprovementReport:
        """Analyze recent data and generate improvement suggestions."""
        min_convos = min_convos or self.MIN_SAMPLE_SIZE
        
        report = ImprovementReport(
            generated_at=datetime.now().isoformat(),
            character_analyses={},
            suggestions=[],
            applied=[],
            skipped=[],
        )
        
        # 1. Gather quality scores per character
        char_quality = self._get_quality_by_character(days)
        
        # 2. Gather effectiveness data per character
        char_effectiveness = self._get_effectiveness_by_character(days)
        
        # 3. Gather conversation patterns
        char_patterns = self._get_conversation_patterns(days)
        
        # 4. Analyze each character
        all_characters = set(list(char_quality.keys()) + list(char_effectiveness.keys()))
        
        for char_id in all_characters:
            quality = char_quality.get(char_id, {})
            effectiveness = char_effectiveness.get(char_id, {})
            patterns = char_patterns.get(char_id, {})
            
            sample_size = quality.get('count', 0) + effectiveness.get('count', 0)
            
            analysis = {
                'character_id': char_id,
                'sample_size': sample_size,
                'quality': quality,
                'effectiveness': effectiveness,
                'patterns': patterns,
                'suggestions': [],
            }
            
            if sample_size >= min_convos:
                suggestions = self._generate_suggestions(char_id, quality, effectiveness, patterns)
                analysis['suggestions'] = [s.field for s in suggestions]
                report.suggestions.extend(suggestions)
            else:
                analysis['skip_reason'] = f'Insufficient data ({sample_size}/{min_convos})'
            
            report.character_analyses[char_id] = analysis
        
        # 5. Global suggestions (not character-specific)
        global_suggestions = self._generate_global_suggestions(char_quality, char_patterns)
        report.suggestions.extend(global_suggestions)
        
        return report
    
    def apply_suggestions(self, report: ImprovementReport, dry_run: bool = True) -> ImprovementReport:
        """Apply suggestions from a report (or dry-run to preview)."""
        for suggestion in report.suggestions:
            if suggestion.confidence < self.MIN_AUTO_APPLY_CONFIDENCE:
                report.skipped.append((suggestion, f'Low confidence ({suggestion.confidence:.2f})'))
                continue
            
            if dry_run:
                report.skipped.append((suggestion, 'Dry run — not applied'))
                continue
            
            # Apply the change
            success = self._apply_suggestion(suggestion)
            if success:
                report.applied.append(suggestion)
                self._log_improvement(suggestion)
            else:
                report.skipped.append((suggestion, 'Application failed'))
        
        return report
    
    # ================================================================
    # DATA GATHERING
    # ================================================================
    
    def _get_quality_by_character(self, days: int) -> Dict[str, Dict]:
        """Get average quality scores grouped by character.
        
        Works for both domain characters (coordinator, domain_work, etc.)
        and philosophy characters (stoic_philosopher, wisdom_sage, etc.).
        Rows with empty character_id are grouped under 'unknown'.
        """
        results = {}
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            cursor = conn.cursor()
            
            # Column is 'overall' (not 'overall_score') in conversation_quality_scores
            cursor.execute("""
                SELECT character_id, character_type,
                       AVG(overall), AVG(coherence), AVG(helpfulness),
                       AVG(engagement), AVG(resolution), AVG(consistency),
                       COUNT(*), MIN(overall), MAX(overall)
                FROM conversation_quality_scores
                WHERE scored_at > datetime('now', ?)
                GROUP BY character_id
            """, (f'-{days} days',))
            
            for row in cursor.fetchall():
                char_id = row[0] or 'unknown'
                results[char_id] = {
                    'character_type': row[1] or 'unknown',
                    'overall': round(row[2] or 0, 3),
                    'coherence': round(row[3] or 0, 3),
                    'helpfulness': round(row[4] or 0, 3),
                    'engagement': round(row[5] or 0, 3),
                    'resolution': round(row[6] or 0, 3),
                    'consistency': round(row[7] or 0, 3),
                    'count': row[8],
                    'min_score': round(row[9] or 0, 3),
                    'max_score': round(row[10] or 0, 3),
                }
            conn.close()
        except Exception as e:
            print(f"  ⚠️ Quality data error: {e}")
        return results
    
    def _get_effectiveness_by_character(self, days: int) -> Dict[str, Dict]:
        """Get effectiveness outcomes grouped by character."""
        results = {}
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            cursor = conn.cursor()
            
            # Check if the table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversation_outcomes'")
            if not cursor.fetchone():
                conn.close()
                return results
            
            cursor.execute("""
                SELECT character_id,
                       AVG(satisfaction_estimate), AVG(message_count),
                       COUNT(*),
                       SUM(CASE WHEN engagement_level IN ('high','very_high') THEN 1 ELSE 0 END)
                FROM conversation_outcomes
                WHERE timestamp > datetime('now', ?)
                GROUP BY character_id
            """, (f'-{days} days',))
            
            for row in cursor.fetchall():
                total = row[3] or 1
                results[row[0] or 'unknown'] = {
                    'avg_satisfaction': round(row[1] or 0, 3),
                    'avg_messages': round(row[2] or 0, 1),
                    'count': row[3],
                    'high_engagement_pct': round((row[4] or 0) / total * 100, 1),
                }
            conn.close()
        except Exception as e:
            print(f"  ⚠️ Effectiveness data error: {e}")
        return results
    
    def _get_conversation_patterns(self, days: int) -> Dict[str, Dict]:
        """Analyze conversation patterns per character."""
        results = {}
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            cursor = conn.cursor()
            
            # Get message length patterns from ai_conversations + messages
            # messages.conversation_id references ai_conversations.id (not session_id)
            cursor.execute("""
                SELECT c.character_id, 
                       AVG(LENGTH(m.content)) as avg_msg_len,
                       COUNT(m.id) as total_msgs,
                       COUNT(DISTINCT c.id) as convo_count
                FROM ai_conversations c
                JOIN messages m ON m.conversation_id = c.id
                WHERE c.created_at > datetime('now', ?)
                  AND m.sender_type = 'assistant'
                GROUP BY c.character_id
            """, (f'-{days} days',))
            
            for row in cursor.fetchall():
                char_id = row[0] or 'unknown'
                results[char_id] = {
                    'avg_response_length': round(row[1] or 0),
                    'total_messages': row[2],
                    'conversation_count': row[3],
                    'avg_msgs_per_convo': round((row[2] or 0) / max(row[3], 1), 1),
                }
            conn.close()
        except Exception as e:
            print(f"  ⚠️ Pattern data error: {e}")
        return results
    
    # ================================================================
    # SUGGESTION GENERATION
    # ================================================================
    
    def _generate_suggestions(self, char_id: str, quality: Dict,
                               effectiveness: Dict, patterns: Dict) -> List[ImprovementSuggestion]:
        """Generate improvement suggestions for a specific character."""
        suggestions = []
        
        # --- Quality-based suggestions ---
        
        # Low coherence → increase structure trait
        if quality.get('coherence', 1) < self.QUALITY_THRESHOLD:
            suggestions.append(ImprovementSuggestion(
                character_id=char_id,
                parameter='trait_vector',
                field='structure',
                current_value=None,  # Will be filled from DB
                suggested_value='+0.05',
                reason=f"Coherence score low ({quality['coherence']:.2f}). "
                       f"Increasing structure should improve topic focus.",
                confidence=0.6 + (self.QUALITY_THRESHOLD - quality['coherence']),
                evidence={'coherence': quality['coherence'], 'sample': quality.get('count', 0)},
            ))
        
        # Low helpfulness → increase supportiveness and action_oriented
        if quality.get('helpfulness', 1) < self.QUALITY_THRESHOLD:
            suggestions.append(ImprovementSuggestion(
                character_id=char_id,
                parameter='trait_vector',
                field='supportiveness',
                current_value=None,
                suggested_value='+0.05',
                reason=f"Helpfulness score low ({quality['helpfulness']:.2f}). "
                       f"Increasing supportiveness should improve practical advice.",
                confidence=0.6 + (self.QUALITY_THRESHOLD - quality['helpfulness']),
                evidence={'helpfulness': quality['helpfulness']},
            ))
            suggestions.append(ImprovementSuggestion(
                character_id=char_id,
                parameter='trait_vector',
                field='action_oriented',
                current_value=None,
                suggested_value='+0.04',
                reason=f"Helpfulness low — increasing action orientation for more practical responses.",
                confidence=0.55,
                evidence={'helpfulness': quality['helpfulness']},
            ))
        
        # Low engagement → increase empathy, decrease formality
        if quality.get('engagement', 1) < self.QUALITY_THRESHOLD:
            suggestions.append(ImprovementSuggestion(
                character_id=char_id,
                parameter='trait_vector',
                field='empathy',
                current_value=None,
                suggested_value='+0.05',
                reason=f"Engagement score low ({quality['engagement']:.2f}). "
                       f"Higher empathy should encourage deeper conversations.",
                confidence=0.65,
                evidence={'engagement': quality['engagement']},
            ))
        
        # Low consistency → add system prompt addon
        if quality.get('consistency', 1) < self.QUALITY_THRESHOLD:
            suggestions.append(ImprovementSuggestion(
                character_id=char_id,
                parameter='system_prompt_addon',
                field='consistency_reminder',
                current_value='',
                suggested_value='Maintain a consistent tone and personality throughout. '
                               'Do not switch between formal and casual mid-conversation.',
                reason=f"Consistency score low ({quality['consistency']:.2f}). "
                       f"Adding explicit prompt guidance for tone consistency.",
                confidence=0.7,
                evidence={'consistency': quality['consistency']},
            ))
        
        # --- Pattern-based suggestions ---
        
        avg_response_len = patterns.get('avg_response_length', 0)
        
        # Very long responses → suggest reducing verbosity
        if avg_response_len > 800:
            suggestions.append(ImprovementSuggestion(
                character_id=char_id,
                parameter='trait_vector',
                field='verbosity',
                current_value=None,
                suggested_value='-0.05',
                reason=f"Average response length is {avg_response_len} chars. "
                       f"Reducing verbosity for more concise responses.",
                confidence=0.6,
                evidence={'avg_response_length': avg_response_len},
            ))
        
        # Very short responses → suggest increasing depth
        elif avg_response_len > 0 and avg_response_len < 150:
            suggestions.append(ImprovementSuggestion(
                character_id=char_id,
                parameter='trait_vector',
                field='depth',
                current_value=None,
                suggested_value='+0.04',
                reason=f"Average response length is only {avg_response_len} chars. "
                       f"Increasing depth for more substantial responses.",
                confidence=0.55,
                evidence={'avg_response_length': avg_response_len},
            ))
        
        # --- Effectiveness-based suggestions ---
        
        if effectiveness.get('avg_satisfaction', 1) < 0.5:
            suggestions.append(ImprovementSuggestion(
                character_id=char_id,
                parameter='system_prompt_addon',
                field='satisfaction_boost',
                current_value='',
                suggested_value='Focus on understanding the user\'s core concern before offering advice. '
                               'Ask clarifying questions when the situation is ambiguous. '
                               'End responses with a specific, actionable next step.',
                reason=f"Satisfaction estimate low ({effectiveness['avg_satisfaction']:.2f}). "
                       f"Adding prompt guidance for better user outcomes.",
                confidence=0.7,
                evidence={'satisfaction': effectiveness['avg_satisfaction'],
                          'sample': effectiveness.get('count', 0)},
            ))
        
        # Low engagement rate
        if effectiveness.get('high_engagement_pct', 100) < 30:
            suggestions.append(ImprovementSuggestion(
                character_id=char_id,
                parameter='trait_vector',
                field='intensity',
                current_value=None,
                suggested_value='+0.03',
                reason=f"Only {effectiveness['high_engagement_pct']:.0f}% high-engagement conversations. "
                       f"Slightly increasing intensity to encourage deeper interaction.",
                confidence=0.5,
                evidence={'high_engagement_pct': effectiveness['high_engagement_pct']},
            ))
        
        return suggestions
    
    def _generate_global_suggestions(self, char_quality: Dict,
                                      char_patterns: Dict) -> List[ImprovementSuggestion]:
        """Generate system-wide suggestions not tied to a specific character."""
        suggestions = []
        
        # Calculate global averages
        if char_quality:
            all_overall = [q['overall'] for q in char_quality.values() if q.get('overall')]
            if all_overall:
                global_avg = sum(all_overall) / len(all_overall)
                
                # Find worst-performing character
                worst_char = min(char_quality.items(), key=lambda x: x[1].get('overall', 1))
                if worst_char[1].get('overall', 1) < 0.4:
                    suggestions.append(ImprovementSuggestion(
                        character_id=worst_char[0],
                        parameter='system_prompt_addon',
                        field='major_revision_needed',
                        current_value='',
                        suggested_value=f'[AUTO-FLAG] This character scored {worst_char[1]["overall"]:.2f} overall. '
                                        f'Consider a full prompt rewrite.',
                        reason=f"Character '{worst_char[0]}' has critically low quality ({worst_char[1]['overall']:.2f}). "
                               f"Global average is {global_avg:.2f}.",
                        confidence=0.8,
                        evidence={'char_score': worst_char[1]['overall'], 'global_avg': global_avg},
                    ))
        
        return suggestions
    
    # ================================================================
    # APPLYING SUGGESTIONS
    # ================================================================
    
    def _apply_suggestion(self, suggestion: ImprovementSuggestion) -> bool:
        """Apply a single suggestion to the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            cursor = conn.cursor()
            
            if suggestion.parameter == 'trait_vector':
                return self._apply_trait_change(cursor, conn, suggestion)
            elif suggestion.parameter == 'system_prompt_addon':
                return self._apply_prompt_addon(cursor, conn, suggestion)
            elif suggestion.parameter == 'style_config':
                return self._apply_style_change(cursor, conn, suggestion)
            
            conn.close()
            return False
        except Exception as e:
            print(f"  ❌ Failed to apply {suggestion.field}: {e}")
            return False
    
    def _apply_trait_change(self, cursor, conn, suggestion: ImprovementSuggestion) -> bool:
        """Apply a trait vector adjustment."""
        # Look up current trait value from character_library
        cursor.execute("""
            SELECT trait_vector FROM character_library
            WHERE character_id = ?
        """, (suggestion.character_id,))
        
        row = cursor.fetchone()
        if not row:
            print(f"  ⚠️ Character '{suggestion.character_id}' not in character_library")
            return False
        
        traits = json.loads(row[0]) if row[0] else {}
        current = traits.get(suggestion.field, 0.5)
        suggestion.current_value = current
        
        # Parse delta
        delta_str = str(suggestion.suggested_value)
        if delta_str.startswith('+'):
            delta = float(delta_str)
        elif delta_str.startswith('-'):
            delta = float(delta_str)
        else:
            delta = float(delta_str) - current
        
        # Clamp delta
        delta = max(-self.MAX_TRAIT_DELTA, min(self.MAX_TRAIT_DELTA, delta))
        new_value = max(0.0, min(1.0, current + delta))
        
        traits[suggestion.field] = round(new_value, 3)
        
        cursor.execute("""
            UPDATE character_library SET trait_vector = ? WHERE character_id = ?
        """, (json.dumps(traits), suggestion.character_id))
        conn.commit()
        
        suggestion.suggested_value = round(new_value, 3)
        print(f"  ✅ {suggestion.character_id}.{suggestion.field}: {current:.3f} → {new_value:.3f} (Δ{delta:+.3f})")
        return True
    
    def _apply_prompt_addon(self, cursor, conn, suggestion: ImprovementSuggestion) -> bool:
        """Store a prompt addon in the improvement log table."""
        # Create table if needed
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS character_prompt_addons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id TEXT NOT NULL,
                addon_type TEXT NOT NULL,
                addon_text TEXT NOT NULL,
                reason TEXT,
                confidence REAL,
                applied_at TEXT DEFAULT (datetime('now')),
                active INTEGER DEFAULT 1
            )
        """)
        
        cursor.execute("""
            INSERT INTO character_prompt_addons (character_id, addon_type, addon_text, reason, confidence)
            VALUES (?, ?, ?, ?, ?)
        """, (suggestion.character_id, suggestion.field, suggestion.suggested_value,
              suggestion.reason, suggestion.confidence))
        conn.commit()
        
        print(f"  ✅ Prompt addon stored for {suggestion.character_id}: {suggestion.field}")
        return True
    
    def _apply_style_change(self, cursor, conn, suggestion: ImprovementSuggestion) -> bool:
        """Apply a style config change."""
        # Store in a config override table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS character_style_overrides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id TEXT NOT NULL,
                field TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                reason TEXT,
                applied_at TEXT DEFAULT (datetime('now')),
                active INTEGER DEFAULT 1
            )
        """)
        
        cursor.execute("""
            INSERT INTO character_style_overrides (character_id, field, old_value, new_value, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (suggestion.character_id, suggestion.field,
              str(suggestion.current_value), str(suggestion.suggested_value),
              suggestion.reason))
        conn.commit()
        
        print(f"  ✅ Style override stored for {suggestion.character_id}.{suggestion.field}")
        return True
    
    def _log_improvement(self, suggestion: ImprovementSuggestion):
        """Log an applied improvement."""
        record = {
            'timestamp': datetime.now().isoformat(),
            'character_id': suggestion.character_id,
            'parameter': suggestion.parameter,
            'field': suggestion.field,
            'current_value': suggestion.current_value,
            'new_value': suggestion.suggested_value,
            'reason': suggestion.reason,
            'confidence': suggestion.confidence,
        }
        self.improvement_log.append(record)
        
        # Publish to Event Bus
        if self.event_bus:
            self.event_bus.publish_async('character.effectiveness_update', {
                'character_id': suggestion.character_id,
                'improvement': suggestion.field,
                'reason': suggestion.reason,
            }, source='self_improvement_agent')
    
    # ================================================================
    # REPORTING
    # ================================================================
    
    def print_report(self, report: ImprovementReport):
        """Print a formatted improvement report."""
        print(f"\n{'='*60}")
        print(f"SELF-IMPROVEMENT REPORT")
        print(f"Generated: {report.generated_at}")
        print(f"{'='*60}")
        
        # Character analyses
        for char_id, analysis in report.character_analyses.items():
            quality = analysis.get('quality', {})
            eff = analysis.get('effectiveness', {})
            patterns = analysis.get('patterns', {})
            
            print(f"\n  📊 {char_id}")
            print(f"     Samples: {analysis['sample_size']}")
            
            if quality:
                print(f"     Quality: overall={quality.get('overall', '?')}"
                      f"  coherence={quality.get('coherence', '?')}"
                      f"  helpfulness={quality.get('helpfulness', '?')}"
                      f"  engagement={quality.get('engagement', '?')}")
            
            if eff:
                print(f"     Effectiveness: satisfaction={eff.get('avg_satisfaction', '?')}"
                      f"  engagement={eff.get('high_engagement_pct', '?')}%")
            
            if patterns:
                print(f"     Patterns: avg_response={patterns.get('avg_response_length', '?')} chars"
                      f"  avg_msgs/convo={patterns.get('avg_msgs_per_convo', '?')}")
            
            if analysis.get('skip_reason'):
                print(f"     ⏭️  {analysis['skip_reason']}")
        
        # Suggestions
        print(f"\n  {'─'*50}")
        print(f"  SUGGESTIONS ({len(report.suggestions)} total)")
        print(f"  {'─'*50}")
        
        for s in report.suggestions:
            icon = '🟢' if s.confidence >= 0.7 else '🟡' if s.confidence >= 0.5 else '🔴'
            print(f"\n  {icon} [{s.character_id}] {s.parameter}.{s.field}")
            print(f"     Change: {s.current_value} → {s.suggested_value}")
            print(f"     Reason: {s.reason}")
            print(f"     Confidence: {s.confidence:.2f}")
        
        if not report.suggestions:
            print(f"\n  ✅ No improvements suggested — all characters performing well!")
        
        # Applied / Skipped
        if report.applied:
            print(f"\n  ✅ Applied: {len(report.applied)} changes")
        if report.skipped:
            print(f"  ⏭️  Skipped: {len(report.skipped)} changes")
            for s, reason in report.skipped[:5]:
                print(f"     - {s.character_id}.{s.field}: {reason}")
        
        print(f"\n{'='*60}")


# ================================================================
# CLI
# ================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Self-Improvement Agent')
    parser.add_argument('--db', type=str, help='Path to smart_response.db')
    parser.add_argument('--days', type=int, default=14, help='Days of data to analyze')
    parser.add_argument('--min-convos', type=int, default=5, help='Minimum conversations per character')
    parser.add_argument('--apply', action='store_true', help='Apply suggestions (default: dry-run)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without applying')
    args = parser.parse_args()
    
    agent = SelfImprovementAgent(db_path=args.db)
    
    print("🧠 Self-Improvement Agent — Analyzing...")
    report = agent.analyze(days=args.days, min_convos=args.min_convos)
    
    dry_run = not args.apply
    report = agent.apply_suggestions(report, dry_run=dry_run)
    
    agent.print_report(report)
    
    if dry_run and report.suggestions:
        print(f"\n💡 Run with --apply to apply {len(report.suggestions)} suggestions")

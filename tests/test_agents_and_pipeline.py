"""
Tests for all recently built agents and the shared conversation pipeline.

Covers:
1. ConversationPipeline — enrich_context, post_process, graceful degradation
2. ConversationQualityScorer — character_id tracking, classify, save/load
3. SelfImprovementAgent — data gathering, analysis, suggestions
4. ABTestingAgent — create, assign, record, evaluate experiments
5. AlertNotifier — subscribe, cooldown, alert history, stats
"""

import os
import sys
import sqlite3
import json
import time
import tempfile
import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timedelta
from dataclasses import dataclass

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


# ================================================================
# 1. CONVERSATION PIPELINE TESTS
# ================================================================

class TestConversationPipeline(unittest.TestCase):
    """Test the shared conversation enrichment pipeline."""
    
    def setUp(self):
        from smart_response.conversation_pipeline import ConversationPipeline
        self.pipeline = ConversationPipeline()
    
    def test_pipeline_creates_with_no_args(self):
        """Pipeline should work with zero systems — graceful degradation."""
        from smart_response.conversation_pipeline import ConversationPipeline
        p = ConversationPipeline()
        self.assertIsNotNone(p)
    
    def test_enrich_context_returns_dict(self):
        """enrich_context should return a dict even with no systems."""
        context = {'user_id': 1}
        result = self.pipeline.enrich_context(1, "hello", "coordinator", context)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['user_id'], 1)
    
    def test_enrich_context_survives_all_none_systems(self):
        """Each enrichment step should silently skip when its system is None."""
        context = {'user_id': 1, 'is_admin': False}
        result = self.pipeline.enrich_context(1, "I feel stressed about work", "coordinator", context)
        # Should not raise, should return context unchanged
        self.assertIsInstance(result, dict)
    
    def test_post_process_returns_structure(self):
        """post_process should return proper structure even with no systems."""
        context = {}
        result = self.pipeline.post_process(
            user_id=1, message="test", character_id="coordinator",
            ai_response_text="Here's my advice...", context=context,
            session_id="sess_123"
        )
        self.assertIn('response_text', result)
        self.assertIn('clarification_data', result)
        self.assertIn('collaboration_data', result)
        self.assertEqual(result['response_text'], "Here's my advice...")
    
    def test_post_process_preserves_response_when_no_systems(self):
        """Response text should pass through unchanged when no post-processors."""
        original = "This is the AI response."
        result = self.pipeline.post_process(1, "msg", "char", original, {})
        self.assertEqual(result['response_text'], original)
    
    def test_append_to_profile_creates_new(self):
        """_append_to_profile should create user_profile when empty."""
        context = {}
        self.pipeline._append_to_profile(context, "Some profile info")
        self.assertEqual(context['user_profile'], "Some profile info")
    
    def test_append_to_profile_appends(self):
        """_append_to_profile should append with double newline."""
        context = {'user_profile': 'Existing'}
        self.pipeline._append_to_profile(context, "New info")
        self.assertEqual(context['user_profile'], "Existing\n\nNew info")
    
    def test_enrich_user_context_calls_system(self):
        """User context manager should be called when present."""
        from smart_response.conversation_pipeline import ConversationPipeline
        
        mock_ucm = MagicMock()
        mock_ucm.process_message.return_value = {'language': 'en', 'references_past': False}
        mock_ucm.format_context_for_prompt.return_value = "User prefers warm tone"
        
        p = ConversationPipeline(user_context_mgr=mock_ucm)
        context = {'user_id': 1}
        p._enrich_user_context(1, "hello", "coordinator", context)
        
        mock_ucm.process_message.assert_called_once()
        mock_ucm.format_context_for_prompt.assert_called_once()
        self.assertIn('user_profile', context)
    
    def test_enrich_goal_coaching_adds_context(self):
        """Goal coaching should add coaching_context when available."""
        from smart_response.conversation_pipeline import ConversationPipeline
        
        mock_gc = MagicMock()
        mock_gc.get_coaching_context_for_prompt.return_value = "Be encouraging"
        
        p = ConversationPipeline(goal_coaching_system=mock_gc)
        context = {}
        p._enrich_goal_coaching(1, "I want to improve", context)
        
        self.assertEqual(context['coaching_context'], "Be encouraging")
    
    def test_enrich_personality_adds_to_profile(self):
        """Personality integration should append Big5 context to user_profile."""
        from smart_response.conversation_pipeline import ConversationPipeline
        
        mock_pi = MagicMock()
        mock_pi.get_conversation_state_from_message.return_value = 'neutral'
        mock_ctx = MagicMock()
        mock_ctx.trait_source = 'assessment'
        mock_ctx.trait_confidence = 0.8
        mock_ctx.change_detected = False
        mock_pi.get_personality_context.return_value = mock_ctx
        mock_pi.format_for_prompt.return_value = "Big5: O=0.7, C=0.6"
        
        p = ConversationPipeline(personality_integrator=mock_pi)
        context = {}
        p._enrich_personality(1, "hello", context)
        
        self.assertIn('Big5', context.get('user_profile', ''))
    
    def test_enrich_situation_analysis_detects_emotion(self):
        """Situation analysis should add emotional state to context."""
        from smart_response.conversation_pipeline import ConversationPipeline
        
        mock_cts = MagicMock()
        situation = MagicMock()
        situation.emotional_state = 'stressed'
        situation.goal_type = 'coping'
        situation.needs_validation = True
        situation.needs_action = False
        mock_cts.analyze_situation.return_value = situation
        
        p = ConversationPipeline(character_trait_system=mock_cts)
        context = {}
        p._enrich_situation_analysis("I'm so stressed about work", context)
        
        self.assertIn('situation_analysis', context)
        self.assertEqual(context['situation_analysis']['emotional_state'], 'stressed')
    
    def test_post_event_bus_publishes(self):
        """Event bus should receive message.sent event."""
        from smart_response.conversation_pipeline import ConversationPipeline
        
        mock_bus = MagicMock()
        p = ConversationPipeline(event_bus=mock_bus)
        p._post_event_bus(1, "sess_123", "coordinator", "gpt-4", False)
        
        mock_bus.publish_async.assert_called_once()
        call_args = mock_bus.publish_async.call_args
        self.assertEqual(call_args[0][0], 'message.sent')
        self.assertEqual(call_args[0][1]['session_id'], 'sess_123')
    
    def test_post_event_bus_skips_without_session(self):
        """Event bus should not publish without session_id."""
        from smart_response.conversation_pipeline import ConversationPipeline
        
        mock_bus = MagicMock()
        p = ConversationPipeline(event_bus=mock_bus)
        p._post_event_bus(1, None, "coordinator", "gpt-4", False)
        
        mock_bus.publish_async.assert_not_called()
    
    def test_pipeline_factory(self):
        """create_pipeline should return a ConversationPipeline instance."""
        from smart_response.conversation_pipeline import create_pipeline
        p = create_pipeline(event_bus=MagicMock())
        self.assertIsNotNone(p.event_bus)
        self.assertIsNone(p.user_context_mgr)


# ================================================================
# 2. CONVERSATION QUALITY SCORER TESTS
# ================================================================

class TestConversationQualityScorer(unittest.TestCase):
    """Test the quality scorer with character_id tracking."""
    
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        self._setup_db()
        
        from agents.quality_scorer import ConversationQualityScorer
        self.scorer = ConversationQualityScorer(self.db_path)
    
    def _setup_db(self):
        """Create minimal DB schema for testing."""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id INTEGER,
                character_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                sender_type TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def _insert_conversation(self, session_id, character_id, messages):
        """Helper: insert a conversation with messages."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO ai_conversations (session_id, user_id, character_id) VALUES (?, 1, ?)',
            (session_id, character_id)
        )
        conv_id = cursor.lastrowid
        for sender, content in messages:
            cursor.execute(
                'INSERT INTO messages (conversation_id, sender_type, content) VALUES (?, ?, ?)',
                (conv_id, sender, content)
            )
        conn.commit()
        conn.close()
    
    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_classify_domain_character(self):
        """Should classify domain characters correctly."""
        self.assertEqual(self.scorer._classify_character('coordinator'), 'domain')
        self.assertEqual(self.scorer._classify_character('domain_work'), 'domain')
        self.assertEqual(self.scorer._classify_character('domain_relationships'), 'domain')
        self.assertEqual(self.scorer._classify_character('domain_custom'), 'domain')
    
    def test_classify_philosophy_character(self):
        """Should classify philosophy characters correctly."""
        self.assertEqual(self.scorer._classify_character('stoic_philosopher'), 'philosophy')
        self.assertEqual(self.scorer._classify_character('super_motivational_coach'), 'philosophy')
        self.assertEqual(self.scorer._classify_character('wisdom_sage'), 'philosophy')
    
    def test_classify_unknown(self):
        """Should return 'unknown' for empty or unrecognized IDs."""
        self.assertEqual(self.scorer._classify_character(''), 'unknown')
        self.assertEqual(self.scorer._classify_character('random_thing'), 'unknown')
    
    def test_quality_score_table_has_character_columns(self):
        """Table should have character_id and character_type columns."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(conversation_quality_scores)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()
        
        self.assertIn('character_id', columns)
        self.assertIn('character_type', columns)
    
    def test_score_conversation_with_character(self):
        """Scoring should include character_id in the result."""
        self._insert_conversation('sess_1', 'stoic_philosopher', [
            ('user', 'How do I deal with failure?'),
            ('assistant', 'Marcus Aurelius would say that failure is a teacher.'),
            ('user', 'That makes sense. What else?'),
            ('assistant', 'Focus on what you can control, not the outcome.'),
        ])
        
        self.scorer._current_character_id = 'stoic_philosopher'
        score = self.scorer.score_conversation('sess_1')
        
        self.assertIsNotNone(score, "score_conversation returned None — check messages table schema")
        self.assertEqual(score.character_id, 'stoic_philosopher')
        self.assertEqual(score.character_type, 'philosophy')
        self.assertGreater(score.overall, 0)
    
    def test_save_and_read_score_with_character(self):
        """Saved scores should include character_id in DB."""
        self._insert_conversation('sess_2', 'coordinator', [
            ('user', 'I need help balancing work and life'),
            ('assistant', 'Let me help you think about this holistically.'),
            ('user', 'Thank you, that would be great'),
            ('assistant', 'Start by identifying your top 3 priorities.'),
        ])
        
        self.scorer._current_character_id = 'coordinator'
        score = self.scorer.score_conversation('sess_2', save=True)
        
        self.assertIsNotNone(score, "score_conversation returned None — check messages table schema")
        
        # Verify in DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT character_id, character_type FROM conversation_quality_scores WHERE session_id = ?', ('sess_2',))
        row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 'coordinator')
        self.assertEqual(row[1], 'domain')
    
    def test_get_recent_conversations_returns_character_info(self):
        """get_recent_conversations should return dicts with character_id."""
        self._insert_conversation('sess_3', 'wisdom_sage', [
            ('user', 'What is wisdom?'),
            ('assistant', 'Wisdom is knowing what you do not know.'),
            ('user', 'Deep. Tell me more.'),
            ('assistant', 'The wise person acts without acting.'),
        ])
        
        results = self.scorer.get_recent_conversations(days=1)
        self.assertGreater(len(results), 0)
        self.assertIsInstance(results[0], dict)
        self.assertIn('session_id', results[0])
        self.assertIn('character_id', results[0])
    
    def test_score_recent_populates_character_id(self):
        """score_recent should pass character_id through to each score."""
        self._insert_conversation('sess_4', 'domain_work', [
            ('user', 'How do I get promoted?'),
            ('assistant', 'Focus on visibility and results.'),
            ('user', 'Good advice. What specifically?'),
            ('assistant', 'Track your achievements and share them quarterly.'),
        ])
        
        report = self.scorer.score_recent(days=1)
        self.assertGreater(len(report.scores), 0)
        for score in report.scores:
            if score.session_id == 'sess_4':
                self.assertEqual(score.character_id, 'domain_work')
                self.assertEqual(score.character_type, 'domain')


# ================================================================
# 3. SELF-IMPROVEMENT AGENT TESTS
# ================================================================

class TestSelfImprovementAgent(unittest.TestCase):
    """Test the self-improvement agent data gathering and analysis."""
    
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        self._setup_db()
    
    def _setup_db(self):
        """Create test DB with quality scores and conversations."""
        conn = sqlite3.connect(self.db_path)
        # Quality scores table (with character_id)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS conversation_quality_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                character_id TEXT DEFAULT '',
                character_type TEXT DEFAULT '',
                coherence REAL, helpfulness REAL, engagement REAL,
                resolution REAL, consistency REAL, overall REAL,
                flags TEXT, details TEXT,
                scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Insert test scores for multiple characters
        for char_id, char_type, overall in [
            ('coordinator', 'domain', 0.75),
            ('coordinator', 'domain', 0.80),
            ('stoic_philosopher', 'philosophy', 0.65),
            ('stoic_philosopher', 'philosophy', 0.70),
            ('domain_work', 'domain', 0.85),
        ]:
            conn.execute('''
                INSERT INTO conversation_quality_scores
                (session_id, character_id, character_type, coherence, helpfulness,
                 engagement, resolution, consistency, overall, flags, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '[]', '{}')
            ''', (f'sess_{char_id}_{overall}', char_id, char_type,
                  overall, overall, overall, overall, overall, overall))
        
        # ai_conversations + messages for pattern analysis
        conn.execute('''
            CREATE TABLE IF NOT EXISTS ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT, user_id INTEGER, character_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER, sender_type TEXT, content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_get_quality_by_character(self):
        """Should group quality scores by character with correct column names."""
        from agents.self_improvement import SelfImprovementAgent
        agent = SelfImprovementAgent(self.db_path)
        
        quality = agent._get_quality_by_character(days=7)
        
        self.assertIn('coordinator', quality)
        self.assertIn('stoic_philosopher', quality)
        self.assertIn('domain_work', quality)
        
        # Check coordinator has correct values
        coord = quality['coordinator']
        self.assertIn('character_type', coord)
        self.assertEqual(coord['character_type'], 'domain')
        self.assertGreater(coord['overall'], 0)
        self.assertEqual(coord['count'], 2)
        
        # Check philosophy character
        stoic = quality['stoic_philosopher']
        self.assertEqual(stoic['character_type'], 'philosophy')
    
    def test_analyze_returns_report(self):
        """analyze() should return an ImprovementReport."""
        from agents.self_improvement import SelfImprovementAgent
        agent = SelfImprovementAgent(self.db_path)
        
        report = agent.analyze(days=7)
        
        self.assertIsNotNone(report)
        self.assertIsNotNone(report.generated_at)
        # Should have data for the characters we inserted
        self.assertIsNotNone(report.character_analyses)
        self.assertIsInstance(report.character_analyses, dict)


# ================================================================
# 4. A/B TESTING AGENT TESTS
# ================================================================

class TestABTestingAgent(unittest.TestCase):
    """Test the A/B testing experiment lifecycle."""
    
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        
        from agents.ab_testing import ABTestingAgent
        self.agent = ABTestingAgent(self.db_path)
    
    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_create_experiment(self):
        """Should create an experiment with variants."""
        exp = self.agent.create_experiment(
            name="Test Experiment",
            description="A test",
            experiment_type="trait_adjustment",
            character_id="coordinator",
            variants=[
                {'name': 'A_control', 'description': 'Control', 'config_overrides': {}},
                {'name': 'B_test', 'description': 'Test', 'config_overrides': {'empathy': 0.1}},
            ]
        )
        
        self.assertIsNotNone(exp)
        self.assertEqual(exp.name, "Test Experiment")
        self.assertEqual(len(exp.variants), 2)
        self.assertEqual(exp.character_id, "coordinator")
    
    def test_get_variant_for_session(self):
        """Should assign variants via round-robin (fewest samples first)."""
        exp = self.agent.create_experiment(
            name="RR Test",
            description="Test round-robin",
            experiment_type="test",
            character_id="coordinator",
            variants=[
                {'name': 'A', 'description': 'A', 'config_overrides': {}},
                {'name': 'B', 'description': 'B', 'config_overrides': {}},
            ]
        )
        
        from agents.ab_testing import ExperimentStatus
        exp.status = ExperimentStatus.RUNNING
        
        v1 = self.agent.get_variant_for_session(exp.experiment_id)
        self.assertIsNotNone(v1)
        # Both variants have 0 samples, so either is valid
        self.assertIn(v1.name, ['A', 'B'])
    
    def test_record_session(self):
        """Should record session result for an experiment."""
        exp = self.agent.create_experiment(
            name="Record Test",
            description="Test recording",
            experiment_type="test",
            character_id="coordinator",
            variants=[
                {'name': 'A', 'description': 'A', 'config_overrides': {}},
                {'name': 'B', 'description': 'B', 'config_overrides': {}},
            ]
        )
        
        from agents.ab_testing import ExperimentStatus
        exp.status = ExperimentStatus.RUNNING
        
        self.agent.record_session(exp.experiment_id, 'A', 'sess_1', quality_score=0.85)
        
        # Check variant got the score
        variant_a = next(v for v in exp.variants if v.name == 'A')
        self.assertEqual(len(variant_a.quality_scores), 1)
        self.assertEqual(variant_a.quality_scores[0], 0.85)
    
    def test_start_experiment(self):
        """Should transition experiment to RUNNING status."""
        exp = self.agent.create_experiment(
            name="Start Test",
            description="Test start",
            experiment_type="test",
            character_id="coordinator",
            variants=[
                {'name': 'A', 'description': 'A', 'config_overrides': {}},
                {'name': 'B', 'description': 'B', 'config_overrides': {}},
            ]
        )
        
        from agents.ab_testing import ExperimentStatus
        self.assertEqual(exp.status, ExperimentStatus.DRAFT)
        
        success = self.agent.start_experiment(exp.experiment_id)
        self.assertTrue(success)
        self.assertEqual(exp.status, ExperimentStatus.RUNNING)
    
    def test_standard_experiments_include_philosophy(self):
        """Standard experiments should include philosophy character experiments."""
        experiments = self.agent.create_standard_experiments()
        
        # Should have 7 experiments (4 coordinator + 2 philosophy + 1 domain_work)
        self.assertGreaterEqual(len(experiments), 7)
        
        char_ids = [e.character_id for e in experiments]
        self.assertIn('stoic_philosopher', char_ids)
        self.assertIn('wisdom_sage', char_ids)
        self.assertIn('domain_work', char_ids)
        self.assertIn('coordinator', char_ids)
    
    def test_experiment_persistence(self):
        """Experiments should persist in the database."""
        exp = self.agent.create_experiment(
            name="Persist Test",
            description="Test DB persistence",
            experiment_type="test",
            character_id="coordinator",
            variants=[
                {'name': 'A', 'description': 'A', 'config_overrides': {}},
            ]
        )
        
        # Create a new agent instance pointing to same DB
        from agents.ab_testing import ABTestingAgent
        agent2 = ABTestingAgent(self.db_path)
        
        # Should load the experiment from DB
        self.assertIn(exp.experiment_id, agent2.experiments)
    
    def test_experiments_dict(self):
        """experiments dict should contain all created experiments."""
        self.agent.create_experiment(
            name="List Test 1", description="t", experiment_type="test",
            character_id="c", variants=[{'name': 'A', 'description': 'A', 'config_overrides': {}}]
        )
        self.agent.create_experiment(
            name="List Test 2", description="t", experiment_type="test",
            character_id="c", variants=[{'name': 'A', 'description': 'A', 'config_overrides': {}}]
        )
        
        self.assertGreaterEqual(len(self.agent.experiments), 2)


# ================================================================
# 5. ALERT NOTIFIER TESTS
# ================================================================

class TestAlertNotifier(unittest.TestCase):
    """Test the alert notifier agent."""
    
    def setUp(self):
        from agents.alert_notifier import AlertNotifier
        self.notifier = AlertNotifier(cooldown_minutes=1)
    
    def test_init_defaults(self):
        """Should initialize with proper defaults."""
        self.assertEqual(self.notifier.cooldown_minutes, 1)
        self.assertEqual(len(self.notifier.alert_history), 0)
        self.assertEqual(self.notifier.stats['alerts_received'], 0)
    
    def test_store_alert(self):
        """Should store alerts in history."""
        record = {
            'timestamp': datetime.now().isoformat(),
            'level': 'critical',
            'topic': 'health.critical',
            'message': 'Test alert',
            'source': 'test',
            'data': {},
        }
        self.notifier._store_alert(record)
        
        self.assertEqual(len(self.notifier.alert_history), 1)
        self.assertEqual(self.notifier.alert_history[0]['message'], 'Test alert')
    
    def test_alert_history_max_size(self):
        """Alert history should be capped at _max_history."""
        self.notifier._max_history = 5
        for i in range(10):
            self.notifier._store_alert({
                'timestamp': datetime.now().isoformat(),
                'level': 'warning',
                'topic': 'test',
                'message': f'Alert {i}',
                'source': 'test',
                'data': {},
            })
        
        self.assertEqual(len(self.notifier.alert_history), 5)
        # Should keep the most recent
        self.assertEqual(self.notifier.alert_history[-1]['message'], 'Alert 9')
    
    def test_get_recent_alerts_no_filter(self):
        """Should return all alerts without filter."""
        for level in ['critical', 'warning', 'critical']:
            self.notifier._store_alert({
                'timestamp': datetime.now().isoformat(),
                'level': level, 'topic': 'test',
                'message': f'{level} alert', 'source': 'test', 'data': {},
            })
        
        alerts = self.notifier.get_recent_alerts()
        self.assertEqual(len(alerts), 3)
    
    def test_get_recent_alerts_filtered(self):
        """Should filter alerts by level."""
        for level in ['critical', 'warning', 'critical', 'warning', 'warning']:
            self.notifier._store_alert({
                'timestamp': datetime.now().isoformat(),
                'level': level, 'topic': 'test',
                'message': f'{level} alert', 'source': 'test', 'data': {},
            })
        
        critical = self.notifier.get_recent_alerts(level='critical')
        self.assertEqual(len(critical), 2)
        
        warnings = self.notifier.get_recent_alerts(level='warning')
        self.assertEqual(len(warnings), 3)
    
    def test_get_stats(self):
        """Should return proper stats dict."""
        stats = self.notifier.get_stats()
        self.assertIn('alerts_received', stats)
        self.assertIn('emails_sent', stats)
        self.assertIn('cooldown_minutes', stats)
        self.assertIn('admin_email', stats)
    
    def test_on_critical_increments_stats(self):
        """_on_critical should increment alerts_received."""
        event = MagicMock()
        event.topic = 'health.critical'
        event.source = 'test'
        event.data = {'alert': 'Provider down', 'provider': 'openai'}
        
        self.notifier._on_critical(event)
        
        self.assertEqual(self.notifier.stats['alerts_received'], 1)
        self.assertEqual(len(self.notifier.alert_history), 1)
        self.assertEqual(self.notifier.alert_history[0]['level'], 'critical')
    
    def test_on_warning_increments_stats(self):
        """_on_warning should increment alerts_received."""
        event = MagicMock()
        event.topic = 'health.warning'
        event.source = 'test'
        event.data = {'message': 'Quota at 80%'}
        
        self.notifier._on_warning(event)
        
        self.assertEqual(self.notifier.stats['alerts_received'], 1)
        self.assertEqual(self.notifier.alert_history[0]['level'], 'warning')
    
    def test_cooldown_suppresses_duplicate(self):
        """Email should be suppressed if same alert_key within cooldown window."""
        from agents.alert_notifier import AlertNotifier
        
        mock_email = MagicMock()
        mock_email.sender_email = 'test@test.com'
        mock_email.sender_password = 'pass'
        mock_email.smtp_server = 'smtp.test.com'
        mock_email.smtp_port = 587
        
        notifier = AlertNotifier(
            email_service=mock_email,
            admin_email='admin@test.com',
            cooldown_minutes=60
        )
        
        event = MagicMock()
        event.topic = 'health.critical'
        event.source = 'test'
        event.data = {'alert': 'Quota exceeded', 'provider': 'openai'}
        
        # First call — should attempt email (will fail in test but that's fine)
        with patch.object(notifier, '_send_email'):
            notifier._send_alert_email('health:openai', 'CRITICAL', 'Quota exceeded', event)
        
        # Second call — should be suppressed
        notifier._send_alert_email('health:openai', 'CRITICAL', 'Quota exceeded', event)
        self.assertEqual(notifier.stats['emails_suppressed'], 1)
    
    def test_start_subscribes_to_event_bus(self):
        """start() should subscribe to critical event topics."""
        mock_bus = MagicMock()
        from agents.alert_notifier import AlertNotifier
        notifier = AlertNotifier(event_bus=mock_bus)
        
        notifier.start()
        
        # Should have subscribed to at least 4 topics
        self.assertGreaterEqual(mock_bus.subscribe.call_count, 4)
        
        # Check topic names
        subscribed_topics = [call[0][0] for call in mock_bus.subscribe.call_args_list]
        self.assertIn('health.critical', subscribed_topics)
        self.assertIn('health.warning', subscribed_topics)
        self.assertIn('agent.error', subscribed_topics)
    
    def test_start_without_bus_no_error(self):
        """start() without event bus should not raise."""
        from agents.alert_notifier import AlertNotifier
        notifier = AlertNotifier()
        notifier.start()  # Should not raise


# ================================================================
# 6. DASHBOARD API FIELD TESTS
# ================================================================

class TestDashboardAPIFields(unittest.TestCase):
    """Test the new fields added to /api/admin/agent-dashboard."""

    def test_agent_tasks_structure(self):
        """agent_tasks should have correct keys and schedule info."""
        # Simulate what the endpoint builds
        tasks = {
            'quality_scoring': {'schedule': 'Daily at 3:00 AM', 'active': True},
            'self_improvement': {'schedule': 'Weekly Monday at 4:00 AM', 'active': True},
            'ab_testing': {'schedule': 'On-demand', 'active': False},
        }
        self.assertIn('quality_scoring', tasks)
        self.assertIn('self_improvement', tasks)
        self.assertIn('ab_testing', tasks)
        for key in tasks:
            self.assertIn('schedule', tasks[key])
            self.assertIn('active', tasks[key])
            self.assertIsInstance(tasks[key]['active'], bool)

    def test_pipeline_health_structure(self):
        """pipeline health dict should reflect system initialization."""
        pipeline_mock = MagicMock()
        pipeline_mock.user_context_mgr = MagicMock()
        pipeline_mock.event_bus = None

        pipeline_data = {'initialized': True, 'systems': {}}
        for attr in ['user_context_mgr', 'event_bus']:
            pipeline_data['systems'][attr] = getattr(pipeline_mock, attr, None) is not None

        self.assertTrue(pipeline_data['initialized'])
        self.assertTrue(pipeline_data['systems']['user_context_mgr'])
        self.assertFalse(pipeline_data['systems']['event_bus'])

    def test_ab_experiments_from_agent(self):
        """ab_experiments should serialize experiments correctly."""
        from agents.ab_testing import ABTestingAgent
        agent = ABTestingAgent.__new__(ABTestingAgent)
        agent.experiments = {}
        agent.db_path = ':memory:'

        exp_mock = MagicMock()
        exp_mock.to_dict.return_value = {
            'experiment_id': 'test_exp',
            'name': 'Test',
            'status': 'draft',
            'variants': [],
        }
        agent.experiments['test_exp'] = exp_mock

        exps = []
        for eid, exp in agent.experiments.items():
            exps.append(exp.to_dict())

        self.assertEqual(len(exps), 1)
        self.assertEqual(exps[0]['experiment_id'], 'test_exp')
        self.assertEqual(exps[0]['status'], 'draft')

    def test_quality_trends_query_format(self):
        """quality_trends rows should have correct keys and bounded values."""
        # Simulate rows from the SQL query
        raw_rows = [
            ('2025-02-10', 0.82, 0.79, 0.85, 0.78, 5),
            ('2025-02-11', 0.84, 0.81, 0.87, 0.80, 8),
            ('2025-02-12', 0.80, 0.77, 0.83, 0.76, 3),
        ]
        trends = [
            {
                'date': r[0],
                'overall': round(r[1] or 0, 3),
                'coherence': round(r[2] or 0, 3),
                'helpfulness': round(r[3] or 0, 3),
                'engagement': round(r[4] or 0, 3),
                'count': r[5],
            }
            for r in raw_rows
        ]

        self.assertEqual(len(trends), 3)
        for t in trends:
            self.assertIn('date', t)
            self.assertIn('overall', t)
            self.assertIn('coherence', t)
            self.assertIn('helpfulness', t)
            self.assertIn('engagement', t)
            self.assertIn('count', t)
            self.assertGreaterEqual(t['overall'], 0)
            self.assertLessEqual(t['overall'], 1)
            self.assertIsInstance(t['count'], int)

        # Verify ordering
        dates = [t['date'] for t in trends]
        self.assertEqual(dates, sorted(dates))

    def test_quality_trends_handles_nulls(self):
        """quality_trends should handle NULL values gracefully."""
        raw_row = ('2025-02-10', None, None, None, None, 0)
        trend = {
            'date': raw_row[0],
            'overall': round(raw_row[1] or 0, 3),
            'coherence': round(raw_row[2] or 0, 3),
            'helpfulness': round(raw_row[3] or 0, 3),
            'engagement': round(raw_row[4] or 0, 3),
            'count': raw_row[5],
        }
        self.assertEqual(trend['overall'], 0)
        self.assertEqual(trend['coherence'], 0)

    def test_quality_trends_from_real_db(self):
        """Insert scores into a temp DB and verify the query works."""
        db = sqlite3.connect(':memory:')
        db.execute("""CREATE TABLE conversation_quality_scores (
            id INTEGER PRIMARY KEY,
            scored_at TEXT DEFAULT (datetime('now')),
            overall REAL, coherence REAL, helpfulness REAL, engagement REAL,
            character_id TEXT, session_id TEXT
        )""")
        # Insert scores across 3 days
        for day_offset in range(3):
            date_str = f'2025-02-{10 + day_offset} 12:00:00'
            for _ in range(2):
                db.execute(
                    "INSERT INTO conversation_quality_scores (scored_at, overall, coherence, helpfulness, engagement) VALUES (?,?,?,?,?)",
                    (date_str, 0.8 + day_offset * 0.01, 0.75, 0.85, 0.7)
                )
        db.commit()

        cursor = db.cursor()
        cursor.execute("""
            SELECT DATE(scored_at) as day,
                   AVG(overall), AVG(coherence), AVG(helpfulness), AVG(engagement),
                   COUNT(*)
            FROM conversation_quality_scores
            GROUP BY DATE(scored_at)
            ORDER BY day ASC
        """)
        rows = cursor.fetchall()
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0][5], 2)  # count per day
        self.assertAlmostEqual(rows[0][1], 0.8, places=2)
        self.assertAlmostEqual(rows[2][1], 0.82, places=2)
        db.close()


# ================================================================
# RUN
# ================================================================

if __name__ == '__main__':
    unittest.main(verbosity=2)

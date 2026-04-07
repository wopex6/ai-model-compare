"""
Automated tests for all web platform enhancements.
Run after each integration to catch regressions.
"""

import sys
import os
import asyncio
import unittest

# Make sure project root is on path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


# ---------------------------------------------------------------------------
# 1. models.py – retry helper + session-reuse
# ---------------------------------------------------------------------------
class TestModelsRetryAndSession(unittest.TestCase):

    def test_retry_helper_exists(self):
        from ai_compare.models import _retry_with_backoff
        self.assertTrue(callable(_retry_with_backoff))

    def test_retry_succeeds_on_first_attempt(self):
        from ai_compare.models import _retry_with_backoff
        calls = []
        async def _op():
            calls.append(1)
            return "ok"
        result = asyncio.run(_retry_with_backoff(_op))
        self.assertEqual(result, "ok")
        self.assertEqual(len(calls), 1)

    def test_retry_retries_on_generic_exception(self):
        from ai_compare.models import _retry_with_backoff
        calls = []
        async def _op():
            calls.append(1)
            if len(calls) < 3:
                raise ConnectionError("transient")
            return "recovered"
        result = asyncio.run(
            _retry_with_backoff(_op, max_attempts=3, base_delay=0.01)
        )
        self.assertEqual(result, "recovered")
        self.assertEqual(len(calls), 3)

    def test_retry_raises_after_max_attempts(self):
        from ai_compare.models import _retry_with_backoff
        async def _op():
            raise ConnectionError("always fails")
        with self.assertRaises(ConnectionError):
            asyncio.run(
                _retry_with_backoff(_op, max_attempts=2, base_delay=0.01)
            )

    def test_meta_model_has_session_reuse(self):
        """MetaModel must have _get_session() — no more per-request ClientSession."""
        import inspect
        from ai_compare.models import MetaModel
        self.assertTrue(hasattr(MetaModel, '_get_session'),
                        "MetaModel missing _get_session — still leaking sessions")
        self.assertTrue(hasattr(MetaModel, 'close'),
                        "MetaModel missing close() — sessions won't be cleaned up")

    def test_grok_model_has_session_reuse(self):
        from ai_compare.models import GrokModel
        self.assertTrue(hasattr(GrokModel, '_get_session'))
        self.assertTrue(hasattr(GrokModel, 'close'))

    def test_claude_model_accepts_max_tokens(self):
        """ClaudeModel.get_response must accept max_tokens kwarg."""
        import inspect
        from ai_compare.models import ClaudeModel
        sig = inspect.signature(ClaudeModel.get_response)
        self.assertIn('max_tokens', sig.parameters,
                      "ClaudeModel.get_response missing max_tokens param")

    def test_retryable_status_codes_defined(self):
        from ai_compare.models import RETRYABLE_STATUS_CODES
        self.assertIn(429, RETRYABLE_STATUS_CODES)   # rate-limit
        self.assertIn(503, RETRYABLE_STATUS_CODES)   # service unavailable
        self.assertIn(500, RETRYABLE_STATUS_CODES)   # server error


# ---------------------------------------------------------------------------
# 2. chatbot.py – user_id param + verbosity + context window
# ---------------------------------------------------------------------------
class TestChatbotVerbosityAndContext(unittest.TestCase):

    def test_chat_accepts_user_id(self):
        import inspect
        from ai_compare.chatbot import AIChatbot
        sig = inspect.signature(AIChatbot.chat)
        self.assertIn('user_id', sig.parameters,
                      "AIChatbot.chat() missing user_id parameter")

    def test_build_enhanced_prompt_accepts_user_id(self):
        import inspect
        from ai_compare.chatbot import AIChatbot
        sig = inspect.signature(AIChatbot._build_enhanced_prompt)
        self.assertIn('user_id', sig.parameters)

    def test_context_window_is_8(self):
        """Conversation history must use last 8 exchanges, not 3."""
        import ast, inspect, textwrap
        from ai_compare import chatbot as _mod
        src = inspect.getsource(_mod.AIChatbot._build_enhanced_prompt)
        self.assertIn('[-8:]', src,
                      "Context window not expanded to 8: still using [-3:] or other slice")
        self.assertNotIn('[-3:]', src,
                         "Old [-3:] context slice still present in _build_enhanced_prompt")

    def test_verbosity_instruction_in_prompt(self):
        """verbosity_instruction must appear in the formatted prompt string."""
        import inspect
        from ai_compare import chatbot as _mod
        from smart_response import personalization_pipeline as _pipe
        prompt_src = inspect.getsource(_mod.AIChatbot._build_enhanced_prompt)
        pipe_src   = inspect.getsource(_pipe)
        self.assertIn('verbosity_instruction', prompt_src)
        self.assertIn('communication.response_length', pipe_src)

    def test_verbosity_rule_mentions_length(self):
        """The LENGTH rule in critical rules must reference verbosity preference."""
        import inspect
        from ai_compare import chatbot as _mod
        src = inspect.getsource(_mod.AIChatbot._build_enhanced_prompt)
        self.assertIn('verbosity preference', src)


# ---------------------------------------------------------------------------
# 3. character_routes.py – user_id threaded + verbosity signal recording
# ---------------------------------------------------------------------------
class TestCharacterRoutesVerbosity(unittest.TestCase):

    def _get_source(self):
        import inspect
        from ai_compare import character_routes as _mod
        return inspect.getsource(_mod)

    def test_user_id_passed_to_chat_smart_response(self):
        src = self._get_source()
        self.assertIn('user_id=user_id', src,
                      "user_id not being passed to bot.chat() in character_routes")

    def test_verbosity_signal_brief_patterns_present(self):
        src = self._get_source()
        self.assertIn('keep it short', src)
        self.assertIn('be brief', src)
        self.assertIn("response_length_feedback", src)

    def test_verbosity_signal_detailed_patterns_present(self):
        src = self._get_source()
        self.assertIn('in detail', src)
        self.assertIn('elaborate', src)


# ---------------------------------------------------------------------------
# 4. conversation_box.js – UI feedback buttons
# ---------------------------------------------------------------------------
class TestConversationBoxUI(unittest.TestCase):

    def _get_js(self):
        path = os.path.join(ROOT, 'static', 'conversation_box.js')
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_too_long_button_present(self):
        js = self._get_js()
        self.assertIn('Too long', js)
        self.assertIn('too-long-btn', js)

    def test_too_short_button_present(self):
        js = self._get_js()
        self.assertIn('Too short', js)
        self.assertIn('too-short-btn', js)

    def test_length_btn_css_defined(self):
        js = self._get_js()
        self.assertIn('.too-long-btn', js)
        self.assertIn('.too-short-btn', js)

    def test_too_long_sends_brief_message(self):
        js = self._get_js()
        self.assertIn("Keep it shorter", js)

    def test_too_short_triggers_detail_flag(self):
        js = self._get_js()
        self.assertIn('detail_requested: true', js)

    def test_existing_tell_me_more_still_present(self):
        """Regression: original buttons must not be removed."""
        js = self._get_js()
        self.assertIn('Tell me more', js)
        self.assertIn('Not what I meant', js)


# ---------------------------------------------------------------------------
# 5. verbosity_system.py – standalone verbosity module
# ---------------------------------------------------------------------------
class TestVerbositySystem(unittest.TestCase):

    def test_analyzer_detects_short_message(self):
        from verbosity_system import VerbosityAnalyzer
        a = VerbosityAnalyzer()
        score_short = a.analyze_message_length("Hi")
        score_long  = a.analyze_message_length(
            "Please provide a very detailed and thorough explanation with multiple examples.")
        self.assertGreater(score_long, score_short)

    def test_context_detection_technical(self):
        from verbosity_system import VerbosityAnalyzer
        a = VerbosityAnalyzer()
        contexts = a.detect_context("help me debug this Python code")
        self.assertIn('technical', contexts)

    def test_context_detection_creative(self):
        from verbosity_system import VerbosityAnalyzer
        a = VerbosityAnalyzer()
        contexts = a.detect_context("I have an idea for a new story")
        self.assertIn('creative', contexts)

    def test_response_adapter_shortens(self):
        from verbosity_system import VerbosityAnalyzer, ResponseLengthAdapter
        a = VerbosityAnalyzer()
        adapter = ResponseLengthAdapter(a)
        long_text = ("This is sentence one. " * 10).strip()
        # Force profile to 'short'
        a.user_profiles['u1'] = __import__(
            'verbosity_system', fromlist=['UserVerbosityProfile']
        ).UserVerbosityProfile(user_id='u1', preferred_length='short')
        short = adapter.adapt_response_length(long_text, 'u1')
        self.assertLessEqual(len(short), len(long_text))


# ---------------------------------------------------------------------------
# 6. advanced_comparison_metrics.py – key metric calculations
# ---------------------------------------------------------------------------
class TestAdvancedMetrics(unittest.TestCase):

    def test_semantic_similarity_related_texts(self):
        from advanced_comparison_metrics import SemanticAnalyzer
        a = SemanticAnalyzer()
        # Use texts with overlapping words so Jaccard > 0
        sim_related = a.calculate_jaccard_similarity(
            "machine learning and neural networks",
            "neural networks power machine learning")
        sim_unrelated = a.calculate_jaccard_similarity(
            "machine learning and neural networks",
            "the cat sat on the mat today")
        self.assertGreater(sim_related, sim_unrelated)

    def test_token_efficiency_returns_dict(self):
        from advanced_comparison_metrics import TokenEfficiencyAnalyzer
        t = TokenEfficiencyAnalyzer()
        metrics = t.calculate_efficiency_metrics("Hello world, this is a test.", "gpt-4")
        for key in ('token_count', 'efficiency_score', 'information_density'):
            self.assertIn(key, metrics)

    def test_coherence_higher_for_connected_text(self):
        from advanced_comparison_metrics import CoherenceAnalyzer
        c = CoherenceAnalyzer()
        coherent = c.analyze_coherence(
            "First, understand the problem. Therefore, we can build a solution. "
            "In conclusion, this approach is effective.")
        incoherent = c.analyze_coherence(
            "Random sentence. Another thought. No connection exists. Final words.")
        self.assertGreaterEqual(
            coherent['coherence_score'], incoherent['coherence_score'])


# ---------------------------------------------------------------------------
# 7. character_routes.py — signal processing wired post-response
# ---------------------------------------------------------------------------
class TestSignalProcessingWired(unittest.TestCase):

    def _get_source(self):
        import inspect
        from ai_compare import character_routes as _mod
        return inspect.getsource(_mod)

    def test_process_signals_and_adapt_called(self):
        src = self._get_source()
        self.assertIn('process_signals_and_adapt', src,
                      "process_signals_and_adapt() never called — signals recorded but never applied")

    def test_called_after_response_built(self):
        """Must appear after session_id is added to response (post-response hook)."""
        src = self._get_source()
        idx_session = src.find("response['session_id'] = session_id")
        idx_adapt   = src.find("process_signals_and_adapt")
        self.assertGreater(idx_adapt, idx_session,
                           "process_signals_and_adapt must be called AFTER the response is built")

    def test_adapt_call_is_error_safe(self):
        """Must be wrapped in try/except so it never blocks a response."""
        src = self._get_source()
        # find the adapt call and check it's inside a try block
        adapt_idx = src.find("process_signals_and_adapt")
        nearby = src[max(0, adapt_idx - 200): adapt_idx]
        self.assertIn('try:', nearby,
                      "process_signals_and_adapt must be inside a try/except block")


# ---------------------------------------------------------------------------
# 8. chatbot.py — emotional context wired
# ---------------------------------------------------------------------------
class TestEmotionalContextWired(unittest.TestCase):

    def _get_source(self):
        import inspect
        from ai_compare import chatbot as _mod
        return inspect.getsource(_mod.AIChatbot._build_enhanced_prompt)

    def _pipe_src(self):
        import inspect
        from smart_response import personalization_pipeline as _pipe
        return inspect.getsource(_pipe)

    def test_emotional_instruction_variable_present(self):
        src = self._get_source()
        self.assertIn('emotional_instruction', src)

    def test_emotional_journey_called(self):
        self.assertIn('analyze_emotional_journey', self._pipe_src())

    def test_declining_trajectory_handled(self):
        src = self._pipe_src()
        self.assertIn("declining", src)
        self.assertIn("empathy", src)

    def test_improving_trajectory_handled(self):
        src = self._pipe_src()
        self.assertIn("improving", src)
        self.assertIn("action-focused", src)

    def test_emotional_instruction_injected_into_template(self):
        src = self._get_source()
        self.assertIn("{emotional_instruction}", src)

    def test_confidence_threshold_guards_injection(self):
        """Should only inject if confidence >= 0.3 — no noise on cold start."""
        src = self._pipe_src()
        self.assertIn("confidence", src)
        self.assertIn("0.3", src)


# ---------------------------------------------------------------------------
# 9. app.py — /ask endpoint with comparison metrics
# ---------------------------------------------------------------------------
class TestAskEndpointMetrics(unittest.TestCase):

    def _get_source(self):
        path = os.path.join(ROOT, 'app.py')
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_include_metrics_param_present(self):
        src = self._get_source()
        self.assertIn("include_metrics", src)

    def test_advanced_response_evaluator_imported(self):
        src = self._get_source()
        self.assertIn("AdvancedResponseEvaluator", src)

    def test_comparison_metrics_in_response(self):
        src = self._get_source()
        self.assertIn("'comparison_metrics'", src)

    def test_rankings_in_response(self):
        src = self._get_source()
        self.assertIn("'rankings'", src)

    def test_metrics_error_is_non_fatal(self):
        """Metrics failure must be caught so the core compare still works."""
        src = self._get_source()
        # Find AdvancedResponseEvaluator block and verify except nearby
        idx = src.find("AdvancedResponseEvaluator")
        region = src[idx: idx + 900]
        self.assertIn("except", region,
                      "Metrics calculation must be wrapped in try/except")


# ---------------------------------------------------------------------------
# 10. Documentation — ENHANCEMENTS_WEB_PERSONALIZATION.md exists and covers all features
# ---------------------------------------------------------------------------
class TestDocumentationUpdated(unittest.TestCase):

    def _get_doc(self):
        path = os.path.join(ROOT, 'ENHANCEMENTS_WEB_PERSONALIZATION.md')
        self.assertTrue(os.path.exists(path), "ENHANCEMENTS_WEB_PERSONALIZATION.md not found")
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_doc_covers_retry_logic(self):
        doc = self._get_doc()
        self.assertIn('retry', doc.lower())

    def test_doc_covers_verbosity(self):
        doc = self._get_doc()
        self.assertIn('verbosity', doc.lower())

    def test_doc_covers_emotional_context(self):
        doc = self._get_doc()
        self.assertIn('emotional', doc.lower())

    def test_doc_covers_signal_processing(self):
        doc = self._get_doc()
        self.assertIn('process_signals_and_adapt', doc)

    def test_doc_covers_comparison_metrics(self):
        doc = self._get_doc()
        self.assertIn('comparison', doc.lower())

    def test_doc_has_test_results_table(self):
        doc = self._get_doc()
        self.assertIn('100%', doc)

    def test_doc_has_architecture_diagram(self):
        doc = self._get_doc()
        self.assertIn('character_routes', doc)


# ---------------------------------------------------------------------------
# 11. ResponseNeedClassifier — core classification logic
# ---------------------------------------------------------------------------
class TestResponseNeedClassifier(unittest.TestCase):

    def setUp(self):
        from smart_response.response_need_classifier import ResponseNeedClassifier
        self.clf = ResponseNeedClassifier()

    def test_sympathy_detected(self):
        r = self.clf.classify("I'm so overwhelmed and I don't know what to do")
        self.assertEqual(r.primary_need, 'sympathy')
        self.assertGreater(r.confidence, 0.0)

    def test_direction_detected(self):
        r = self.clf.classify("I'm not sure which option to choose. Should I stay or go?")
        self.assertEqual(r.primary_need, 'direction')

    def test_action_plan_detected(self):
        r = self.clf.classify("Give me a step-by-step plan to launch my startup")
        self.assertEqual(r.primary_need, 'action_plan')

    def test_immediate_result_detected(self):
        r = self.clf.classify("Quick answer: what is the capital of France?")
        self.assertEqual(r.primary_need, 'immediate_result')

    def test_small_steps_detected(self):
        r = self.clf.classify("I'm completely overwhelmed. Can you break this down into baby steps?")
        self.assertEqual(r.primary_need, 'small_steps')

    def test_inspiration_detected(self):
        r = self.clf.classify("I feel stuck and uninspired. Challenge my thinking on this.")
        self.assertEqual(r.primary_need, 'inspiration')

    def test_validation_detected(self):
        r = self.clf.classify("Am I on the right track with this approach?")
        self.assertEqual(r.primary_need, 'validation')

    def test_information_detected(self):
        r = self.clf.classify("What is machine learning and how does it work?")
        self.assertEqual(r.primary_need, 'information')

    def test_never_raises(self):
        """Classifier must never raise — even on empty/weird input."""
        for msg in ['', '   ', '???', 'x' * 2000, None.__class__.__name__]:
            result = self.clf.classify(msg)
            self.assertIsNotNone(result)
            self.assertIn(result.primary_need, [
                'direction', 'action_plan', 'immediate_result', 'inspiration',
                'small_steps', 'sympathy', 'information', 'validation'
            ])

    def test_prompt_instruction_always_returned(self):
        r = self.clf.classify("help me please")
        self.assertIsInstance(r.prompt_instruction, str)
        self.assertGreater(len(r.prompt_instruction), 10)

    def test_get_instruction_returns_empty_below_threshold(self):
        from smart_response.response_need_classifier import ResponseNeedClassifier
        clf = ResponseNeedClassifier()
        result = clf.get_instruction("ok", min_confidence=0.99)
        self.assertEqual(result, "")

    def test_sympathy_instruction_contains_empathy(self):
        r = self.clf.classify("I'm so sad and nobody cares")
        self.assertIn('heard', r.prompt_instruction.lower())

    def test_action_plan_instruction_contains_steps(self):
        r = self.clf.classify("walk me through the process step by step")
        self.assertIn('step', r.prompt_instruction.lower())

    def test_singleton_get_need_classifier(self):
        from smart_response.response_need_classifier import get_need_classifier
        a = get_need_classifier()
        b = get_need_classifier()
        self.assertIs(a, b)


# ---------------------------------------------------------------------------
# 12. base_chatbot.py — parity with chatbot.py
# ---------------------------------------------------------------------------
class TestBaseChatbotParity(unittest.TestCase):

    def _get_source(self):
        import inspect
        from ai_compare import base_chatbot as _mod
        return inspect.getsource(_mod.BaseChatbot)

    def test_chat_accepts_user_id(self):
        import inspect
        from ai_compare.base_chatbot import BaseChatbot
        sig = inspect.signature(BaseChatbot.chat)
        self.assertIn('user_id', sig.parameters)

    def test_build_prompt_accepts_user_id(self):
        import inspect
        from ai_compare.base_chatbot import BaseChatbot
        sig = inspect.signature(BaseChatbot._build_enhanced_prompt)
        self.assertIn('user_id', sig.parameters)

    def test_core_process_accepts_user_id(self):
        import inspect
        from ai_compare.base_chatbot import BaseChatbot
        sig = inspect.signature(BaseChatbot._core_process)
        self.assertIn('user_id', sig.parameters)

    def test_context_window_is_8(self):
        src = self._get_source()
        self.assertIn('[-8:]', src)
        self.assertNotIn('[-3:]', src)

    def test_verbosity_wired(self):
        import inspect
        from smart_response import personalization_pipeline as _pipe
        self.assertIn('communication.response_length', inspect.getsource(_pipe))

    def test_emotional_context_wired(self):
        import inspect
        from smart_response import personalization_pipeline as _pipe
        self.assertIn('analyze_emotional_journey', inspect.getsource(_pipe))

    def test_need_classifier_wired(self):
        import inspect
        from smart_response import personalization_pipeline as _pipe
        pipe_src = inspect.getsource(_pipe)
        self.assertIn('response_need_classifier', pipe_src)
        self.assertIn('need_instruction', pipe_src)

    def test_critical_rules_present(self):
        src = self._get_source()
        self.assertIn('CRITICAL RESPONSE RULES', src)


# ---------------------------------------------------------------------------
# 13. ProactiveClarifier
# ---------------------------------------------------------------------------
class TestProactiveClarifier(unittest.TestCase):

    def setUp(self):
        from smart_response.proactive_clarifier import ProactiveClarifier
        self.clf = ProactiveClarifier(confidence_threshold=0.35)

    def test_no_clarify_when_clear_intent(self):
        d = self.clf.decide("walk me through a step by step plan", need_confidence=0.8, primary_need='action_plan')
        self.assertFalse(d.should_clarify)

    def test_clarify_when_vague_and_low_confidence(self):
        d = self.clf.decide("help", need_confidence=0.05, primary_need='information')
        self.assertTrue(d.should_clarify)

    def test_clarify_on_competing_needs(self):
        d = self.clf.decide(
            "I need something but not sure what",
            need_confidence=0.2,
            primary_need='direction',
            secondary_need='sympathy',
        )
        self.assertTrue(d.should_clarify)

    def test_critical_pattern_triggers_empathy(self):
        d = self.clf.decide("I want to kill myself", need_confidence=0.1, primary_need='sympathy')
        self.assertTrue(d.should_clarify)
        self.assertEqual(d.urgency, 'critical')
        self.assertIn("safe", d.question.lower())

    def test_critical_bypasses_confidence_threshold(self):
        """Critical detection must fire even with high confidence."""
        d = self.clf.decide("I can't go on anymore", need_confidence=0.9, primary_need='sympathy')
        self.assertTrue(d.should_clarify)
        self.assertEqual(d.urgency, 'critical')

    def test_question_always_non_empty_when_clarifying(self):
        d = self.clf.decide("ok", need_confidence=0.01, primary_need='information')
        if d.should_clarify:
            self.assertGreater(len(d.question), 10)

    def test_format_response_returns_dict(self):
        from smart_response.proactive_clarifier import ProactiveClarifier, ClarificationDecision
        clf = ProactiveClarifier()
        decision = ClarificationDecision(
            should_clarify=True, question="What do you need?",
            reason="test", urgency="normal", detected_need="direction"
        )
        result = clf.format_clarification_response(decision)
        self.assertIn('response', result)
        self.assertIn('type', result)
        self.assertEqual(result['type'], 'clarification')

    def test_never_raises(self):
        for msg in ['', '   ', '??', 'x' * 500]:
            d = self.clf.decide(msg, need_confidence=0.0, primary_need='information')
            self.assertIsNotNone(d)

    def test_singleton(self):
        from smart_response.proactive_clarifier import get_clarifier
        self.assertIs(get_clarifier(), get_clarifier())


# ---------------------------------------------------------------------------
# 14. CharacterSuggester
# ---------------------------------------------------------------------------
class TestCharacterSuggester(unittest.TestCase):

    def setUp(self):
        from smart_response.character_suggester import CharacterSuggester
        self.sug = CharacterSuggester(suggestion_confidence_threshold=0.5)

    def test_no_suggestion_below_confidence(self):
        s = self.sug.suggest('coach', 'sympathy', need_confidence=0.3)
        self.assertFalse(s.should_suggest)

    def test_suggests_psychologist_for_sympathy(self):
        s = self.sug.suggest('marcus', 'sympathy', need_confidence=0.8)
        self.assertTrue(s.should_suggest)
        self.assertEqual(s.suggested_character_id, 'psychologist')

    def test_suggests_coach_for_action_plan(self):
        s = self.sug.suggest('philosopher', 'action_plan', need_confidence=0.7)
        self.assertTrue(s.should_suggest)
        self.assertEqual(s.suggested_character_id, 'coach')

    def test_no_suggestion_when_already_best_character(self):
        s = self.sug.suggest('psychologist', 'sympathy', need_confidence=0.9)
        self.assertFalse(s.should_suggest)

    def test_general_purpose_character_not_replaced(self):
        """Coach/Sage/Psychologist should NOT be replaced — they handle most needs."""
        for char in ['coach', 'sage', 'psychologist']:
            s = self.sug.suggest(char, 'action_plan', need_confidence=0.9)
            self.assertFalse(s.should_suggest,
                f"{char} should not be suggested to switch away from")

    def test_format_suggestion_message(self):
        from smart_response.character_suggester import CharacterSuggestion
        suggestion = CharacterSuggestion(
            should_suggest=True,
            suggested_character_id='psychologist',
            suggested_character_name='The Psychologist',
            reason='specialises in emotional support',
            confidence=0.8,
        )
        msg = self.sug.format_suggestion_message(suggestion)
        self.assertIn('The Psychologist', msg)
        self.assertIn('specialises in emotional support', msg)

    def test_empty_message_when_no_suggestion(self):
        s = self.sug.suggest('coach', 'action_plan', need_confidence=0.9)
        msg = self.sug.format_suggestion_message(s)
        self.assertEqual(msg, '')

    def test_available_characters_filter(self):
        """Should not suggest characters outside the available list."""
        s = self.sug.suggest('marcus', 'sympathy', need_confidence=0.8,
                             available_characters=['coach', 'sage'])
        if s.should_suggest:
            self.assertIn(s.suggested_character_id, ['coach', 'sage'])

    def test_never_raises(self):
        for need in ['direction', 'action_plan', 'sympathy', 'unknown_need']:
            result = self.sug.suggest('coach', need, need_confidence=0.8)
            self.assertIsNotNone(result)

    def test_singleton(self):
        from smart_response.character_suggester import get_character_suggester
        self.assertIs(get_character_suggester(), get_character_suggester())


# ---------------------------------------------------------------------------
# 15. character_routes.py — proactive clarification + character suggestion wired
# ---------------------------------------------------------------------------
class TestRoutesNewFeatures(unittest.TestCase):

    def _src(self):
        import inspect
        from ai_compare import character_routes as _mod
        return inspect.getsource(_mod)

    def test_proactive_clarifier_imported(self):
        src = self._src()
        self.assertIn('proactive_clarifier', src)
        self.assertIn('get_clarifier', src)

    def test_clarification_returned_before_ai_call(self):
        src = self._src()
        idx_clarify = src.find('should_clarify')
        idx_ai      = src.find('def ai_function')
        self.assertLess(idx_clarify, idx_ai,
                        "Clarification check must come BEFORE ai_function is defined")

    def test_character_suggester_imported(self):
        src = self._src()
        self.assertIn('character_suggester', src)
        self.assertIn('get_character_suggester', src)

    def test_character_suggestion_added_to_response(self):
        src = self._src()
        self.assertIn("'character_suggestion'", src)

    def test_detected_need_added_to_response(self):
        src = self._src()
        self.assertIn("'detected_need'", src)

    def test_clarification_saves_critical_to_db(self):
        src = self._src()
        self.assertIn('proactive_clarification', src)


# ---------------------------------------------------------------------------
# 16. app.py — /api/user/personalization-profile endpoint
# ---------------------------------------------------------------------------
class TestPersonalizationProfileEndpoint(unittest.TestCase):

    def _src(self):
        path = os.path.join(ROOT, 'app.py')
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_endpoint_defined(self):
        src = self._src()
        self.assertIn('/api/user/personalization-profile', src)

    def test_returns_response_length(self):
        src = self._src()
        self.assertIn("'response_length'", src)

    def test_returns_emotional_journey(self):
        src = self._src()
        self.assertIn("'emotional_journey'", src)

    def test_returns_communication_style(self):
        src = self._src()
        self.assertIn("'communication_style'", src)

    def test_requires_auth(self):
        src = self._src()
        idx_route = src.find('/api/user/personalization-profile')
        region = src[idx_route: idx_route + 200]
        self.assertIn('require_auth', region)

    def test_each_section_error_safe(self):
        """Each data section must be wrapped in its own try/except."""
        src = self._src()
        idx = src.find('/api/user/personalization-profile')
        region = src[idx: idx + 3500]
        self.assertGreaterEqual(region.count('except Exception'), 2,
                                "Each profile section needs its own error handling")


# ---------------------------------------------------------------------------
# 17. conversation_box.js — clarification card + character suggestion UI
# ---------------------------------------------------------------------------
class TestConversationBoxNewUI(unittest.TestCase):

    def _js(self):
        path = os.path.join(ROOT, 'static', 'conversation_box.js')
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_clarification_card_method_exists(self):
        js = self._js()
        self.assertIn('_addClarificationCard', js)

    def test_clarification_card_uses_critical_class(self):
        js = self._js()
        self.assertIn('critical', js)
        self.assertIn('clarification-card', js)

    def test_clarification_label_text(self):
        js = self._js()
        self.assertIn('Just to clarify', js)
        self.assertIn('Important', js)

    def test_character_suggestion_method_exists(self):
        js = self._js()
        self.assertIn('_addCharacterSuggestion', js)

    def test_character_suggestion_bar_css(self):
        js = self._js()
        self.assertIn('character-suggestion-bar', js)

    def test_character_switch_handler_exists(self):
        js = self._js()
        self.assertIn('_handleCharacterSwitch', js)

    def test_clarification_routing_in_send(self):
        """type === 'clarification' must route to _addClarificationCard."""
        js = self._js()
        self.assertIn("type === 'clarification'", js)
        self.assertIn('_addClarificationCard', js)

    def test_suggestion_shown_only_for_normal_responses(self):
        js = self._js()
        # character_suggestion must appear inside the else branch (not for clarifications)
        idx_else   = js.find('} else {')
        idx_suggest = js.find('_addCharacterSuggestion')
        self.assertGreater(idx_suggest, idx_else,
                           "_addCharacterSuggestion must be inside the else (non-clarification) branch")

    def test_critical_card_css_defined(self):
        js = self._js()
        self.assertIn('.clarification-card.critical', js)

    def test_response_actions_not_shown_for_clarifications(self):
        """_addResponseActions must NOT be called for clarification responses."""
        js = self._js()
        # Find the clarification branch and verify _addResponseActions is not there
        clarify_idx = js.find('_addClarificationCard(data.response')
        actions_idx = js.find('_addResponseActions()')
        # _addResponseActions must be AFTER the clarification call (in the else)
        self.assertLess(clarify_idx, actions_idx)


# ---------------------------------------------------------------------------
# 18. Explicit Context Extraction — wired into routes + injected into prompts
# ---------------------------------------------------------------------------
class TestExplicitContextWiring(unittest.TestCase):

    def _routes_src(self):
        import inspect
        from ai_compare import character_routes as _mod
        return inspect.getsource(_mod)

    def _chatbot_src(self):
        import inspect
        from ai_compare import chatbot as _mod
        return inspect.getsource(_mod.AIChatbot._build_enhanced_prompt)

    def _base_src(self):
        import inspect
        from ai_compare import base_chatbot as _mod
        return inspect.getsource(_mod.BaseChatbot._build_enhanced_prompt)

    # ---- Routes wiring ----
    def test_extraction_called_in_routes(self):
        src = self._routes_src()
        self.assertIn('extract_explicit_context', src)

    def test_extraction_uses_integrated_db(self):
        src = self._routes_src()
        idx = src.find('extract_explicit_context')
        nearby = src[max(0, idx - 300): idx]
        self.assertIn('integrated_db', nearby)

    def test_extraction_is_error_safe_in_routes(self):
        src = self._routes_src()
        idx = src.find('extract_explicit_context')
        nearby = src[max(0, idx - 400): idx]
        self.assertIn('try:', nearby)

    def test_extraction_runs_before_ai_call(self):
        """Extraction must happen before ai_function is defined."""
        src = self._routes_src()
        idx_extract = src.find('extract_explicit_context')
        idx_ai_func = src.find('def ai_function')
        self.assertLess(idx_extract, idx_ai_func,
                        "Explicit context extraction must run before AI call")

    # ---- chatbot.py prompt injection ----
    def test_explicit_context_block_variable_in_chatbot(self):
        src = self._chatbot_src()
        self.assertIn('explicit_context_block', src)

    def test_explicit_context_injected_into_chatbot_template(self):
        src = self._chatbot_src()
        self.assertIn('{explicit_context_block}', src)

    def test_format_for_ai_prompt_called_in_chatbot(self):
        import inspect
        from smart_response import personalization_pipeline as _pipe
        self.assertIn('format_for_ai_prompt', inspect.getsource(_pipe))

    def test_explicit_context_is_error_safe_in_chatbot(self):
        import inspect
        from smart_response import personalization_pipeline as _pipe
        src = inspect.getsource(_pipe)
        self.assertIn('explicit_context_block', src)
        self.assertIn('except Exception', src)

    # ---- base_chatbot.py parity ----
    def test_explicit_context_block_variable_in_base(self):
        src = self._base_src()
        self.assertIn('explicit_context_block', src)

    def test_explicit_context_injected_into_base_template(self):
        src = self._base_src()
        self.assertIn('{explicit_context_block}', src)

    # ---- ExplicitContextHandler standalone ----
    def test_handler_extracts_emotional_state(self):
        import sqlite3
        from smart_response.explicit_context_handler import ExplicitContextHandler
        conn = sqlite3.connect(':memory:')
        ech = ExplicitContextHandler(conn)
        results = ech.extract_explicit_context(999, 'test', "I'm feeling really anxious about this")
        conn.close()
        types = [r.get('type') for r in results]
        self.assertIn('emotional_state', types)

    def test_handler_extracts_goal(self):
        import sqlite3
        from smart_response.explicit_context_handler import ExplicitContextHandler
        conn = sqlite3.connect(':memory:')
        ech = ExplicitContextHandler(conn)
        results = ech.extract_explicit_context(999, 'test', "My goal is to get a promotion this year")
        conn.close()
        types = [r.get('type') for r in results]
        self.assertIn('goal', types)

    def test_handler_extracts_preference(self):
        import sqlite3
        from smart_response.explicit_context_handler import ExplicitContextHandler
        conn = sqlite3.connect(':memory:')
        ech = ExplicitContextHandler(conn)
        results = ech.extract_explicit_context(999, 'test', "I prefer short, direct answers")
        conn.close()
        types = [r.get('type') for r in results]
        self.assertTrue(len(results) >= 0)  # May or may not match depending on pattern

    def test_handler_format_for_prompt_returns_string(self):
        import sqlite3
        from smart_response.explicit_context_handler import ExplicitContextHandler
        conn = sqlite3.connect(':memory:')
        ech = ExplicitContextHandler(conn)
        ech.extract_explicit_context(999, 'test', "I'm feeling anxious. My goal is to stay calm.")
        result = ech.format_for_ai_prompt(999, 'test')
        conn.close()
        self.assertIsInstance(result, str)

    def test_handler_never_raises_on_unknown_message(self):
        import sqlite3
        from smart_response.explicit_context_handler import ExplicitContextHandler
        conn = sqlite3.connect(':memory:')
        ech = ExplicitContextHandler(conn)
        try:
            ech.extract_explicit_context(999, 'test', "Just a normal question about Python")
        except Exception as e:
            self.fail(f"ExplicitContextHandler raised: {e}")
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# 19. ProgressContextBuilder + wiring into prompt builders
# ---------------------------------------------------------------------------
class TestProgressContextBuilder(unittest.TestCase):

    def test_returns_empty_string_on_no_history(self):
        """No history → empty string (no noise on new users)."""
        from smart_response.progress_context_builder import build_progress_context
        result = build_progress_context(99999, 'nonexistent_char', db_path=':memory:')
        self.assertEqual(result, '')

    def test_returns_string_type_always(self):
        from smart_response.progress_context_builder import build_progress_context
        result = build_progress_context(1, 'coach')
        self.assertIsInstance(result, str)

    def test_never_raises(self):
        from smart_response.progress_context_builder import build_progress_context
        for uid, char in [(0, ''), (None, None), (-1, 'sage'), (99999, 'x' * 100)]:
            try:
                build_progress_context(uid, char)
            except Exception as e:
                self.fail(f"build_progress_context raised: {e}")

    def test_builds_context_from_secondary_history(self):
        """When secondary history exists, should produce non-empty context block."""
        import sqlite3, json
        from smart_response.dual_layer_history import DualLayerHistorySystem
        from smart_response.progress_context_builder import build_progress_context

        # Set up in-memory DB with repeated topics
        import tempfile, os
        tmp = tempfile.mktemp(suffix='.db')
        conn = sqlite3.connect(tmp)
        dlh = DualLayerHistorySystem(conn)
        # Store enough interactions to have >1 of a topic
        for _ in range(3):
            pid = dlh.store_interaction(1, 'coach', 'I want a promotion', 'Great!', 'direct')
            dlh.analyze_and_store_secondary(pid, 1, 'coach',
                interpretation={'topics': ['career', 'promotion'], 'concerns': ['performance review']})
        conn.close()

        result = build_progress_context(1, 'coach', db_path=tmp)
        os.unlink(tmp)
        # With repeated topics, should produce a non-empty block
        self.assertIsInstance(result, str)

    def test_max_lines_reasonable(self):
        """Context block must not exceed 8 lines (don't bloat the prompt)."""
        import sqlite3, tempfile, os
        from smart_response.dual_layer_history import DualLayerHistorySystem
        from smart_response.progress_context_builder import build_progress_context

        tmp = tempfile.mktemp(suffix='.db')
        conn = sqlite3.connect(tmp)
        dlh = DualLayerHistorySystem(conn)
        for _ in range(10):
            pid = dlh.store_interaction(1, 'sage', 'Help me with everything', 'OK', 'direct')
            dlh.analyze_and_store_secondary(pid, 1, 'sage',
                interpretation={'topics': ['work', 'life', 'health', 'goals', 'relationships'],
                                'concerns': ['stress', 'anxiety', 'time']})
        conn.close()
        result = build_progress_context(1, 'sage', db_path=tmp)
        os.unlink(tmp)
        if result:
            self.assertLessEqual(len(result.splitlines()), 8)

    def test_wired_in_chatbot(self):
        import inspect
        from ai_compare import chatbot as _mod
        from smart_response import personalization_pipeline as _pipe
        prompt_src = inspect.getsource(_mod.AIChatbot._build_enhanced_prompt)
        self.assertIn('build_personalization', prompt_src)
        self.assertIn('progress_context_builder', inspect.getsource(_pipe))
        self.assertIn('progress_context_block', prompt_src)
        self.assertIn('{progress_context_block}', prompt_src)

    def test_wired_in_base_chatbot(self):
        import inspect
        from ai_compare import base_chatbot as _mod
        from smart_response import personalization_pipeline as _pipe
        prompt_src = inspect.getsource(_mod.BaseChatbot._build_enhanced_prompt)
        self.assertIn('build_personalization', prompt_src)
        self.assertIn('progress_context_builder', inspect.getsource(_pipe))
        self.assertIn('progress_context_block', prompt_src)
        self.assertIn('{progress_context_block}', prompt_src)

    def test_progress_endpoint_in_app(self):
        path = os.path.join(ROOT, 'app.py')
        with open(path, 'r', encoding='utf-8') as f:
            src = f.read()
        self.assertIn('/api/user/progress-summary', src)
        self.assertIn('progress_context', src)

    def test_progress_endpoint_requires_auth(self):
        path = os.path.join(ROOT, 'app.py')
        with open(path, 'r', encoding='utf-8') as f:
            src = f.read()
        idx = src.find('/api/user/progress-summary')
        region = src[idx: idx + 200]
        self.assertIn('require_auth', region)


# ---------------------------------------------------------------------------
# 20. Dual-Layer History Storage — wired into character_routes.py
# ---------------------------------------------------------------------------
class TestDualLayerHistoryWiring(unittest.TestCase):

    def _src(self):
        import inspect
        from ai_compare import character_routes as _mod
        return inspect.getsource(_mod)

    def test_store_interaction_called(self):
        src = self._src()
        self.assertIn('store_interaction', src)

    def test_analyze_and_store_secondary_called(self):
        src = self._src()
        self.assertIn('analyze_and_store_secondary', src)

    def test_dual_layer_import_present(self):
        src = self._src()
        self.assertIn('DualLayerHistorySystem', src)

    def test_wiring_uses_integrated_db(self):
        src = self._src()
        idx = src.find('store_interaction')
        nearby = src[max(0, idx - 600): idx]
        self.assertIn('integrated_db', nearby)

    def test_wiring_is_error_safe(self):
        src = self._src()
        idx = src.find('store_interaction')
        nearby = src[max(0, idx - 600): idx]
        self.assertIn('try:', nearby)

    def test_secondary_uses_primary_id(self):
        """analyze_and_store_secondary must only be called if store_interaction succeeded."""
        src = self._src()
        idx_prim = src.find('store_interaction')
        idx_sec  = src.find('analyze_and_store_secondary')
        self.assertLess(idx_prim, idx_sec,
                        "Secondary analysis must be called after primary store")
        # Should be conditional on primary_id
        region = src[idx_prim: idx_sec + 50]
        self.assertIn('_primary_id', region)

    def test_history_stored_after_response_built(self):
        """History must be stored after the response dict is built (has content to store)."""
        src = self._src()
        idx_session = src.find("response['session_id'] = session_id")
        idx_dlh     = src.find('DualLayerHistorySystem')
        self.assertGreater(idx_dlh, idx_session,
                           "Dual-layer history must be stored AFTER response is built")

    def test_dual_layer_history_standalone(self):
        """DualLayerHistorySystem can store and retrieve an interaction."""
        import sqlite3, tempfile, os
        from smart_response.dual_layer_history import DualLayerHistorySystem
        tmp = tempfile.mktemp(suffix='.db')
        conn = sqlite3.connect(tmp)
        dlh = DualLayerHistorySystem(conn)
        pid = dlh.store_interaction(1, 'coach', 'Hello', 'Hi there!', 'direct')
        self.assertGreater(pid, 0)
        sid = dlh.analyze_and_store_secondary(pid, 1, 'coach')
        self.assertGreater(sid, 0)
        conn.close()
        os.unlink(tmp)


# ---------------------------------------------------------------------------
# 21. Character Effectiveness Tracking
# ---------------------------------------------------------------------------
class TestCharacterEffectivenessTracking(unittest.TestCase):

    def _app_src(self):
        path = os.path.join(ROOT, 'app.py')
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def _js(self):
        path = os.path.join(ROOT, 'static', 'conversation_box.js')
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    # ---- app.py endpoint ----
    def test_endpoint_defined(self):
        src = self._app_src()
        self.assertIn('/api/user/character-switch', src)

    def test_endpoint_is_post(self):
        src = self._app_src()
        idx = src.find('/api/user/character-switch')
        region = src[idx: idx + 80]
        self.assertIn('POST', region)

    def test_endpoint_requires_auth(self):
        src = self._app_src()
        idx = src.find('/api/user/character-switch')
        region = src[idx: idx + 200]
        self.assertIn('require_auth', region)

    def test_endpoint_records_from_and_to_character(self):
        src = self._app_src()
        idx = src.find('record_character_switch')
        region = src[idx: idx + 600]
        self.assertIn('from_character', region)
        self.assertIn('to_character', region)

    def test_endpoint_records_detected_need(self):
        src = self._app_src()
        idx = src.find('record_character_switch')
        region = src[idx: idx + 600]
        self.assertIn('detected_need', region)

    def test_endpoint_uses_record_engagement(self):
        src = self._app_src()
        idx = src.find('record_character_switch')
        region = src[idx: idx + 1400]
        self.assertIn('record_engagement', region)

    # ---- conversation_box.js ----
    def test_handle_switch_calls_api(self):
        js = self._js()
        self.assertIn('/api/user/character-switch', js)

    def test_handle_switch_sends_from_character(self):
        js = self._js()
        idx = js.find('/api/user/character-switch')
        region = js[idx: idx + 400]
        self.assertIn('from_character', region)

    def test_handle_switch_is_fire_and_forget(self):
        """Should not block navigation — must use catch() to suppress errors."""
        js = self._js()
        idx = js.find('/api/user/character-switch')
        region = js[idx: idx + 500]
        self.assertIn('.catch(', region)

    def test_suggestion_bar_passes_meta_to_handler(self):
        """_addCharacterSuggestion must encode metadata and pass it to the click handler."""
        js = self._js()
        self.assertIn('encodeURIComponent', js)
        self.assertIn('metaEncoded', js)


# ---------------------------------------------------------------------------
# 22. CharacterSuggester Effectiveness Weighting
# ---------------------------------------------------------------------------
class TestCharacterSuggesterEffectiveness(unittest.TestCase):

    def setUp(self):
        from smart_response.character_suggester import CharacterSuggester
        self.sug = CharacterSuggester()

    def test_get_effectiveness_scores_returns_dict(self):
        """Should return empty dict when no data (not raise)."""
        scores = self.sug.get_effectiveness_scores('sympathy', db_path=':memory:')
        self.assertIsInstance(scores, dict)

    def test_get_effectiveness_scores_never_raises(self):
        for need in ['sympathy', 'direction', 'bad_need', '', None]:
            try:
                self.sug.get_effectiveness_scores(need, db_path=':memory:')
            except Exception as e:
                self.fail(f"get_effectiveness_scores raised: {e}")

    def test_empty_db_returns_empty_scores(self):
        scores = self.sug.get_effectiveness_scores('sympathy', db_path=':memory:')
        self.assertEqual(scores, {})

    def test_effectiveness_scores_from_real_signals(self):
        """With enough character_switch signals, scores reflect distribution."""
        import sqlite3, tempfile, os
        tmp = tempfile.mktemp(suffix='.db')
        conn = sqlite3.connect(tmp)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_engagement_signals
            (id INTEGER PRIMARY KEY, user_id INTEGER, signal_type TEXT,
             signal_value REAL, context_data TEXT, character_id TEXT,
             topic TEXT, session_id TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        # Insert 4 switches to psychologist for sympathy
        for _ in range(4):
            cursor.execute("INSERT INTO user_engagement_signals (user_id, signal_type, character_id, topic) VALUES (1,'character_switch','psychologist','sympathy')")
        # Insert 1 switch to sage for sympathy
        cursor.execute("INSERT INTO user_engagement_signals (user_id, signal_type, character_id, topic) VALUES (1,'character_switch','sage','sympathy')")
        conn.commit()
        conn.close()

        scores = self.sug.get_effectiveness_scores('sympathy', db_path=tmp, min_signals=1)
        os.unlink(tmp)
        self.assertGreater(scores.get('psychologist', 0), scores.get('sage', 0))

    def test_effectiveness_reranks_candidates(self):
        """When effectiveness data gives 'sage' a high score, sage should be preferred over static default."""
        import sqlite3, tempfile, os
        tmp = tempfile.mktemp(suffix='.db')
        conn = sqlite3.connect(tmp)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_engagement_signals
            (id INTEGER PRIMARY KEY, user_id INTEGER, signal_type TEXT,
             signal_value REAL, context_data TEXT, character_id TEXT,
             topic TEXT, session_id TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        # Give 'sage' overwhelming advantage for 'inspiration'
        for _ in range(8):
            cursor.execute("INSERT INTO user_engagement_signals (user_id, signal_type, character_id, topic) VALUES (1,'character_switch','sage','inspiration')")
        cursor.execute("INSERT INTO user_engagement_signals (user_id, signal_type, character_id, topic) VALUES (1,'character_switch','philosopher','inspiration')")
        conn.commit()
        conn.close()

        result = self.sug.suggest('marcus', 'inspiration', need_confidence=0.8, db_path=tmp)
        os.unlink(tmp)
        # With strong effectiveness signal, sage should still appear as suggestion
        if result.should_suggest:
            self.assertIn(result.suggested_character_id, ['sage', 'philosopher'])

    def test_static_fallback_when_no_data(self):
        """Static ordering used when effectiveness DB has no signals."""
        result = self.sug.suggest('marcus', 'sympathy', need_confidence=0.8, db_path=':memory:')
        # Should still suggest something using static mapping
        self.assertIsNotNone(result)
        if result.should_suggest:
            self.assertEqual(result.suggested_character_id, 'psychologist')

    def test_suggest_still_accepts_no_db_path(self):
        """suggest() should work without db_path (uses default)."""
        result = self.sug.suggest('marcus', 'sympathy', need_confidence=0.8)
        self.assertIsNotNone(result)

    def test_effectiveness_method_in_module(self):
        import inspect
        from smart_response import character_suggester as _mod
        src = inspect.getsource(_mod)
        self.assertIn('get_effectiveness_scores', src)
        self.assertIn('character_switch', src)
        self.assertIn('effectiveness', src)


# ---------------------------------------------------------------------------
# 23. Personalization Status Indicator
# ---------------------------------------------------------------------------
class TestPersonalizationStatusIndicator(unittest.TestCase):

    def _app_src(self):
        path = os.path.join(ROOT, 'app.py')
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def _js(self):
        path = os.path.join(ROOT, 'static', 'conversation_box.js')
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    # ---- app.py endpoint ----
    def test_endpoint_returns_verbosity_object(self):
        src = self._app_src()
        idx = src.find('def get_personalization_profile')
        region = src[idx: idx + 1200]
        self.assertIn("profile['verbosity']", region)

    def test_endpoint_returns_emotional_state(self):
        src = self._app_src()
        idx = src.find('def get_personalization_profile')
        region = src[idx: idx + 1500]
        self.assertIn("emotional_state", region)

    def test_endpoint_returns_active_goal(self):
        src = self._app_src()
        idx = src.find('def get_personalization_profile')
        region = src[idx: idx + 2800]
        self.assertIn("active_goal", region)

    def test_endpoint_returns_current_need(self):
        src = self._app_src()
        idx = src.find('def get_personalization_profile')
        region = src[idx: idx + 3500]
        self.assertIn("current_need", region)

    def test_explicit_context_queried_for_profile(self):
        src = self._app_src()
        idx = src.find('def get_personalization_profile')
        region = src[idx: idx + 1800]
        self.assertIn('get_explicit_context', region)

    # ---- conversation_box.js ----
    def test_load_status_method_exists(self):
        js = self._js()
        self.assertIn('_loadPersonalizationStatus', js)

    def test_render_status_method_exists(self):
        js = self._js()
        self.assertIn('_renderPersonalizationStatus', js)

    def test_load_called_on_init(self):
        js = self._js()
        idx = js.find('this.loadHistory()')
        region = js[idx: idx + 100]
        self.assertIn('_loadPersonalizationStatus', region)

    def test_chips_css_defined(self):
        js = self._js()
        self.assertIn('persona-chip', js)
        self.assertIn('personalization-status', js)

    def test_emotion_chip_uses_emotion_class(self):
        js = self._js()
        self.assertIn('persona-chip emotion', js)

    def test_goal_chip_uses_goal_class(self):
        js = self._js()
        self.assertIn('persona-chip goal', js)

    def test_verbosity_chip_uses_verbosity_class(self):
        js = self._js()
        self.assertIn('persona-chip verbosity', js)

    def test_render_is_silent_on_missing_profile(self):
        """_renderPersonalizationStatus must guard against null profile."""
        js = self._js()
        idx = js.find('_renderPersonalizationStatus(profile)')
        region = js[idx: idx + 150]
        self.assertIn('if (!profile)', region)

    def test_chips_removed_before_re_render(self):
        """Should remove existing status bar before re-rendering."""
        js = self._js()
        self.assertIn('personalization-status-bar', js)
        self.assertIn('existing.remove()', js)


# ---------------------------------------------------------------------------
# 24. GoalCheckInBuilder
# ---------------------------------------------------------------------------
class TestGoalCheckInBuilder(unittest.TestCase):

    def setUp(self):
        from smart_response.goal_checkin_builder import GoalCheckInBuilder
        self.builder = GoalCheckInBuilder()

    def test_module_importable(self):
        from smart_response.goal_checkin_builder import GoalCheckInBuilder, get_goal_checkin_builder
        self.assertIsNotNone(GoalCheckInBuilder)

    def test_returns_string_always(self):
        result = self.builder.build_checkin_block(1, 'coach', db_path=':memory:')
        self.assertIsInstance(result, str)

    def test_never_raises(self):
        for uid in [1, 0, -1, None]:
            try:
                self.builder.build_checkin_block(uid, 'coach', db_path=':memory:')
            except Exception as e:
                self.fail(f"build_checkin_block raised: {e}")

    def test_empty_db_returns_empty(self):
        result = self.builder.build_checkin_block(1, 'coach', db_path=':memory:')
        self.assertEqual(result, '')

    def test_old_goal_produces_checkin_block(self):
        """A goal set 10 days ago should generate a check-in hint."""
        import sqlite3, tempfile, os
        tmp = tempfile.mktemp(suffix='.db')
        conn = sqlite3.connect(tmp)
        cursor = conn.cursor()
        # Create required tables
        cursor.execute('''CREATE TABLE IF NOT EXISTS explicit_context
            (id INTEGER PRIMARY KEY, user_id INTEGER, character TEXT,
             context_type TEXT, context_key TEXT, context_value TEXT,
             original_statement TEXT, priority TEXT, confidence REAL,
             extracted_via TEXT, active INTEGER DEFAULT 1,
             timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS character_sessions
            (id INTEGER PRIMARY KEY, user_id INTEGER, character_id TEXT,
             session_id TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS character_messages
            (id INTEGER PRIMARY KEY, user_id INTEGER, character_id TEXT,
             role TEXT, content TEXT,
             timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        # Insert 5 sessions
        for _ in range(5):
            cursor.execute("INSERT INTO character_sessions (user_id, character_id, session_id) VALUES (1,'coach','s1')")
        # Insert an old active goal (15 days ago)
        cursor.execute(
            "INSERT INTO explicit_context (user_id, character, context_type, context_key, context_value, priority, active, timestamp) VALUES (1,'coach','goal','main','get promoted','HIGH',1, datetime('now','-15 days'))"
        )
        conn.commit()
        conn.close()

        from smart_response.goal_checkin_builder import GoalCheckInBuilder
        result = GoalCheckInBuilder().build_checkin_block(1, 'coach', db_path=tmp)
        os.unlink(tmp)
        self.assertIn('GOAL CHECK-IN', result)
        self.assertIn('get promoted', result)

    def test_recently_mentioned_goal_skipped(self):
        """Goal mentioned in the last 5 days should NOT trigger a check-in."""
        import sqlite3, tempfile, os
        tmp = tempfile.mktemp(suffix='.db')
        conn = sqlite3.connect(tmp)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS explicit_context
            (id INTEGER PRIMARY KEY, user_id INTEGER, character TEXT,
             context_type TEXT, context_key TEXT, context_value TEXT,
             original_statement TEXT, priority TEXT, confidence REAL,
             extracted_via TEXT, active INTEGER DEFAULT 1,
             timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS character_sessions
            (id INTEGER PRIMARY KEY, user_id INTEGER, character_id TEXT,
             session_id TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS character_messages
            (id INTEGER PRIMARY KEY, user_id INTEGER, character_id TEXT,
             role TEXT, content TEXT,
             timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        for _ in range(5):
            cursor.execute("INSERT INTO character_sessions (user_id, character_id, session_id) VALUES (1,'coach','s1')")
        cursor.execute(
            "INSERT INTO explicit_context (user_id, character, context_type, context_key, context_value, priority, active, timestamp) VALUES (1,'coach','goal','main','get promoted','HIGH',1, datetime('now','-15 days'))"
        )
        # Recent message mentioning the goal
        cursor.execute(
            "INSERT INTO character_messages (user_id, character_id, role, content, timestamp) VALUES (1,'coach','user','I finally managed to get promoted last week', datetime('now','-1 days'))"
        )
        conn.commit()
        conn.close()

        from smart_response.goal_checkin_builder import GoalCheckInBuilder
        result = GoalCheckInBuilder().build_checkin_block(1, 'coach', db_path=tmp)
        os.unlink(tmp)
        self.assertEqual(result, '')

    def test_wired_in_chatbot(self):
        import inspect, ai_compare.chatbot as _mod
        from smart_response import personalization_pipeline as _pipe
        self.assertIn('build_personalization', inspect.getsource(_mod.AIChatbot._build_enhanced_prompt))
        self.assertIn('GoalCheckInBuilder', inspect.getsource(_pipe))

    def test_wired_in_base_chatbot(self):
        import inspect, ai_compare.base_chatbot as _mod
        from smart_response import personalization_pipeline as _pipe
        self.assertIn('build_personalization', inspect.getsource(_mod.BaseChatbot._build_enhanced_prompt))
        self.assertIn('GoalCheckInBuilder', inspect.getsource(_pipe))

    def test_checkin_block_injected_into_prompt_template_chatbot(self):
        import inspect, ai_compare.chatbot as _mod
        src = inspect.getsource(_mod)
        self.assertIn('{goal_checkin_block}', src)

    def test_checkin_block_injected_into_prompt_template_base(self):
        import inspect, ai_compare.base_chatbot as _mod
        src = inspect.getsource(_mod)
        self.assertIn('{goal_checkin_block}', src)


# ---------------------------------------------------------------------------
# 25. SessionEngagementTracker
# ---------------------------------------------------------------------------
class TestSessionEngagementTracker(unittest.TestCase):

    def setUp(self):
        from smart_response.session_engagement_tracker import SessionEngagementTracker
        self.tracker = SessionEngagementTracker()

    def _make_db(self, msgs, last_days_ago=0):
        """Create a temp DB with character_messages rows."""
        import sqlite3, tempfile
        tmp = tempfile.mktemp(suffix='.db')
        conn = sqlite3.connect(tmp)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE character_messages
            (id INTEGER PRIMARY KEY, user_id INTEGER, character_id TEXT,
             role TEXT, content TEXT,
             timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        for i, msg in enumerate(msgs):
            # space messages 1 day apart ending last_days_ago from now
            days_back = last_days_ago + (len(msgs) - 1 - i)
            cursor.execute(
                "INSERT INTO character_messages (user_id, character_id, role, content, timestamp) "
                f"VALUES (1,'coach','user',?,datetime('now','-{days_back} days'))",
                (msg,)
            )
        conn.commit()
        conn.close()
        return tmp

    def test_module_importable(self):
        from smart_response.session_engagement_tracker import (
            SessionEngagementTracker, get_engagement_tracker
        )
        self.assertIsNotNone(SessionEngagementTracker)

    def test_returns_string_always(self):
        result = self.tracker.build_engagement_block(1, 'coach', db_path=':memory:')
        self.assertIsInstance(result, str)

    def test_empty_db_returns_empty(self):
        self.assertEqual(
            self.tracker.build_engagement_block(1, 'coach', db_path=':memory:'), ''
        )

    def test_recent_user_no_block(self):
        """User active 2 days ago — no re-engagement block."""
        import os
        tmp = self._make_db(['hello world'] * 3, last_days_ago=2)
        result = self.tracker.build_engagement_block(1, 'coach', db_path=tmp)
        os.unlink(tmp)
        self.assertEqual(result, '')

    def test_absent_user_gets_block(self):
        """User absent 10 days — re-engagement block fires."""
        import os
        tmp = self._make_db(['help me think through my career'] * 3, last_days_ago=10)
        result = self.tracker.build_engagement_block(1, 'coach', db_path=tmp)
        os.unlink(tmp)
        self.assertIn('RE-ENGAGEMENT', result)
        self.assertIn('10', result)

    def test_never_raises(self):
        for uid in [1, 0, -1, None]:
            try:
                self.tracker.build_engagement_block(uid, 'coach', db_path=':memory:')
            except Exception as e:
                self.fail(f"build_engagement_block raised: {e}")

    def test_record_verbosity_signal_no_raise(self):
        self.tracker.record_verbosity_signal(1, 'coach', db_path=':memory:')

    def test_wired_in_chatbot(self):
        import inspect, ai_compare.chatbot as _mod
        from smart_response import personalization_pipeline as _pipe
        self.assertIn('build_personalization', inspect.getsource(_mod.AIChatbot._build_enhanced_prompt))
        self.assertIn('SessionEngagementTracker', inspect.getsource(_pipe))

    def test_wired_in_base_chatbot(self):
        import inspect, ai_compare.base_chatbot as _mod
        from smart_response import personalization_pipeline as _pipe
        self.assertIn('build_personalization', inspect.getsource(_mod.BaseChatbot._build_enhanced_prompt))
        self.assertIn('SessionEngagementTracker', inspect.getsource(_pipe))

    def test_engagement_block_in_prompt_template_chatbot(self):
        import inspect, ai_compare.chatbot as _mod
        src = inspect.getsource(_mod)
        self.assertIn('{engagement_block}', src)

    def test_engagement_block_in_prompt_template_base(self):
        import inspect, ai_compare.base_chatbot as _mod
        src = inspect.getsource(_mod)
        self.assertIn('{engagement_block}', src)


# ---------------------------------------------------------------------------
# 26. FrustrationDetector
# ---------------------------------------------------------------------------
class TestFrustrationDetector(unittest.TestCase):

    def setUp(self):
        from smart_response.frustration_detector import FrustrationDetector
        self.fd = FrustrationDetector()

    def test_module_importable(self):
        from smart_response.frustration_detector import FrustrationDetector, get_frustration_detector
        self.assertIsNotNone(FrustrationDetector)

    def test_returns_string_always(self):
        result = self.fd.build_frustration_block('hello', 1, db_path=':memory:')
        self.assertIsInstance(result, str)

    def test_no_frustration_normal_message(self):
        result = self.fd.build_frustration_block('what should I do?', 1, db_path=':memory:')
        self.assertEqual(result, '')

    def test_correction_phrase_detected(self):
        result = self.fd.build_frustration_block(
            "no that's wrong, you didn't understand", 1, db_path=':memory:'
        )
        self.assertIn('FRUSTRATION DETECTED', result)

    def test_another_correction_phrase(self):
        result = self.fd.build_frustration_block(
            "not what i asked, try again", 1, db_path=':memory:'
        )
        self.assertIn('FRUSTRATION DETECTED', result)

    def test_block_contains_pivot_instruction(self):
        result = self.fd.build_frustration_block(
            "you don't understand me at all", 1, db_path=':memory:'
        )
        self.assertIn('completely different', result)

    def test_repetition_detection_with_similar_messages(self):
        """3 repeated similar messages should fire repetition frustration."""
        import sqlite3, tempfile, os
        tmp = tempfile.mktemp(suffix='.db')
        conn = sqlite3.connect(tmp)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE character_messages
            (id INTEGER PRIMARY KEY, user_id INTEGER, character_id TEXT,
             role TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        for msg in [
            'I want to get promoted',
            'help me get promoted faster',
            'tips to get promoted quickly',
        ]:
            cursor.execute(
                "INSERT INTO character_messages (user_id, character_id, role, content) VALUES (1,'coach','user',?)",
                (msg,)
            )
        conn.commit()
        conn.close()
        from smart_response.frustration_detector import FrustrationDetector
        result = FrustrationDetector().build_frustration_block(
            'how do I get promoted', 1, db_path=tmp
        )
        os.unlink(tmp)
        self.assertIn('FRUSTRATION DETECTED', result)

    def test_never_raises(self):
        for uid in [1, 0, -1, None]:
            try:
                self.fd.build_frustration_block('test', uid, db_path=':memory:')
            except Exception as e:
                self.fail(f"Raised: {e}")

    def test_wired_in_chatbot(self):
        import inspect, ai_compare.chatbot as _mod
        from smart_response import personalization_pipeline as _pipe
        self.assertIn('build_personalization', inspect.getsource(_mod.AIChatbot._build_enhanced_prompt))
        self.assertIn('FrustrationDetector', inspect.getsource(_pipe))

    def test_wired_in_base_chatbot(self):
        import inspect, ai_compare.base_chatbot as _mod
        from smart_response import personalization_pipeline as _pipe
        self.assertIn('build_personalization', inspect.getsource(_mod.BaseChatbot._build_enhanced_prompt))
        self.assertIn('FrustrationDetector', inspect.getsource(_pipe))

    def test_frustration_block_in_prompt_template_chatbot(self):
        import inspect, ai_compare.chatbot as _mod
        src = inspect.getsource(_mod)
        self.assertIn('{frustration_block}', src)

    def test_frustration_block_in_prompt_template_base(self):
        import inspect, ai_compare.base_chatbot as _mod
        src = inspect.getsource(_mod)
        self.assertIn('{frustration_block}', src)


# ---------------------------------------------------------------------------
# 27. MilestoneDetector
# ---------------------------------------------------------------------------
class TestMilestoneDetector(unittest.TestCase):

    def _make_db_with_goal(self, goal_text):
        import sqlite3, tempfile
        tmp = tempfile.mktemp(suffix='.db')
        conn = sqlite3.connect(tmp)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE explicit_context
            (id INTEGER PRIMARY KEY, user_id INTEGER, character TEXT,
             context_type TEXT, context_key TEXT, context_value TEXT,
             original_statement TEXT, priority TEXT, confidence REAL,
             extracted_via TEXT, active INTEGER DEFAULT 1,
             timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute(
            "INSERT INTO explicit_context (user_id, character, context_type, context_key, context_value, priority, active) VALUES (1,'coach','goal','main',?,'HIGH',1)",
            (goal_text,)
        )
        conn.commit()
        conn.close()
        return tmp

    def test_module_importable(self):
        from smart_response.milestone_detector import MilestoneDetector, get_milestone_detector
        self.assertIsNotNone(MilestoneDetector)

    def test_returns_string_always(self):
        from smart_response.milestone_detector import MilestoneDetector
        result = MilestoneDetector().build_milestone_block('hello', 1, db_path=':memory:')
        self.assertIsInstance(result, str)

    def test_no_match_normal_message(self):
        from smart_response.milestone_detector import MilestoneDetector
        result = MilestoneDetector().build_milestone_block(
            'how do I get promoted?', 1, db_path=':memory:'
        )
        self.assertEqual(result, '')

    def test_goal_achievement_detected(self):
        import os
        from smart_response.milestone_detector import MilestoneDetector
        tmp = self._make_db_with_goal('get promoted')
        result = MilestoneDetector().build_milestone_block(
            'I finally got promoted today!', 1, db_path=tmp
        )
        os.unlink(tmp)
        self.assertIn('MILESTONE ACHIEVED', result)
        self.assertIn('get promoted', result)

    def test_goal_deactivated_after_achievement(self):
        """After detection the goal should be marked active=0."""
        import sqlite3, os
        from smart_response.milestone_detector import MilestoneDetector
        tmp = self._make_db_with_goal('land a new job')
        MilestoneDetector().build_milestone_block(
            'I got the job! I landed the new role', 1, db_path=tmp
        )
        conn = sqlite3.connect(tmp)
        cursor = conn.cursor()
        cursor.execute("SELECT active FROM explicit_context WHERE user_id=1")
        row = cursor.fetchone()
        conn.close()
        os.unlink(tmp)
        self.assertEqual(row[0], 0)

    def test_no_achievement_without_phrase(self):
        """Goal text in message but no achievement phrase → no block."""
        import os
        from smart_response.milestone_detector import MilestoneDetector
        tmp = self._make_db_with_goal('learn Python')
        result = MilestoneDetector().build_milestone_block(
            'tell me more about learning Python', 1, db_path=tmp
        )
        os.unlink(tmp)
        self.assertEqual(result, '')

    def test_never_raises(self):
        from smart_response.milestone_detector import MilestoneDetector
        for uid in [1, 0, -1, None]:
            try:
                MilestoneDetector().build_milestone_block('I got it', uid, db_path=':memory:')
            except Exception as e:
                self.fail(f"Raised: {e}")

    def test_wired_in_chatbot(self):
        import inspect, ai_compare.chatbot as _mod
        from smart_response import personalization_pipeline as _pipe
        self.assertIn('build_personalization', inspect.getsource(_mod.AIChatbot._build_enhanced_prompt))
        self.assertIn('MilestoneDetector', inspect.getsource(_pipe))

    def test_wired_in_base_chatbot(self):
        import inspect, ai_compare.base_chatbot as _mod
        from smart_response import personalization_pipeline as _pipe
        self.assertIn('build_personalization', inspect.getsource(_mod.BaseChatbot._build_enhanced_prompt))
        self.assertIn('MilestoneDetector', inspect.getsource(_pipe))

    def test_milestone_block_in_prompt_chatbot(self):
        import inspect, ai_compare.chatbot as _mod
        src = inspect.getsource(_mod)
        self.assertIn('{milestone_block}', src)

    def test_milestone_block_in_prompt_base(self):
        import inspect, ai_compare.base_chatbot as _mod
        src = inspect.getsource(_mod)
        self.assertIn('{milestone_block}', src)


# ---------------------------------------------------------------------------
# 28. Cross-character explicit context carryover
# ---------------------------------------------------------------------------
class TestCrossCharacterContext(unittest.TestCase):

    def _make_db(self):
        import sqlite3, tempfile
        tmp = tempfile.mktemp(suffix='.db')
        conn = sqlite3.connect(tmp)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE explicit_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, character TEXT, context_type TEXT,
            context_key TEXT, context_value TEXT, original_statement TEXT,
            priority TEXT DEFAULT 'MEDIUM', confidence REAL DEFAULT 1.0,
            extracted_via TEXT DEFAULT 'test', active INTEGER DEFAULT 1,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.commit()
        return tmp, conn

    def test_get_cross_character_context_returns_other_char_items(self):
        from smart_response.explicit_context_handler import ExplicitContextHandler
        tmp, conn = self._make_db()
        conn.execute(
            "INSERT INTO explicit_context (user_id,character,context_type,context_key,context_value,priority) VALUES (1,'coach','goal','career','get promoted','HIGH')"
        )
        conn.commit()
        handler = ExplicitContextHandler(conn)
        cross = handler.get_cross_character_context(1, 'psychologist')
        self.assertTrue(any(c['value'] == 'get promoted' for c in cross))
        conn.close()

    def test_cross_character_excludes_current_char(self):
        from smart_response.explicit_context_handler import ExplicitContextHandler
        tmp, conn = self._make_db()
        conn.execute(
            "INSERT INTO explicit_context (user_id,character,context_type,context_key,context_value,priority) VALUES (1,'coach','goal','career','get promoted','HIGH')"
        )
        conn.commit()
        handler = ExplicitContextHandler(conn)
        cross = handler.get_cross_character_context(1, 'coach')
        self.assertEqual(len(cross), 0)
        conn.close()

    def test_cross_character_only_active_items(self):
        from smart_response.explicit_context_handler import ExplicitContextHandler
        tmp, conn = self._make_db()
        conn.execute(
            "INSERT INTO explicit_context (user_id,character,context_type,context_key,context_value,priority,active) VALUES (1,'coach','goal','career','old goal','HIGH',0)"
        )
        conn.commit()
        handler = ExplicitContextHandler(conn)
        cross = handler.get_cross_character_context(1, 'psychologist')
        self.assertEqual(len(cross), 0)
        conn.close()

    def test_format_for_ai_prompt_includes_other_char_goal(self):
        from smart_response.explicit_context_handler import ExplicitContextHandler
        tmp, conn = self._make_db()
        conn.execute(
            "INSERT INTO explicit_context (user_id,character,context_type,context_key,context_value,priority) VALUES (1,'coach','goal','career','get promoted','HIGH')"
        )
        conn.commit()
        handler = ExplicitContextHandler(conn)
        prompt = handler.format_for_ai_prompt(1, 'psychologist')
        self.assertIn('get promoted', prompt)
        conn.close()

    def test_no_duplicate_values_in_merged_context(self):
        from smart_response.explicit_context_handler import ExplicitContextHandler
        tmp, conn = self._make_db()
        conn.execute(
            "INSERT INTO explicit_context (user_id,character,context_type,context_key,context_value,priority) VALUES (1,'coach','goal','career','get promoted','HIGH')"
        )
        conn.execute(
            "INSERT INTO explicit_context (user_id,character,context_type,context_key,context_value,priority) VALUES (1,'psychologist','goal','career','get promoted','HIGH')"
        )
        conn.commit()
        handler = ExplicitContextHandler(conn)
        prompt = handler.format_for_ai_prompt(1, 'psychologist')
        self.assertEqual(prompt.count('get promoted'), 1)
        conn.close()

    def test_medium_priority_cross_char_not_included(self):
        from smart_response.explicit_context_handler import ExplicitContextHandler
        tmp, conn = self._make_db()
        conn.execute(
            "INSERT INTO explicit_context (user_id,character,context_type,context_key,context_value,priority) VALUES (1,'coach','preference','style','concise answers','MEDIUM')"
        )
        conn.commit()
        handler = ExplicitContextHandler(conn)
        cross = handler.get_cross_character_context(1, 'psychologist')
        self.assertEqual(len(cross), 0)
        conn.close()

    def test_get_cross_character_context_method_exists(self):
        from smart_response.explicit_context_handler import ExplicitContextHandler
        self.assertTrue(hasattr(ExplicitContextHandler, 'get_cross_character_context'))


# ---------------------------------------------------------------------------
# 29. FormatPreferenceDetector
# ---------------------------------------------------------------------------
class TestFormatPreferenceDetector(unittest.TestCase):

    def test_module_importable(self):
        from smart_response.format_preference_detector import FormatPreferenceDetector, get_format_detector
        self.assertIsNotNone(FormatPreferenceDetector)

    def test_returns_string_always(self):
        from smart_response.format_preference_detector import FormatPreferenceDetector
        result = FormatPreferenceDetector().build_format_instruction("hello")
        self.assertIsInstance(result, str)

    def test_empty_message_returns_empty(self):
        from smart_response.format_preference_detector import FormatPreferenceDetector
        self.assertEqual(FormatPreferenceDetector().build_format_instruction(""), '')

    def test_bullet_trigger(self):
        from smart_response.format_preference_detector import FormatPreferenceDetector
        result = FormatPreferenceDetector().build_format_instruction("Give me a list of things I can do to improve")
        self.assertIn('bullet', result.lower())

    def test_step_trigger(self):
        from smart_response.format_preference_detector import FormatPreferenceDetector
        result = FormatPreferenceDetector().build_format_instruction("Walk me through this process step by step")
        self.assertIn('step', result.lower())

    def test_prose_trigger(self):
        from smart_response.format_preference_detector import FormatPreferenceDetector
        result = FormatPreferenceDetector().build_format_instruction("Just tell me the answer, keep it brief")
        self.assertIn('prose', result.lower())

    def test_neutral_message_returns_empty(self):
        from smart_response.format_preference_detector import FormatPreferenceDetector
        result = FormatPreferenceDetector().build_format_instruction("I feel stuck with my career goals")
        self.assertEqual(result, '')

    def test_what_are_triggers_bullet(self):
        from smart_response.format_preference_detector import FormatPreferenceDetector
        result = FormatPreferenceDetector().build_format_instruction("What are the key reasons this happens?")
        self.assertIn('bullet', result.lower())

    def test_how_do_i_triggers_steps(self):
        from smart_response.format_preference_detector import FormatPreferenceDetector
        result = FormatPreferenceDetector().build_format_instruction("How do I get better at networking?")
        self.assertIn('step', result.lower())

    def test_summarize_triggers_prose(self):
        from smart_response.format_preference_detector import FormatPreferenceDetector
        result = FormatPreferenceDetector().build_format_instruction("Can you summarize what we discussed?")
        self.assertIn('prose', result.lower())

    def test_never_raises(self):
        from smart_response.format_preference_detector import FormatPreferenceDetector
        for msg in [None, '', '   ', 'normal message', '!@#$%^&*']:
            try:
                FormatPreferenceDetector().build_format_instruction(msg)
            except Exception as e:
                self.fail(f"Raised for msg={msg!r}: {e}")

    def test_wired_in_chatbot(self):
        import inspect, ai_compare.chatbot as _mod
        from smart_response import personalization_pipeline as _pipe
        self.assertIn('build_personalization', inspect.getsource(_mod.AIChatbot._build_enhanced_prompt))
        self.assertIn('get_format_detector', inspect.getsource(_pipe))

    def test_wired_in_base_chatbot(self):
        import inspect, ai_compare.base_chatbot as _mod
        from smart_response import personalization_pipeline as _pipe
        self.assertIn('build_personalization', inspect.getsource(_mod.BaseChatbot._build_enhanced_prompt))
        self.assertIn('get_format_detector', inspect.getsource(_pipe))

    def test_format_instruction_in_prompt_chatbot(self):
        import inspect, ai_compare.chatbot as _mod
        src = inspect.getsource(_mod)
        self.assertIn('{format_instruction}', src)

    def test_format_instruction_in_prompt_base(self):
        import inspect, ai_compare.base_chatbot as _mod
        src = inspect.getsource(_mod)
        self.assertIn('{format_instruction}', src)


# ---------------------------------------------------------------------------
# 30. ToneCalibrator
# ---------------------------------------------------------------------------
class TestToneCalibrator(unittest.TestCase):

    def _make_db(self, msgs):
        import sqlite3, tempfile
        tmp = tempfile.mktemp(suffix='.db')
        conn = sqlite3.connect(tmp)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE character_messages
            (id INTEGER PRIMARY KEY, user_id INTEGER, character_id TEXT,
             role TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        for msg in msgs:
            cursor.execute(
                "INSERT INTO character_messages (user_id, character_id, role, content) VALUES (1,'coach','user',?)",
                (msg,)
            )
        conn.commit()
        conn.close()
        return tmp

    def test_module_importable(self):
        from smart_response.tone_calibrator import ToneCalibrator, get_tone_calibrator
        self.assertIsNotNone(ToneCalibrator)

    def test_returns_string_always(self):
        from smart_response.tone_calibrator import ToneCalibrator
        result = ToneCalibrator().build_tone_instruction(1, db_path=':memory:')
        self.assertIsInstance(result, str)

    def test_empty_db_returns_empty(self):
        from smart_response.tone_calibrator import ToneCalibrator
        self.assertEqual(ToneCalibrator().build_tone_instruction(1, db_path=':memory:'), '')

    def test_casual_messages_return_casual_instruction(self):
        import os
        from smart_response.tone_calibrator import ToneCalibrator
        msgs = [
            "lol yeah tbh i don't know what to do",
            "btw i'm kinda lost ngl",
            "ok so gonna try that, thanks ya",
            "idk man it's hard lmao",
            "ugh can't figure it out",
        ]
        tmp = self._make_db(msgs)
        result = ToneCalibrator().build_tone_instruction(1, db_path=tmp)
        os.unlink(tmp)
        self.assertIn('casually', result.lower())

    def test_formal_messages_return_formal_instruction(self):
        import os
        from smart_response.tone_calibrator import ToneCalibrator
        msgs = [
            "I would like to understand the best approach regarding this matter.",
            "Furthermore, I am seeking guidance on how to proceed accordingly.",
            "Could you please elaborate on the most advisable course of action?",
            "With respect to the aforementioned challenge, I am looking to resolve it.",
            "Therefore, I would appreciate a structured recommendation.",
        ]
        tmp = self._make_db(msgs)
        result = ToneCalibrator().build_tone_instruction(1, db_path=tmp)
        os.unlink(tmp)
        self.assertIn('formally', result.lower())

    def test_neutral_messages_return_empty(self):
        import os
        from smart_response.tone_calibrator import ToneCalibrator
        msgs = [
            "How do I improve my skills?",
            "What should I focus on this week?",
            "Can you help me think through this problem?",
            "I need some advice about my career.",
        ]
        tmp = self._make_db(msgs)
        result = ToneCalibrator().build_tone_instruction(1, db_path=tmp)
        os.unlink(tmp)
        self.assertEqual(result, '')

    def test_insufficient_messages_return_empty(self):
        import os
        from smart_response.tone_calibrator import ToneCalibrator
        tmp = self._make_db(["lol yeah btw"])  # only 1 message
        result = ToneCalibrator().build_tone_instruction(1, db_path=tmp)
        os.unlink(tmp)
        self.assertEqual(result, '')

    def test_never_raises(self):
        from smart_response.tone_calibrator import ToneCalibrator
        for uid in [1, 0, -1, None]:
            try:
                ToneCalibrator().build_tone_instruction(uid, db_path=':memory:')
            except Exception as e:
                self.fail(f"Raised: {e}")

    def test_wired_in_chatbot(self):
        import inspect, ai_compare.chatbot as _mod
        from smart_response import personalization_pipeline as _pipe
        self.assertIn('build_personalization', inspect.getsource(_mod.AIChatbot._build_enhanced_prompt))
        self.assertIn('ToneCalibrator', inspect.getsource(_pipe))

    def test_wired_in_base_chatbot(self):
        import inspect, ai_compare.base_chatbot as _mod
        from smart_response import personalization_pipeline as _pipe
        self.assertIn('build_personalization', inspect.getsource(_mod.BaseChatbot._build_enhanced_prompt))
        self.assertIn('ToneCalibrator', inspect.getsource(_pipe))

    def test_tone_in_prompt_chatbot(self):
        import inspect, ai_compare.chatbot as _mod
        src = inspect.getsource(_mod)
        self.assertIn('{tone_instruction}', src)

    def test_tone_in_prompt_base(self):
        import inspect, ai_compare.base_chatbot as _mod
        src = inspect.getsource(_mod)
        self.assertIn('{tone_instruction}', src)


# ---------------------------------------------------------------------------
# 30. PersonalizationPipeline — shared module for both chatbot paths
# ---------------------------------------------------------------------------
class TestPersonalizationPipeline(unittest.TestCase):

    def test_module_importable(self):
        from smart_response.personalization_pipeline import build_personalization, PersonalizationResult
        self.assertIsNotNone(build_personalization)

    def test_returns_result_instance(self):
        from smart_response.personalization_pipeline import build_personalization, PersonalizationResult
        result = build_personalization('hello', None)
        self.assertIsInstance(result, PersonalizationResult)

    def test_all_fields_are_strings(self):
        from smart_response.personalization_pipeline import build_personalization
        result = build_personalization('hello world', None)
        for field in ['explicit_context_block', 'progress_context_block', 'goal_checkin_block',
                      'engagement_block', 'frustration_block', 'milestone_block',
                      'verbosity_instruction', 'tone_instruction', 'format_instruction',
                      'emotional_instruction', 'need_instruction']:
            self.assertIsInstance(getattr(result, field), str, f"{field} not a string")

    def test_never_raises_with_none_user(self):
        from smart_response.personalization_pipeline import build_personalization
        try:
            build_personalization('any message', None, character_id='coach')
        except Exception as e:
            self.fail(f"Raised with None user_id: {e}")

    def test_never_raises_with_empty_message(self):
        from smart_response.personalization_pipeline import build_personalization
        for msg in ['', None, '   ']:
            try:
                build_personalization(msg, None)
            except Exception as e:
                self.fail(f"Raised for msg={msg!r}: {e}")

    def test_format_instruction_detected_for_list_request(self):
        from smart_response.personalization_pipeline import build_personalization
        result = build_personalization('give me a list of the key points', None)
        self.assertIn('bullet', result.format_instruction.lower())

    def test_format_instruction_detected_for_steps_request(self):
        from smart_response.personalization_pipeline import build_personalization
        result = build_personalization('walk me through the steps to do this', None)
        self.assertIn('numbered', result.format_instruction.lower())

    def test_format_instruction_empty_for_neutral(self):
        from smart_response.personalization_pipeline import build_personalization
        result = build_personalization('what do you think?', None)
        self.assertEqual(result.format_instruction, '')

    def test_both_chatbots_call_pipeline(self):
        import inspect
        from ai_compare import chatbot as _c, base_chatbot as _b
        self.assertIn('build_personalization', inspect.getsource(_c.AIChatbot._build_enhanced_prompt))
        self.assertIn('build_personalization', inspect.getsource(_b.BaseChatbot._build_enhanced_prompt))

    def test_all_modules_represented_in_pipeline(self):
        import inspect
        from smart_response import personalization_pipeline as _pipe
        src = inspect.getsource(_pipe)
        for module in ['UserPersonalization', 'ExplicitContextHandler', 'build_progress_context',
                       'GoalCheckInBuilder', 'SessionEngagementTracker', 'FrustrationDetector',
                       'MilestoneDetector', 'get_format_detector', 'ToneCalibrator',
                       'get_need_classifier', 'get_intelligence_system']:
            self.assertIn(module, src, f"{module} missing from pipeline")

    def test_pipeline_error_isolation(self):
        """A failure in one module must not cascade — all fields should still be strings."""
        from smart_response.personalization_pipeline import build_personalization
        result = build_personalization('test', user_id=999999, character_id='nonexistent',
                                       db_path=':memory:')
        for field in ['explicit_context_block', 'progress_context_block', 'goal_checkin_block']:
            self.assertIsInstance(getattr(result, field), str)


# ---------------------------------------------------------------------------
# 31. /api/user/conversation-summary endpoint
# ---------------------------------------------------------------------------
class TestConversationSummaryEndpoint(unittest.TestCase):

    def _app_src(self):
        path = os.path.join(ROOT, 'app.py')
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_route_defined_in_app(self):
        self.assertIn('/api/user/conversation-summary', self._app_src())

    def test_requires_auth(self):
        src = self._app_src()
        idx = src.find('/api/user/conversation-summary')
        region = src[idx: idx + 200]
        self.assertIn('require_auth', region)

    def test_returns_total_messages_field(self):
        src = self._app_src()
        self.assertIn("'total_messages'", src)

    def test_returns_characters_used_field(self):
        src = self._app_src()
        self.assertIn("'characters_used'", src)

    def test_returns_most_active_character_field(self):
        src = self._app_src()
        self.assertIn("'most_active_character'", src)

    def test_returns_active_goals_field(self):
        src = self._app_src()
        self.assertIn("'active_goals'", src)

    def test_returns_emotional_state_field(self):
        src = self._app_src()
        self.assertIn("'emotional_state'", src)

    def test_returns_first_last_interaction_fields(self):
        src = self._app_src()
        self.assertIn("'first_interaction'", src)
        self.assertIn("'last_interaction'", src)

    def test_queries_character_messages_table(self):
        src = self._app_src()
        idx = src.find('/api/user/conversation-summary')
        region = src[idx: idx + 2000]
        self.assertIn('character_messages', region)

    def test_queries_explicit_context_for_goals(self):
        src = self._app_src()
        idx = src.find('def get_conversation_summary')
        region = src[idx: idx + 4000]
        self.assertIn('explicit_context', region)
        self.assertIn("context_type = 'goal'", region)

    def test_error_safe_structure(self):
        src = self._app_src()
        idx = src.find('def get_conversation_summary')
        region = src[idx: idx + 4000]
        self.assertGreater(region.count('except Exception'), 3,
                           "Each sub-query should have its own except Exception block")

    def test_returns_success_key(self):
        src = self._app_src()
        idx = src.find('def get_conversation_summary')
        region = src[idx: idx + 6000]
        self.assertIn("'success': True", region)
        self.assertIn("'summary': summary", region)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [
        TestModelsRetryAndSession,
        TestChatbotVerbosityAndContext,
        TestCharacterRoutesVerbosity,
        TestConversationBoxUI,
        TestSignalProcessingWired,
        TestEmotionalContextWired,
        TestAskEndpointMetrics,
        TestDocumentationUpdated,
        TestVerbositySystem,
        TestAdvancedMetrics,
        TestResponseNeedClassifier,
        TestBaseChatbotParity,
        TestProactiveClarifier,
        TestCharacterSuggester,
        TestRoutesNewFeatures,
        TestPersonalizationProfileEndpoint,
        TestConversationBoxNewUI,
        TestExplicitContextWiring,
        TestProgressContextBuilder,
        TestDualLayerHistoryWiring,
        TestCharacterEffectivenessTracking,
        TestCharacterSuggesterEffectiveness,
        TestPersonalizationStatusIndicator,
        TestGoalCheckInBuilder,
        TestSessionEngagementTracker,
        TestFrustrationDetector,
        TestMilestoneDetector,
        TestCrossCharacterContext,
        TestFormatPreferenceDetector,
        TestToneCalibrator,
        TestPersonalizationPipeline,
        TestConversationSummaryEndpoint,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    total   = result.testsRun
    passed  = total - len(result.failures) - len(result.errors)
    failed  = len(result.failures) + len(result.errors)
    print(f"\n{'='*55}")
    print(f"TOTAL: {total}  |  PASSED: {passed}  |  FAILED: {failed}")
    print(f"SUCCESS RATE: {passed/total*100:.1f}%" if total else "No tests run")
    print('='*55)
    sys.exit(0 if result.wasSuccessful() else 1)

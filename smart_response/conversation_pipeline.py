"""
Shared Conversation Enrichment Pipeline

Extracts all intelligence features into a single reusable pipeline that both
the philosophy character endpoint and domain character endpoint call.

This ensures ALL characters get the same enrichment:
- User Context Manager (preferences, goals, language)
- Goal Coaching (adaptive coaching context)
- Personality Integration (Big5 traits → AI prompt)
- Adaptive Companion (implicit needs, micro-steps, tone)
- Follow-up Suggestions (learned user preferences)
- User Intelligence (behavioral patterns, engagement)
- Explicit Context Handler ("I'm feeling X", "My goal is Y")
- File Attachments (user-uploaded docs)
- Conversation History (multi-exchange context window)
- Situation Analysis (emotional state, goal type)
- Proactive Clarification (ambiguity detection)
- Character Collaboration (Moltbook multi-agent)
- Event Bus (publish events)
- Effectiveness Learner (outcome tracking)
- Trait Inference (continuous Big5 refinement)
- AI Summarization (periodic summaries)
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


class ConversationPipeline:
    """
    Shared enrichment pipeline for all character types.
    
    Usage:
        pipeline = ConversationPipeline(
            user_context_mgr=user_context_mgr,
            goal_coaching_system=goal_coaching_system,
            personality_integrator=personality_integrator,
            ...
        )
        
        # Before AI call — enrich context
        context = pipeline.enrich_context(user_id, message, character_id, context)
        
        # After AI call — post-process
        pipeline.post_process(user_id, message, character_id, ai_response, context, session_id)
    """
    
    def __init__(self, **kwargs):
        """Accept all system references. Each is optional — pipeline degrades gracefully."""
        self.user_context_mgr = kwargs.get('user_context_mgr')
        self.goal_coaching_system = kwargs.get('goal_coaching_system')
        self.personality_integrator = kwargs.get('personality_integrator')
        self.integrated_db = kwargs.get('integrated_db')
        self.smart_response_conn = kwargs.get('smart_response_conn')
        self.clarification_system = kwargs.get('clarification_system')
        self.character_trait_system = kwargs.get('character_trait_system')
        self.explicit_context_handler = kwargs.get('explicit_context_handler')
        self.collaboration_system = kwargs.get('collaboration_system')
        self.effectiveness_learner = kwargs.get('effectiveness_learner')
        self.event_bus = kwargs.get('event_bus')
        self.trait_inference = kwargs.get('trait_inference')
        self.user_personalization = kwargs.get('user_personalization')
        self.greeting_system = kwargs.get('greeting_system')
        self.domain_character_manager = kwargs.get('domain_character_manager')
    
    # ================================================================
    # PRE-AI ENRICHMENT (builds context before AI call)
    # ================================================================
    
    def enrich_context(self, user_id: int, message: str, character_id: str,
                       context: Dict) -> Dict:
        """
        Run all enrichment steps to build a rich context dict before AI call.
        Each step is wrapped in try/except so failures are non-fatal.
        
        Args:
            user_id: Current user
            message: User's message text
            character_id: Target character (e.g. 'coordinator', 'stoic_philosopher')
            context: Base context dict (already has user_id, is_admin, etc.)
        
        Returns:
            Enriched context dict with user_profile, coaching_context, etc.
        """
        # 1. User Context Manager (preferences, goals, language patterns)
        self._enrich_user_context(user_id, message, character_id, context)
        
        # 2. Goal Coaching (adaptive coaching context)
        self._enrich_goal_coaching(user_id, message, context)
        
        # 3. Personality Integration (Big5 → AI prompt)
        self._enrich_personality(user_id, message, context)
        
        # 4. File Attachments
        self._enrich_attachments(user_id, character_id, context)
        
        # 5. Character History Insights
        self._enrich_history_insights(user_id, character_id, context)
        
        # 6. Adaptive Companion (implicit needs, micro-steps)
        self._enrich_adaptive_companion(user_id, message, character_id, context)
        
        # 7. Follow-up Suggestions (learned preferences)
        self._enrich_follow_up_suggestions(user_id, context)
        
        # 8. User Intelligence (behavioral patterns)
        self._enrich_user_intelligence(user_id, message, character_id, context)
        
        # 9. Conversation History (recent exchanges for AI context)
        self._enrich_conversation_history(user_id, character_id, context)
        
        # 10. Situation Analysis (emotional state, goal type)
        self._enrich_situation_analysis(message, context)
        
        # 11. Explicit Context Extraction ("I'm feeling X", "My goal is Y")
        self._enrich_explicit_context(user_id, character_id, message, context)
        
        return context
    
    # ================================================================
    # POST-AI ENRICHMENT (after AI response is generated)
    # ================================================================
    
    def post_process(self, user_id: int, message: str, character_id: str,
                     ai_response_text: str, context: Dict,
                     session_id: str = None,
                     model: str = 'unknown') -> Dict:
        """
        Run all post-AI-call processing steps.
        
        Returns dict with:
            - clarification_data: Any clarification questions appended
            - collaboration_data: Any collaboration enrichment
            - situation: Situation analysis result
            - response_text: Potentially enriched AI response text
        """
        result = {
            'response_text': ai_response_text,
            'clarification_data': None,
            'collaboration_data': None,
            'situation': context.get('situation_analysis'),
        }
        
        # 12. Proactive Clarification (append question to response)
        result['clarification_data'], result['response_text'] = \
            self._post_clarification(message, result['response_text'], context)
        
        # 13. Character Collaboration (multi-perspective enrichment)
        result['collaboration_data'], result['response_text'] = \
            self._post_collaboration(user_id, message, result['response_text'], context)
        
        # 14. Event Bus (publish message.sent)
        self._post_event_bus(user_id, session_id, character_id, model,
                            bool(result['collaboration_data']))
        
        # 15. Effectiveness Learner (periodic outcome analysis)
        self._post_effectiveness(user_id, message, character_id, session_id)
        
        # 16. Trait Inference (continuous Big5 refinement)
        self._post_trait_inference(user_id)
        
        # 17. AI Summarization (periodic summaries)
        self._post_summarization(user_id, character_id, context)
        
        return result
    
    # ================================================================
    # INDIVIDUAL ENRICHMENT STEPS
    # ================================================================
    
    def _append_to_profile(self, context: Dict, text: str):
        """Helper: append text to user_profile in context."""
        existing = context.get('user_profile', '')
        if existing:
            context['user_profile'] = f"{existing}\n\n{text}"
        else:
            context['user_profile'] = text
    
    def _enrich_user_context(self, user_id: int, message: str,
                             character_id: str, context: Dict):
        """Step 1: User Context Manager — preferences, goals, language patterns."""
        if not self.user_context_mgr:
            return
        try:
            user_context = self.user_context_mgr.process_message(
                user_id, message, character_id,
                message_id=context.get('history_id')
            )
            context.update(user_context)
            
            user_context_prompt = self.user_context_mgr.format_context_for_prompt(user_context)
            if user_context_prompt:
                self._append_to_profile(context, user_context_prompt)
                logger.info("[USER_CONTEXT] Added user profile for AI")
            
            if user_context.get('references_past'):
                logger.info("[USER_CONTEXT] User references past conversation - expanding context")
        except Exception as e:
            logger.warning(f"User context processing failed: {e}")
    
    def _enrich_goal_coaching(self, user_id: int, message: str, context: Dict):
        """Step 2: Goal Coaching — adaptive coaching context."""
        if not self.goal_coaching_system:
            return
        try:
            coaching_context = self.goal_coaching_system.get_coaching_context_for_prompt(user_id, message)
            if coaching_context:
                context['coaching_context'] = coaching_context
                logger.info(f"[COACHING] Added adaptive coaching context for user {user_id}")
        except Exception as e:
            logger.warning(f"Goal coaching context failed: {e}")
    
    def _enrich_personality(self, user_id: int, message: str, context: Dict):
        """Step 3: Personality Integration — Big5 traits → AI prompt."""
        if not self.personality_integrator:
            return
        try:
            conversation_state = self.personality_integrator.get_conversation_state_from_message(message)
            personality_context = self.personality_integrator.get_personality_context(
                user_id, conversation_state
            )
            personality_prompt = self.personality_integrator.format_for_prompt(personality_context)
            if personality_prompt:
                self._append_to_profile(context, personality_prompt)
                logger.info(f"[PERSONALITY] Added (source: {personality_context.trait_source}, "
                           f"confidence: {personality_context.trait_confidence:.0%})")
                if personality_context.change_detected:
                    logger.info(f"[PERSONALITY] Change detected: {personality_context.change_summary}")
        except Exception as e:
            logger.warning(f"Personality integration failed: {e}")
    
    def _enrich_attachments(self, user_id: int, character_id: str, context: Dict):
        """Step 4: File Attachments — user-uploaded docs in AI context."""
        if not self.integrated_db:
            return
        try:
            attachments = self.integrated_db.get_active_attachments(user_id, character_id)
            if attachments:
                from app import format_attachments_for_ai
                attachment_context = format_attachments_for_ai(attachments)
                if attachment_context:
                    context['file_attachments'] = attachment_context
                    logger.info(f"[ATTACHMENTS] Added {len(attachments)} file(s) to context")
        except Exception as e:
            logger.warning(f"File attachment context failed: {e}")
    
    def _enrich_history_insights(self, user_id: int, character_id: str, context: Dict):
        """Step 5: Character History Insights — personalization from past interpretations."""
        if not self.domain_character_manager:
            return
        try:
            character = (self.domain_character_manager.characters.get(character_id)
                        or self.domain_character_manager.coordinator)
            if character and hasattr(character, 'get_personalization_context'):
                personalization = character.get_personalization_context(user_id)
                if personalization:
                    self._append_to_profile(context, personalization)
                    logger.info("[HISTORY_INSIGHTS] Added personalization from past interpretations")
        except Exception as e:
            logger.warning(f"Character history insights failed: {e}")
    
    def _enrich_adaptive_companion(self, user_id: int, message: str,
                                    character_id: str, context: Dict):
        """Step 6: Adaptive Companion — implicit needs, micro-steps, tone adaptation."""
        if not self.smart_response_conn:
            return
        try:
            from smart_response.adaptive_companion import get_adaptive_companion
            adaptive = get_adaptive_companion(self.smart_response_conn)
            adaptive_context = adaptive.build_adaptive_context(
                user_id, message, character_id,
                user_history=context.get('message_history', [])
            )
            if adaptive_context:
                context['adaptive_context'] = adaptive_context
                implicit_need = adaptive_context.get('implicit_needs', {}).get('primary_need', 'unknown')
                logger.info(f"[ADAPTIVE] Detected implicit need: {implicit_need}")
        except Exception as e:
            logger.warning(f"Adaptive companion failed: {e}")
    
    def _enrich_follow_up_suggestions(self, user_id: int, context: Dict):
        """Step 7: Follow-up Suggestions — learned user preferences."""
        if not self.smart_response_conn:
            return
        try:
            from smart_response.follow_up_suggestions import get_suggestion_system
            suggestion_system = get_suggestion_system(self.smart_response_conn)
            context['db_connection'] = self.smart_response_conn
            pref_summary = suggestion_system.get_preference_summary_for_prompt(user_id)
            if pref_summary:
                self._append_to_profile(context, pref_summary)
                logger.info("[SUGGESTIONS] Added learned preferences to AI context")
        except Exception as e:
            logger.warning(f"Suggestion preferences failed: {e}")
    
    def _enrich_user_intelligence(self, user_id: int, message: str,
                                   character_id: str, context: Dict):
        """Step 8: User Intelligence — behavioral patterns, engagement signals."""
        if not self.smart_response_conn:
            return
        try:
            from smart_response.user_intelligence import get_intelligence_system
            intel_system = get_intelligence_system(self.smart_response_conn)
            context['intelligence_system'] = intel_system
            
            topic = character_id or 'general'
            is_long = len(message) > 100
            intel_system.record_engagement(
                user_id,
                'long_message' if is_long else 'message_sent',
                context={'message_length': len(message)},
                character_id=character_id,
                topic=topic
            )
            
            intel_context = intel_system.get_ai_prompt_context(user_id)
            if intel_context:
                self._append_to_profile(context, intel_context)
                logger.info("[INTELLIGENCE] Added behavioral insights to AI context")
        except Exception as e:
            logger.warning(f"User intelligence failed: {e}")
    
    def _enrich_conversation_history(self, user_id: int, character_id: str,
                                      context: Dict):
        """Step 9: Conversation History — recent exchanges for AI context window."""
        if not self.smart_response_conn:
            return
        try:
            base_exchanges = int(os.environ.get('AI_CONTEXT_EXCHANGES', 5))
            context_exchanges = base_exchanges * 2 if context.get('references_past') else base_exchanges
            
            cursor = self.smart_response_conn.cursor()
            
            # Try history_primary first (domain chars use this)
            try:
                cursor.execute('''
                    SELECT hp.user_message, hp.assistant_response, hp.character
                    FROM history_primary hp
                    LEFT JOIN message_visibility mv ON hp.id = mv.history_id AND mv.character_id = ?
                    WHERE hp.user_id = ? 
                      AND (mv.character_id = ? OR hp.character = ?)
                      AND hp.assistant_response IS NOT NULL 
                      AND hp.assistant_response != ''
                    ORDER BY hp.timestamp DESC
                    LIMIT ?
                ''', (character_id, user_id, character_id, character_id, context_exchanges))
                rows = cursor.fetchall()
            except Exception:
                rows = []
            
            # Fallback: try ai_conversations + messages (both char types use this)
            if not rows:
                try:
                    cursor.execute('''
                        SELECT m.content, m.sender_type
                        FROM messages m
                        JOIN ai_conversations c ON m.conversation_id = c.id
                        WHERE c.user_id = ? AND c.character_id = ?
                        ORDER BY m.timestamp DESC
                        LIMIT ?
                    ''', (user_id, character_id, context_exchanges * 2))
                    raw_rows = cursor.fetchall()
                    # Convert to user/assistant pairs
                    rows = []
                    i = len(raw_rows) - 1
                    while i >= 1:
                        if raw_rows[i][1] == 'user' and raw_rows[i-1][1] == 'assistant':
                            rows.append((raw_rows[i][0], raw_rows[i-1][0], character_id))
                            i -= 2
                        else:
                            i -= 1
                except Exception:
                    rows = []
            
            message_history = []
            history_token_estimate = 0
            
            for row in reversed(rows):
                user_msg, ai_resp = row[0], row[1]
                if user_msg:
                    message_history.append({'role': 'user', 'content': user_msg})
                    history_token_estimate += len(user_msg) // 4
                if ai_resp:
                    message_history.append({'role': 'assistant', 'content': ai_resp})
                    history_token_estimate += len(ai_resp) // 4
            
            if message_history:
                context['message_history'] = message_history
                context['history_token_estimate'] = history_token_estimate
                logger.info(f"[CONTEXT] Added {len(message_history)} history messages "
                           f"(~{history_token_estimate} tokens)")
        except Exception as e:
            logger.warning(f"Could not fetch conversation history: {e}")
    
    def _enrich_situation_analysis(self, message: str, context: Dict):
        """Step 10: Situation Analysis — emotional state, goal type."""
        if not self.character_trait_system:
            return
        try:
            situation = self.character_trait_system.analyze_situation(message, context)
            flags = []
            if situation.needs_validation:
                flags.append("needs_validation")
            if situation.needs_action:
                flags.append("needs_action")
            flag_str = f" [{', '.join(flags)}]" if flags else ""
            logger.info(f"[SITUATION] {situation.emotional_state} ({situation.goal_type}){flag_str}")
            
            if situation.emotional_state != 'neutral':
                context['situation_analysis'] = {
                    'emotional_state': situation.emotional_state,
                    'goal_type': situation.goal_type,
                    'needs_validation': situation.needs_validation,
                    'needs_action': situation.needs_action
                }
        except Exception as e:
            logger.warning(f"Situation analysis failed: {e}")
    
    def _enrich_explicit_context(self, user_id: int, character_id: str,
                                  message: str, context: Dict):
        """Step 11: Explicit Context — capture 'I feel X', 'My goal is Y'."""
        if not self.explicit_context_handler:
            return
        try:
            extracted = self.explicit_context_handler.extract_explicit_context(
                user_id, character_id, message
            )
            if extracted:
                logger.info(f"[EXPLICIT] Extracted {len(extracted)} explicit context items")
            
            past_prompt = self.explicit_context_handler.format_for_ai_prompt(user_id, character_id)
            if past_prompt:
                context['explicit_user_context'] = past_prompt
                logger.info("[EXPLICIT] Retrieved past explicit context for AI")
        except Exception as e:
            logger.warning(f"Explicit context extraction failed: {e}")
    
    # ================================================================
    # POST-AI STEPS
    # ================================================================
    
    def _post_clarification(self, message: str, response_text: str,
                            context: Dict) -> Tuple[Optional[Dict], str]:
        """Step 12: Proactive Clarification — append question to response."""
        if not self.clarification_system or not response_text:
            return None, response_text
        try:
            confidence, questions = self.clarification_system.analyze_message(message, context)
            if questions:
                q = questions[0]
                logger.info(f"[CLARIFICATION] Needed (confidence: {confidence.overall:.0%}): {q.question}")
                
                clarification_text = self.clarification_system.format_clarification_for_response(
                    questions[:1], context.get('user_language')
                )
                if clarification_text:
                    response_text += clarification_text
                
                return {
                    'confidence': round(confidence.overall, 3),
                    'needs_clarification': True,
                    'questions': [q.to_dict() for q in questions[:1]],
                }, response_text
        except Exception as e:
            logger.warning(f"Clarification failed: {e}")
        return None, response_text
    
    def _post_collaboration(self, user_id: int, message: str,
                            response_text: str, context: Dict) -> Tuple[Optional[Dict], str]:
        """Step 13: Character Collaboration — multi-perspective enrichment."""
        if not self.collaboration_system or not response_text:
            return None, response_text
        try:
            collab_context = {}
            collab_personality = None
            if self.personality_integrator:
                try:
                    p_ctx = self.personality_integrator.get_personality_context(user_id)
                    collab_personality = {
                        'openness': p_ctx.openness, 'conscientiousness': p_ctx.conscientiousness,
                        'extraversion': p_ctx.extraversion, 'agreeableness': p_ctx.agreeableness,
                        'neuroticism': p_ctx.neuroticism
                    }
                except Exception:
                    pass
            
            should_collab, detected_mode, rule_name = self.collaboration_system.should_collaborate(
                message, collab_context
            )
            
            if should_collab:
                if collab_personality:
                    collab_result = self.collaboration_system.personality_aware_collaborate(
                        message, user_id, personality=collab_personality,
                        context=collab_context, mode=detected_mode
                    )
                else:
                    collab_result = self.collaboration_system.orchestrate_collaboration(
                        message, user_id, collab_context, detected_mode or 'silent', rule_name
                    )
                
                if collab_result:
                    if collab_result.mode == 'silent':
                        enrichment_parts = []
                        for c in collab_result.contributions[1:]:
                            if c.get('action_suggestion'):
                                enrichment_parts.append(c['action_suggestion'])
                        if enrichment_parts:
                            response_text = response_text + "\n\n" + enrichment_parts[0][:200]
                    elif collab_result.mode == 'visible':
                        response_text = response_text + "\n\n" + collab_result.response
                    else:
                        response_text = collab_result.response
                    
                    return {
                        'collaborated': True,
                        'mode': collab_result.mode,
                        'perspectives_count': len(collab_result.participating_characters),
                        'event_id': collab_result.event_id,
                        'contributions_count': len(collab_result.contributions)
                    }, response_text
        except Exception as e:
            logger.warning(f"Collaboration enrichment failed: {e}")
        return None, response_text
    
    def _post_event_bus(self, user_id: int, session_id: str, character_id: str,
                        model: str, collaborated: bool):
        """Step 14: Event Bus — publish message.sent event."""
        if not self.event_bus or not session_id:
            return
        try:
            self.event_bus.publish_async('message.sent', {
                'session_id': session_id,
                'user_id': user_id,
                'character_id': character_id,
                'has_ai_response': True,
                'model': model,
                'collaborated': collaborated,
            }, source='conversation_pipeline')
        except Exception as e:
            logger.warning(f"Event bus publish failed: {e}")
    
    def _post_effectiveness(self, user_id: int, message: str,
                            character_id: str, session_id: str):
        """Step 15: Effectiveness Learner — periodic outcome analysis."""
        if not self.effectiveness_learner or not session_id:
            return
        try:
            msgs = self.integrated_db.get_conversation_messages(session_id, user_id)
            if not msgs:
                return
            user_msg_count = sum(1 for m in msgs if m.get('sender_type') == 'user')
            if user_msg_count > 0 and user_msg_count % 5 == 0:
                eff_char_id = character_id
                if self.character_trait_system:
                    try:
                        sit = self.character_trait_system.analyze_situation(message)
                        mc, _, _ = self.character_trait_system.match_character(sit)
                        if mc:
                            eff_char_id = mc.character_id
                    except Exception:
                        pass
                
                outcome = self.effectiveness_learner.analyze_and_record(
                    session_id, user_id, msgs, character_id=eff_char_id
                )
                logger.info(f"[EFFECTIVENESS] char={eff_char_id}, "
                           f"satisfaction={outcome.satisfaction_estimate:.2f}, "
                           f"engagement={outcome.engagement_level.value}")
                
                if self.event_bus:
                    self.event_bus.publish_async('conversation.completed', {
                        'session_id': session_id,
                        'user_id': user_id,
                        'character_id': eff_char_id,
                        'satisfaction': outcome.satisfaction_estimate,
                        'engagement': outcome.engagement_level.value,
                        'situation_type': outcome.situation_type,
                        'message_count': user_msg_count,
                    }, source='effectiveness_learner')
        except Exception as e:
            logger.warning(f"Effectiveness tracking failed: {e}")
    
    def _post_trait_inference(self, user_id: int):
        """Step 16: Trait Inference — continuous Big5 refinement."""
        if not self.trait_inference:
            return
        try:
            inference_result = self.trait_inference.run_inference_if_needed(user_id)
            if inference_result:
                logger.info(f"[TRAIT_INFERENCE] Updated traits for user {user_id} "
                           f"(confidence: {inference_result['confidence']:.0%})")
                if self.personality_integrator:
                    self.personality_integrator.invalidate_cache(user_id)
        except Exception as e:
            logger.warning(f"Trait inference failed: {e}")
    
    def _post_summarization(self, user_id: int, character_id: str, context: Dict):
        """Step 17: AI Summarization — periodic conversation summaries."""
        if not self.user_context_mgr or not context.get('needs_summary_refresh'):
            return
        if not self.smart_response_conn:
            return
        try:
            cursor = self.smart_response_conn.cursor()
            cursor.execute('''
                SELECT hp.user_message, hp.assistant_response
                FROM history_primary hp
                LEFT JOIN message_visibility mv ON hp.id = mv.history_id AND mv.character_id = ?
                WHERE hp.user_id = ?
                  AND (mv.character_id = ? OR hp.character = ?)
                  AND hp.assistant_response IS NOT NULL
                  AND hp.assistant_response != ''
                ORDER BY hp.timestamp DESC
                LIMIT 15
            ''', (character_id, user_id, character_id, character_id))
            recent_msgs = [{'user_message': r[0], 'assistant_response': r[1]} for r in cursor.fetchall()]
            
            if recent_msgs and len(recent_msgs) >= 3:
                summary = self.user_context_mgr.generate_summary(
                    user_id, character_id,
                    list(reversed(recent_msgs)),
                    context.get('history_id')
                )
                if summary:
                    logger.info("[SUMMARY] Generated conversation summary")
        except Exception as e:
            logger.warning(f"Summarization failed: {e}")


def create_pipeline(**kwargs) -> ConversationPipeline:
    """Factory function to create the pipeline."""
    return ConversationPipeline(**kwargs)

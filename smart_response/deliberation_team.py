"""
Deliberation Team

A reasoning team of 5 thinking-style agents that negotiate an answer:
- The Contrarian          (domain_contrarian)
- The First-Principles Thinker (domain_first_principles)
- The Expansionist        (domain_expansionist)
- The Outsider            (domain_outsider)
- The Executor            (domain_executor)

Flow (single real-AI round + blind coordinator negotiation):
1. Each agent produces one independent take (real AI call via DomainCharacterAI).
2. The takes are pooled and ANONYMIZED (Perspective A/B/C...) in random order.
3. The Coordinator (Aria) negotiates the anonymized takes into ONE final answer
   WITHOUT knowing which agent said what (blind synthesis).
4. Attribution (who said what) is returned separately so the UI can optionally
   reveal it — giving "with and without knowing where the comments come from".

This module deliberately REUSES existing infrastructure:
- CharacterManager           -> holds the 5 agents + coordinator
- DomainCharacterAI          -> real AI calls, budget control, failover
- CoordinatorCharacter/Aria  -> final synthesis persona
- CharacterCollaborationSystem (optional) -> logging of the collaboration event
"""

import re
import random
from typing import Dict, List, Optional, Any


# The 5 thinking-style agents that make up the team (character IDs in configs.py)
TEAM_AGENT_IDS: List[str] = [
    "domain_contrarian",
    "domain_first_principles",
    "domain_expansionist",
    "domain_outsider",
    "domain_executor",
]

COORDINATOR_ID = "coordinator"

# --- Token / size guards (keep well within provider input & output limits) ---
# Delimiter the model must emit so we can split one response back into agents.
AGENT_MARKER = "###AGENT:{agent_id}###"
_MARKER_RE = re.compile(r"^\s*#{2,4}\s*AGENT\s*:\s*([a-zA-Z0-9_]+)\s*#{2,4}\s*$", re.MULTILINE)

# Output budget for the single batched call: ~180 tokens per agent + overhead,
# hard-capped so we never exceed the model's output limit.
BATCH_TOKENS_PER_AGENT = 180
BATCH_TOKENS_OVERHEAD = 200
BATCH_TOKENS_CEILING = 3500

# Input guard: cap how much of a very long user message we inline into prompts
# (protects the input-token limit; full message stays available to the caller).
MAX_MESSAGE_CHARS = 4000
# Per-agent persona system prompts are inlined in the batched call; cap each so
# 5 personas + instructions stay small on the input side.
MAX_PERSONA_CHARS = 900


class DeliberationTeam:
    """Orchestrates a blind, coordinator-mediated negotiation among the 5 agents."""

    def __init__(self, character_manager, domain_character_ai,
                 collaboration_system=None, batch: bool = True,
                 agent_ids: Optional[List[str]] = None,
                 coordinator_id: str = COORDINATOR_ID):
        """
        Args:
            character_manager: CharacterManager instance (holds agents + coordinator)
            domain_character_ai: DomainCharacterAI instance (real AI calls)
            collaboration_system: optional CharacterCollaborationSystem for event logging
            batch: when True, gather all agent takes in ONE AI call (delimited
                   sections) to cut cost, then redistribute. Falls back to
                   per-agent calls if the batched response can't be parsed.
            agent_ids: roster of character IDs that make up this team. Defaults
                   to the built-in 5-agent deliberation team. Any registered
                   domain character (or the coordinator) can be a member.
            coordinator_id: character ID that negotiates the final answer.
        """
        self.manager = character_manager
        self.ai = domain_character_ai
        self.collaboration_system = collaboration_system
        self.batch = batch
        self.agent_ids = list(agent_ids) if agent_ids else list(TEAM_AGENT_IDS)
        self.coordinator_id = coordinator_id or COORDINATOR_ID

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def available_agents(self) -> List[str]:
        """Return this team's agent IDs that are actually registered in the manager."""
        if not self.manager:
            return []
        registered = getattr(self.manager, 'characters', {})
        return [aid for aid in self.agent_ids if aid in registered]

    def deliberate(self, message: str, context: Optional[Dict] = None,
                   reveal_attribution: bool = False,
                   user_id: Optional[int] = None,
                   batch: Optional[bool] = None,
                   is_admin: bool = False) -> Dict[str, Any]:
        """
        Run the deliberation and return a structured result.

        Args:
            message: The user's message/question.
            context: Conversation context (passed through to DomainCharacterAI).
            reveal_attribution: If True, the returned contributions include the
                agent display names. The coordinator ALWAYS negotiates blind;
                this flag only controls what is exposed to the caller/UI.
            user_id: Optional user id (for budget accounting/context).
            batch: Override the instance default. True = one combined AI call for
                all agents; False = one call per agent.

        Returns:
            {
                'final_response': str,       # coordinator's negotiated answer
                'contributions': [           # each agent's take
                    {'label': 'Perspective A', 'agent_id': ..., 'display_name': ...|None, 'content': ...},
                    ...
                ],
                'participating_agents': [display names],
                'blind': True,               # synthesis was identity-blind
                'attribution_revealed': bool,
                'event_id': int | None,
            }
        """
        context = dict(context or {})
        if user_id is not None:
            context.setdefault('user_id', user_id)
        context.setdefault('is_admin', is_admin)

        agent_ids = self.available_agents()
        if len(agent_ids) < 2:
            return {
                'final_response': None,
                'contributions': [],
                'participating_agents': [],
                'blind': True,
                'attribution_revealed': reveal_attribution,
                'event_id': None,
                'error': 'Deliberation team not available (need at least 2 agents).'
            }

        # --- Round 1: gather each agent's independent take ---
        use_batch = self.batch if batch is None else batch
        raw_takes, gather_mode = self._gather_takes(message, context, agent_ids, use_batch)

        if not raw_takes:
            return {
                'final_response': None,
                'contributions': [],
                'participating_agents': [],
                'blind': True,
                'attribution_revealed': reveal_attribution,
                'event_id': None,
                'gather_mode': gather_mode,
                'ai_calls': 0,
                'error': 'No agent produced a response.'
            }

        # --- Anonymize: shuffle + relabel as Perspective A/B/C... ---
        shuffled = list(raw_takes)
        random.shuffle(shuffled)
        labels = [f"Perspective {chr(ord('A') + i)}" for i in range(len(shuffled))]
        for label, take in zip(labels, shuffled):
            take['label'] = label

        # --- Round 2: blind coordinator negotiation (real AI) ---
        final_response = self._coordinator_negotiate(message, shuffled, context)

        # --- Optional: log via existing collaboration tables ---
        event_id = self._log_event(user_id, message, raw_takes, final_response)

        # --- Build contributions payload (attribution optional) ---
        contributions = []
        for take in shuffled:
            contributions.append({
                'label': take['label'],
                'agent_id': take['agent_id'] if reveal_attribution else None,
                'display_name': take['display_name'] if reveal_attribution else None,
                'content': take['content'],
            })

        # AI-call accounting: batched = 1 (agents) + 1 (synthesis);
        # sequential = N (agents) + 1 (synthesis).
        ai_calls = (1 if gather_mode == 'batched' else len(raw_takes)) + 1

        return {
            'final_response': final_response,
            'contributions': contributions,
            'participating_agents': [t['display_name'] for t in raw_takes],
            'blind': True,
            'attribution_revealed': reveal_attribution,
            'event_id': event_id,
            'gather_mode': gather_mode,
            'ai_calls': ai_calls,
        }

    # ------------------------------------------------------------------
    # Round 1 gathering (batched or sequential)
    # ------------------------------------------------------------------
    def _gather_takes(self, message: str, context: Dict,
                      agent_ids: List[str], use_batch: bool):
        """Collect each agent's independent take, batched into one call if possible.

        Returns (takes, mode) where mode is 'batched' or 'sequential'.
        """
        if use_batch:
            takes = self._gather_takes_batched(message, context, agent_ids)
            # Require at least 2 parsed sections to consider the batch a success.
            if len(takes) >= 2:
                return takes, 'batched'
            print("[DELIBERATION] Batched gather incomplete — falling back to per-agent calls")
        return self._gather_takes_sequential(message, context, agent_ids), 'sequential'

    def _gather_takes_batched(self, message: str, context: Dict,
                              agent_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Ask ONE AI call to produce all agents' takes in delimited sections,
        then split the response back per agent. Cuts N calls down to 1.
        """
        from .characters.configs import DOMAIN_CHARACTER_CONFIGS

        # Build the combined persona block (reuse each character's prompt + style)
        persona_blocks = []
        order = []
        for aid in agent_ids:
            character = self.manager.characters.get(aid)
            if not character:
                continue
            cfg = DOMAIN_CHARACTER_CONFIGS.get(aid, {})
            persona = self._cap(cfg.get('system_prompt', ''), MAX_PERSONA_CHARS)
            style = ""
            try:
                style = character.get_style_instructions() or ""
            except Exception:
                pass
            marker = AGENT_MARKER.format(agent_id=aid)
            block = (
                f"{marker}\n"
                f"Display name: {character.display_name}\n"
                f"{persona}"
            )
            if style:
                block += f"\nStyle: {style}"
            persona_blocks.append(block)
            order.append((aid, character.display_name))

        if len(order) < 2:
            return []

        marker_list = "\n".join(AGENT_MARKER.format(agent_id=aid) for aid, _ in order)
        combined_prompt = f"""You simulate a panel of {len(order)} DISTINCT reasoning agents. Each agent has its own persona below. Produce EACH agent's independent take on the user's message.

STRICT OUTPUT FORMAT — follow exactly:
- For every agent, output its marker line EXACTLY as given, on its own line, then that agent's take on the next lines.
- Use these markers, in this order:
{marker_list}
- Do NOT add any text before the first marker or after the last agent's take.
- Do NOT mention the markers, other agents, or that you are simulating a panel, inside the takes.
- Keep each agent's take to about 3-5 sentences, true to that agent's persona.

AGENT PERSONAS:

{chr(10).join(persona_blocks)}
"""

        capped_message = self._cap(message, MAX_MESSAGE_CHARS)
        user_message = f"The user said: \"{capped_message}\"\n\nProvide each agent's take using the required markers."

        # Output token budget scaled to number of agents, hard-capped.
        max_tokens = min(
            BATCH_TOKENS_CEILING,
            BATCH_TOKENS_PER_AGENT * len(order) + BATCH_TOKENS_OVERHEAD
        )
        call_ctx = dict(context)
        call_ctx['max_tokens_override'] = max_tokens

        try:
            raw = self.ai.call_ai_direct(
                combined_prompt, user_message, 'deliberation_batch', context=call_ctx,
                count_budget=True, user_id=context.get('user_id'),
                is_admin=context.get('is_admin', False)
            )
        except Exception as e:
            print(f"[DELIBERATION] Batched call failed: {e}")
            return []

        if not raw or not raw.strip():
            return []

        parsed = self._parse_batched(raw, order)
        return parsed

    def _parse_batched(self, raw: str, order: List) -> List[Dict[str, Any]]:
        """Split a delimited batched response back into per-agent takes."""
        name_by_id = {aid: name for aid, name in order}
        valid_ids = set(name_by_id.keys())

        # Find all markers and their positions
        matches = list(_MARKER_RE.finditer(raw))
        takes: List[Dict[str, Any]] = []

        if matches:
            for i, m in enumerate(matches):
                aid = m.group(1)
                if aid not in valid_ids:
                    continue
                start = m.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
                content = raw[start:end].strip()
                # Drop an optional leading "Display name: ..." echo line
                content = re.sub(r"^Display name:.*\n?", "", content).strip()
                if content:
                    takes.append({
                        'agent_id': aid,
                        'display_name': name_by_id[aid],
                        'content': content,
                    })

        # De-duplicate by agent_id (keep first), preserve marker order
        seen = set()
        deduped = []
        for t in takes:
            if t['agent_id'] in seen:
                continue
            seen.add(t['agent_id'])
            deduped.append(t)
        return deduped

    def _gather_takes_sequential(self, message: str, context: Dict,
                                 agent_ids: List[str]) -> List[Dict[str, Any]]:
        """One real AI call per agent (fallback / high-fidelity mode)."""
        raw_takes: List[Dict[str, Any]] = []
        for aid in agent_ids:
            character = self.manager.characters.get(aid)
            if not character:
                continue
            try:
                resp = self.ai.generate_response(character, message, context)
                content = (resp.content or "").strip()
            except Exception as e:
                print(f"[DELIBERATION] Agent {aid} failed: {e}")
                content = ""
            if content:
                raw_takes.append({
                    'agent_id': aid,
                    'display_name': character.display_name,
                    'content': content,
                })
        return raw_takes

    @staticmethod
    def _cap(text: str, max_chars: int) -> str:
        """Truncate text to max_chars, adding an ellipsis marker if cut."""
        if not text:
            return ""
        text = text.strip()
        if len(text) <= max_chars:
            return text
        return text[:max_chars].rstrip() + " […]"

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _coordinator_negotiate(self, message: str, anonymized_takes: List[Dict],
                               context: Dict) -> str:
        """Have the coordinator negotiate anonymized takes into one answer."""
        # Pull coordinator persona from configs (reuse existing system prompt)
        from .characters.configs import DOMAIN_CHARACTER_CONFIGS
        coord_cfg = DOMAIN_CHARACTER_CONFIGS.get(self.coordinator_id, {})
        coord_prompt = coord_cfg.get('system_prompt', 'You are a helpful coordinator.')

        perspectives_block = "\n\n".join(
            f"{t['label']}:\n{t['content']}" for t in anonymized_takes
        )

        system_prompt = f"""{coord_prompt}

You are chairing a reasoning team. Below are several ANONYMOUS perspectives on the
user's message. You do NOT know which team member wrote which — judge each on merit.

Your task is to NEGOTIATE these perspectives into a single, coherent answer for the user:
1. Identify where the perspectives AGREE — treat that as the solid core.
2. Identify where they CONFLICT — resolve the tension explicitly, don't just average.
3. Keep the sharpest challenge (risks/assumptions) and the most actionable next step.
4. Do NOT mention "Perspective A/B" or that this came from a team — speak in one clear voice.
5. Be concise and specific. End with the single most important next action for the user.

ANONYMOUS PERSPECTIVES:
{perspectives_block}
"""

        user_message = f"The user said: \"{message}\"\n\nGive the team's unified answer."

        try:
            result = self.ai.call_ai_direct(
                system_prompt, user_message, self.coordinator_id,
                count_budget=True, user_id=context.get('user_id'),
                is_admin=context.get('is_admin', False)
            )
        except Exception as e:
            print(f"[DELIBERATION] Coordinator synthesis failed: {e}")
            result = None

        if result and result.strip():
            return result.strip()

        # Fallback: stitch takes together if AI synthesis unavailable
        return self._fallback_synthesis(anonymized_takes)

    def _fallback_synthesis(self, anonymized_takes: List[Dict]) -> str:
        """Deterministic fallback when no AI is available."""
        parts = ["Here's how the team weighed in:\n"]
        for t in anonymized_takes:
            snippet = t['content'].split('\n')[0][:200]
            parts.append(f"- {snippet}")
        parts.append("\nStart with the most concrete next step above.")
        return "\n".join(parts)

    def _log_event(self, user_id, message, raw_takes, final_response) -> Optional[int]:
        """Reuse the collaboration logging tables if the system is available."""
        if not self.collaboration_system:
            return None
        try:
            contributions = [{
                'character_id': t['agent_id'],
                'character_name': t['display_name'],
                'interpretation': t['content'],
                'emotional_framing': '',
                'action_suggestion': '',
                'relevance_score': 1.0,
            } for t in raw_takes]
            return self.collaboration_system._log_collaboration(
                user_id or 0, message, 'deliberate', 'deliberation_team',
                [], contributions, final_response
            )
        except Exception as e:
            print(f"[DELIBERATION] Event logging failed (non-critical): {e}")
            return None


def create_deliberation_team(character_manager, domain_character_ai,
                             collaboration_system=None,
                             batch: bool = True,
                             agent_ids: Optional[List[str]] = None,
                             coordinator_id: str = COORDINATOR_ID) -> DeliberationTeam:
    """Factory for a DeliberationTeam (built-in roster by default)."""
    return DeliberationTeam(character_manager, domain_character_ai,
                            collaboration_system, batch=batch,
                            agent_ids=agent_ids, coordinator_id=coordinator_id)

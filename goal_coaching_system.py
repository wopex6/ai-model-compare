"""
Goal Coaching System - Conversational Engagement Engine

This system works BEHIND THE SCENES to help users achieve their goals through
natural, adaptive conversation - NOT rigid formal coaching.

Key Principles:
1. Strategy is invisible to users - they just experience helpful conversation
2. Adapt to users' psychology, mood, and changing needs in real-time
3. Provide SPECIFIC immediate actions, not generic advice
4. Encourage engagement through warmth, curiosity, and celebration
5. A strategy users don't follow is worthless - focus on adoption
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass


@dataclass
class GoalContext:
    """Internal context for tracking user's journey (invisible to user)"""
    goal_id: int
    title: str
    description: str
    status: str
    engagement_level: str  # high, medium, low, disengaged
    user_mood: str  # motivated, uncertain, frustrated, neutral
    last_action_taken: str
    days_since_progress: int
    blockers: List[str]
    wins: List[str]


@dataclass 
class UserPsychState:
    """Track user's psychological state for adaptive responses"""
    energy_level: str  # high, medium, low
    confidence: str  # confident, uncertain, struggling
    engagement: str  # engaged, passive, resistant
    needs_encouragement: bool
    needs_concrete_help: bool
    needs_space: bool


class GoalCoachingSystem:
    """
    Invisible coaching that feels like helpful conversation.
    
    All strategy tracking happens behind the scenes.
    Users only experience natural, adaptive support.
    
    Focus Areas:
    - Detect what user ACTUALLY needs right now (not what we planned)
    - Give ONE specific thing they can do TODAY
    - Celebrate small wins to build momentum
    - Recognize when to push vs when to support
    - Never feel like a formal coaching program
    """
    
    def __init__(self, db, ai_call_func: Callable = None):
        self.db = db
        self.ai_call_func = ai_call_func
        
        # Engagement patterns to detect user state
        self.disengagement_signals = [
            'busy', 'later', 'not now', 'maybe', 'i guess', 'whatever',
            'sure', 'ok', 'fine', "don't know", 'not sure'
        ]
        
        self.motivation_signals = [
            'excited', 'ready', 'let\'s do', 'want to', 'eager',
            'motivated', 'pumped', 'can\'t wait', 'yes!', 'absolutely'
        ]
        
        self.struggle_signals = [
            'stuck', 'confused', 'overwhelmed', 'frustrated', 'hard',
            'difficult', 'can\'t', 'struggling', 'help', 'lost'
        ]
        
        self.progress_signals = [
            'did it', 'done', 'finished', 'completed', 'achieved',
            'finally', 'managed', 'succeeded', 'worked', 'progress'
        ]
    
    def detect_user_state(self, message: str) -> UserPsychState:
        """Detect user's psychological state from their message"""
        message_lower = message.lower()
        
        # Detect engagement level
        is_disengaged = any(s in message_lower for s in self.disengagement_signals)
        is_motivated = any(s in message_lower for s in self.motivation_signals)
        is_struggling = any(s in message_lower for s in self.struggle_signals)
        has_progress = any(s in message_lower for s in self.progress_signals)
        
        # Determine engagement
        if is_disengaged:
            engagement = 'passive'
        elif is_motivated or has_progress:
            engagement = 'engaged'
        else:
            engagement = 'neutral'
        
        # Determine energy and confidence
        if is_struggling:
            energy = 'low'
            confidence = 'struggling'
        elif is_motivated:
            energy = 'high'
            confidence = 'confident'
        elif is_disengaged:
            energy = 'low'
            confidence = 'uncertain'
        else:
            energy = 'medium'
            confidence = 'uncertain'
        
        return UserPsychState(
            energy_level=energy,
            confidence=confidence,
            engagement=engagement,
            needs_encouragement=is_struggling or is_disengaged,
            needs_concrete_help=is_struggling or '?' in message,
            needs_space=is_disengaged and len(message) < 20
        )
    
    def get_or_create_active_goal(self, user_id: int, goal_hint: str = None) -> Optional[GoalContext]:
        """Get user's active goal (internal tracking only)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT g.id, g.goal_title, g.goal_description, g.status,
                   s.strategy_phase, s.current_step, s.next_action, s.last_user_input
            FROM user_goals g
            LEFT JOIN goal_strategies s ON g.id = s.goal_id
            WHERE g.user_id = ? AND g.status = 'active'
            ORDER BY g.priority DESC, g.updated_at DESC
            LIMIT 1
        ''', (user_id,))
        
        row = cursor.fetchone()
        
        if row:
            # Calculate days since last progress
            cursor.execute('''
                SELECT julianday('now') - julianday(updated_at) 
                FROM goal_strategies WHERE goal_id = ?
            ''', (row[0],))
            days_row = cursor.fetchone()
            days_since = int(days_row[0]) if days_row and days_row[0] else 0
            
            conn.close()
            return GoalContext(
                goal_id=row[0],
                title=row[1],
                description=row[2] or '',
                status=row[3],
                engagement_level='medium',
                user_mood='neutral',
                last_action_taken=row[6] or '',
                days_since_progress=days_since,
                blockers=[],
                wins=[]
            )
        
        conn.close()
        return None
    
    def create_goal(self, user_id: int, title: str, description: str = None, 
                   goal_type: str = 'general') -> int:
        """Create a new goal for the user"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_goals (user_id, goal_title, goal_description, goal_type)
            VALUES (?, ?, ?, ?)
        ''', (user_id, title, description, goal_type))
        
        goal_id = cursor.lastrowid
        
        # Initialize strategy in discovery phase
        cursor.execute('''
            INSERT INTO goal_strategies (goal_id, strategy_phase, current_step, next_question)
            VALUES (?, 'discovery', 1, ?)
        ''', (goal_id, f"What specifically do you want to achieve with {title}?"))
        
        conn.commit()
        conn.close()
        
        return goal_id
    
    def detect_goal_from_message(self, user_id: int, message: str) -> Optional[Dict]:
        """Use AI to detect if user is expressing a goal"""
        if not self.ai_call_func:
            return None
        
        try:
            response = self.ai_call_func(
                system_prompt="""You are a goal detection assistant. Analyze the user's message and determine if they are expressing a goal, aspiration, or something they want to achieve.

Return JSON in this exact format:
{
    "has_goal": true/false,
    "goal_title": "short title if goal detected",
    "goal_description": "detailed description",
    "goal_type": "career/health/learning/financial/relationship/personal/general",
    "urgency": "high/medium/low",
    "confidence": 0.0-1.0
}

Only return has_goal=true if the user clearly expresses wanting to achieve, improve, or accomplish something.""",
                user_message=f"Analyze this message for goals: {message}",
                purpose='goal_detection',
                character='coordinator'
            )
            
            if response and response.get('success'):
                # Parse JSON from response
                response_text = response.get('response', '{}')
                # Extract JSON from response
                import re
                json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
        except Exception as e:
            print(f"[GOAL] Error detecting goal: {e}")
        
        return None
    
    def generate_adaptive_guidance(self, user_id: int, user_message: str) -> Dict:
        """
        Generate natural, adaptive guidance based on user's current state.
        
        This is NOT formal coaching - it's helpful conversation that adapts to:
        - What the user actually needs RIGHT NOW
        - Their energy/mood/engagement level
        - Whether to push, support, or give space
        """
        # Detect user's current psychological state
        user_state = self.detect_user_state(user_message)
        goal_context = self.get_or_create_active_goal(user_id)
        
        # No goal yet - check if they're expressing one naturally
        if not goal_context:
            detected = self.detect_goal_from_message(user_id, user_message)
            if detected and detected.get('has_goal') and detected.get('confidence', 0) > 0.6:
                goal_id = self.create_goal(
                    user_id, 
                    detected.get('goal_title', 'New Goal'),
                    detected.get('goal_description'),
                    detected.get('goal_type', 'general')
                )
                goal_context = self.get_or_create_active_goal(user_id)
        
        if not goal_context:
            return {'has_guidance': False}
        
        # Track this interaction
        self._track_engagement(goal_context.goal_id, user_message, user_state)
        
        # Generate adaptive response based on user state
        guidance = self._generate_adaptive_response(goal_context, user_message, user_state)
        
        return {
            'has_guidance': True,
            'user_state': {
                'energy': user_state.energy_level,
                'engagement': user_state.engagement,
                'needs_encouragement': user_state.needs_encouragement,
                'needs_concrete_help': user_state.needs_concrete_help
            },
            **guidance
        }
    
    def _generate_adaptive_response(self, goal: GoalContext, user_input: str, 
                                    user_state: UserPsychState) -> Dict:
        """Generate response adapted to user's psychological state"""
        
        # Determine response strategy based on user state
        if user_state.needs_space:
            strategy = "gentle_check_in"
            tone = "Give space, light touch, no pressure"
        elif user_state.needs_encouragement:
            strategy = "supportive_boost"
            tone = "Warm, validating, celebrate any effort"
        elif user_state.needs_concrete_help:
            strategy = "specific_action"
            tone = "Clear, practical, ONE thing they can do TODAY"
        elif user_state.engagement == 'engaged':
            strategy = "momentum_builder"
            tone = "Energetic, build on their motivation, stretch them slightly"
        else:
            strategy = "curious_exploration"
            tone = "Curious, open questions, understand where they are"
        
        if not self.ai_call_func:
            return self._get_fallback_guidance(goal, user_state, strategy)
        
        try:
            response = self.ai_call_func(
                system_prompt=f"""You are having a natural, helpful conversation with someone working toward: "{goal.title}"

CRITICAL RULES:
1. DO NOT sound like a formal coach or program
2. Be conversational, warm, like a supportive friend
3. Give ONE specific thing they can do TODAY (not vague advice)
4. Adapt to their current mood and energy

USER'S CURRENT STATE:
- Energy: {user_state.energy_level}
- Confidence: {user_state.confidence}  
- Engagement: {user_state.engagement}

RESPONSE STRATEGY: {strategy}
TONE: {tone}

{"They seem disengaged - don't push, just check in warmly." if user_state.needs_space else ""}
{"They're struggling - validate first, then offer concrete help." if user_state.needs_encouragement else ""}
{"They need specific guidance - give them ONE clear action." if user_state.needs_concrete_help else ""}
{"They're motivated - match their energy and help them channel it." if user_state.engagement == 'engaged' else ""}

Days since last progress: {goal.days_since_progress}
Last action: {goal.last_action_taken or 'None recorded'}

Respond naturally. End with either:
- A specific action suggestion (if they need direction)
- A gentle check-in question (if they need space)
- Encouragement to keep going (if they're making progress)

DO NOT use formal coaching language. Sound human.""",
                user_message=user_input,
                purpose='adaptive_guidance',
                character='coordinator'
            )
            
            if response and response.get('success'):
                return {
                    'response_text': response.get('response', ''),
                    'strategy_used': strategy,
                    'immediate_action': self._extract_action(response.get('response', ''))
                }
        except Exception as e:
            print(f"[COACHING] Adaptive response error: {e}")
        
        return self._get_fallback_guidance(goal, user_state, strategy)
    
    def _get_fallback_guidance(self, goal: GoalContext, user_state: UserPsychState, 
                               strategy: str) -> Dict:
        """Fallback guidance when AI is unavailable"""
        
        if strategy == "gentle_check_in":
            text = f"No rush at all. Whenever you're ready to chat about {goal.title}, I'm here. 😊"
        elif strategy == "supportive_boost":
            text = f"Hey, I know {goal.title} can feel overwhelming sometimes. Even thinking about it counts as progress. What's one tiny thing you could do in the next 5 minutes?"
        elif strategy == "specific_action":
            text = f"Here's something specific: spend just 10 minutes today on {goal.title}. Set a timer, do one small thing, then stop. That's it. What would that one thing be?"
        elif strategy == "momentum_builder":
            text = f"Love the energy! Let's channel it - what's the ONE thing that would make the biggest difference for {goal.title} right now?"
        else:
            text = f"I'm curious - what's on your mind about {goal.title} today?"
        
        return {
            'response_text': text,
            'strategy_used': strategy,
            'immediate_action': None
        }
    
    def _extract_action(self, response_text: str) -> Optional[str]:
        """Extract specific action item from response"""
        action_indicators = ['try ', 'could ', 'spend ', 'take ', 'start ', 'do ', 'make ']
        sentences = response_text.split('.')
        
        for sentence in sentences:
            sentence_lower = sentence.lower().strip()
            if any(indicator in sentence_lower for indicator in action_indicators):
                if len(sentence) > 20 and len(sentence) < 150:
                    return sentence.strip()
        return None
    
    def _track_engagement(self, goal_id: int, user_input: str, user_state: UserPsychState):
        """Track user engagement for adaptive learning"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Update strategy with engagement data
        cursor.execute('''
            UPDATE goal_strategies 
            SET last_user_input = ?, updated_at = CURRENT_TIMESTAMP
            WHERE goal_id = ?
        ''', (user_input[:500], goal_id))
        
        conn.commit()
        conn.close()
    
    def _update_strategy(self, goal_id: int, user_input: str):
        """Update goal strategy based on user input"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get current strategy
        cursor.execute('''
            SELECT strategy_phase, current_step FROM goal_strategies WHERE goal_id = ?
        ''', (goal_id,))
        row = cursor.fetchone()
        
        if row:
            phase, step = row
            new_step = step + 1
            
            # Phase progression logic
            if new_step > 5:  # Move to next phase after 5 interactions
                phase_order = ['discovery', 'planning', 'execution', 'validation', 'completion']
                current_idx = phase_order.index(phase) if phase in phase_order else 0
                if current_idx < len(phase_order) - 1:
                    phase = phase_order[current_idx + 1]
                    new_step = 1
            
            cursor.execute('''
                UPDATE goal_strategies 
                SET current_step = ?, strategy_phase = ?, last_user_input = ?, updated_at = CURRENT_TIMESTAMP
                WHERE goal_id = ?
            ''', (new_step, phase, user_input[:500], goal_id))
        
        conn.commit()
        conn.close()
    
    def _get_goal_milestones(self, goal_id: int) -> List[Dict]:
        """Get milestones for a goal"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, milestone_title, status, completed_at
            FROM goal_milestones
            WHERE goal_id = ?
            ORDER BY sequence_order
        ''', (goal_id,))
        
        milestones = [
            {'id': r[0], 'title': r[1], 'status': r[2], 'completed': r[3] is not None}
            for r in cursor.fetchall()
        ]
        
        conn.close()
        return milestones
    
    def _calculate_progress(self, goal_id: int) -> float:
        """Calculate goal progress percentage"""
        milestones = self._get_goal_milestones(goal_id)
        if not milestones:
            # Use strategy phase for progress
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT strategy_phase FROM goal_strategies WHERE goal_id = ?', (goal_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                phases = {'discovery': 10, 'planning': 30, 'execution': 60, 'validation': 80, 'completion': 100}
                return phases.get(row[0], 10)
            return 10
        
        completed = sum(1 for m in milestones if m['completed'])
        return (completed / len(milestones)) * 100
    
    def schedule_followup(self, user_id: int, goal_id: int, question: str, 
                         delay_hours: int = 24) -> int:
        """Schedule a follow-up question for later"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        scheduled_time = datetime.now() + timedelta(hours=delay_hours)
        
        cursor.execute('''
            INSERT INTO goal_followups 
            (goal_id, user_id, followup_question, scheduled_for)
            VALUES (?, ?, ?, ?)
        ''', (goal_id, user_id, question, scheduled_time))
        
        followup_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return followup_id
    
    def get_pending_followups(self, user_id: int) -> List[Dict]:
        """Get pending follow-ups that are due"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT f.id, f.goal_id, f.followup_question, g.goal_title
            FROM goal_followups f
            JOIN user_goals g ON f.goal_id = g.id
            WHERE f.user_id = ? 
              AND f.sent_at IS NULL 
              AND f.scheduled_for <= CURRENT_TIMESTAMP
            ORDER BY f.scheduled_for
        ''', (user_id,))
        
        followups = [
            {'id': r[0], 'goal_id': r[1], 'question': r[2], 'goal_title': r[3]}
            for r in cursor.fetchall()
        ]
        
        conn.close()
        return followups
    
    def mark_followup_sent(self, followup_id: int):
        """Mark a follow-up as sent"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE goal_followups SET sent_at = CURRENT_TIMESTAMP WHERE id = ?
        ''', (followup_id,))
        conn.commit()
        conn.close()
    
    def get_coaching_context_for_prompt(self, user_id: int, user_message: str = "") -> Optional[str]:
        """
        Get invisible coaching context for AI prompts.
        
        This guides the AI to be helpful without being formal or rigid.
        The user should never feel like they're in a "coaching program".
        """
        goal = self.get_or_create_active_goal(user_id)
        if not goal:
            return None
        
        # Detect user state if message provided
        user_state = self.detect_user_state(user_message) if user_message else None
        
        # Determine approach based on user state
        if user_state:
            if user_state.needs_space:
                approach = "Be gentle, no pressure. Just check in warmly."
            elif user_state.needs_encouragement:
                approach = "Validate their feelings first. Then offer ONE small, easy action."
            elif user_state.needs_concrete_help:
                approach = "Give ONE specific thing they can do TODAY. Be practical, not philosophical."
            elif user_state.engagement == 'engaged':
                approach = "Match their energy! Help them channel it into immediate action."
            else:
                approach = "Be curious and warm. Ask about what's on their mind."
        else:
            approach = "Be helpful and conversational. Give specific, not generic, guidance."
        
        # Build context that guides AI naturally
        context = f"""
BEHIND-THE-SCENES CONTEXT (invisible to user):
The user is working toward: "{goal.title}"
Days since last engagement: {goal.days_since_progress}
Last discussed: {goal.last_action_taken or 'Nothing specific yet'}

YOUR APPROACH: {approach}

CRITICAL GUIDELINES:
- Sound like a helpful friend, NOT a formal coach
- Give ONE specific action they can do TODAY (not vague advice like "stay positive")
- If they share progress, celebrate it genuinely
- If they're stuck, acknowledge it's hard, then offer concrete help
- End with something that invites continued conversation (question OR action suggestion)
- NEVER use formal coaching language or numbered steps
- Adapt to their energy - if they're tired, don't push; if they're motivated, channel it
"""
        return context


def create_goal_coaching_system(db, ai_call_func=None) -> GoalCoachingSystem:
    """Factory function to create GoalCoachingSystem instance"""
    return GoalCoachingSystem(db, ai_call_func)

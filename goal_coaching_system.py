"""
Goal Coaching System - Proactive strategy-driven user engagement

This system transforms passive Q&A into active coaching by:
1. Tracking user goals and strategies behind the scenes
2. Generating follow-up questions to keep users engaged
3. Providing continuous guidance and actionable advice
4. Integrating with auto bot context prompts for holistic engagement
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass


@dataclass
class GoalContext:
    """Context for a user's active goal"""
    goal_id: int
    title: str
    description: str
    status: str
    strategy_phase: str
    current_step: int
    next_action: str
    next_question: str
    milestones: List[Dict]
    progress_percentage: float


class GoalCoachingSystem:
    """
    Proactive goal coaching that maintains strategy and pushes users toward achievement.
    
    Strategy Phases:
    1. discovery - Understanding the goal and user's situation
    2. planning - Creating actionable steps and milestones
    3. execution - Guiding through action steps with follow-ups
    4. validation - Checking progress and adjusting strategy
    5. completion - Celebrating achievements and setting next goals
    """
    
    def __init__(self, db, ai_call_func: Callable = None):
        self.db = db
        self.ai_call_func = ai_call_func
        
        # Phase-specific question templates
        self.phase_questions = {
            'discovery': [
                "What specifically do you want to achieve with {goal}?",
                "What's driving you to pursue this goal right now?",
                "What obstacles have you faced before when trying this?",
                "On a scale of 1-10, how committed are you to this goal?",
                "What does success look like to you?"
            ],
            'planning': [
                "What's the first small step you could take this week?",
                "Who else might be able to help you with this?",
                "What resources do you already have available?",
                "What's a realistic timeline for your first milestone?",
                "How will you track your progress?"
            ],
            'execution': [
                "How did your last action step go?",
                "What's blocking you from taking the next step?",
                "What support do you need right now?",
                "Have you encountered any unexpected challenges?",
                "What's working well so far?"
            ],
            'validation': [
                "Are you still on track with your original goal?",
                "Do we need to adjust the strategy?",
                "What have you learned so far?",
                "Is the current pace sustainable for you?",
                "Any wins to celebrate, even small ones?"
            ]
        }
    
    def get_or_create_active_goal(self, user_id: int, goal_hint: str = None) -> Optional[GoalContext]:
        """Get user's active goal or detect one from conversation"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check for existing active goal
        cursor.execute('''
            SELECT g.id, g.goal_title, g.goal_description, g.status,
                   s.strategy_phase, s.current_step, s.next_action, s.next_question
            FROM user_goals g
            LEFT JOIN goal_strategies s ON g.id = s.goal_id
            WHERE g.user_id = ? AND g.status = 'active'
            ORDER BY g.priority DESC, g.updated_at DESC
            LIMIT 1
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return GoalContext(
                goal_id=row[0],
                title=row[1],
                description=row[2] or '',
                status=row[3],
                strategy_phase=row[4] or 'discovery',
                current_step=row[5] or 1,
                next_action=row[6] or '',
                next_question=row[7] or '',
                milestones=self._get_goal_milestones(row[0]),
                progress_percentage=self._calculate_progress(row[0])
            )
        
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
    
    def generate_coaching_response(self, user_id: int, user_message: str, 
                                   goal_context: GoalContext = None) -> Dict:
        """Generate a coaching-style response with follow-up questions"""
        if not goal_context:
            goal_context = self.get_or_create_active_goal(user_id)
        
        if not goal_context:
            # No active goal - check if user is expressing one
            detected = self.detect_goal_from_message(user_id, user_message)
            if detected and detected.get('has_goal') and detected.get('confidence', 0) > 0.6:
                # Create the goal
                goal_id = self.create_goal(
                    user_id, 
                    detected.get('goal_title', 'New Goal'),
                    detected.get('goal_description'),
                    detected.get('goal_type', 'general')
                )
                goal_context = self.get_or_create_active_goal(user_id)
        
        if not goal_context:
            return {
                'has_coaching': False,
                'coaching_context': None
            }
        
        # Update strategy based on user input
        self._update_strategy(goal_context.goal_id, user_message)
        
        # Generate next question and guidance
        coaching = self._generate_next_coaching_step(goal_context, user_message)
        
        return {
            'has_coaching': True,
            'goal_title': goal_context.title,
            'strategy_phase': goal_context.strategy_phase,
            'progress': goal_context.progress_percentage,
            'next_question': coaching.get('next_question'),
            'guidance': coaching.get('guidance'),
            'action_items': coaching.get('action_items', []),
            'coaching_context': coaching
        }
    
    def _generate_next_coaching_step(self, goal: GoalContext, user_input: str) -> Dict:
        """Generate the next coaching step with AI"""
        if not self.ai_call_func:
            # Fallback to template-based questions
            phase_qs = self.phase_questions.get(goal.strategy_phase, self.phase_questions['discovery'])
            step_idx = min(goal.current_step - 1, len(phase_qs) - 1)
            return {
                'next_question': phase_qs[step_idx].format(goal=goal.title),
                'guidance': f"Let's work on your goal: {goal.title}",
                'action_items': []
            }
        
        try:
            response = self.ai_call_func(
                system_prompt=f"""You are a proactive goal coach helping the user achieve: "{goal.title}"

Current Phase: {goal.strategy_phase}
Progress: {goal.progress_percentage}%
Next Action: {goal.next_action or 'To be determined'}

Your role is to:
1. Acknowledge what the user shared
2. Provide specific, actionable guidance
3. Ask ONE focused follow-up question to keep momentum
4. End with encouragement

Keep responses concise but warm. Focus on the next immediate step.

Return your response in this JSON format:
{{
    "acknowledgment": "brief acknowledgment of user's input",
    "guidance": "specific advice or instruction (2-3 sentences)",
    "next_question": "one focused follow-up question",
    "action_items": ["specific action 1", "specific action 2"],
    "encouragement": "brief motivating message"
}}""",
                user_message=f"User said: {user_input}\n\nGenerate the next coaching step.",
                purpose='goal_coaching',
                character='coordinator'
            )
            
            if response and response.get('success'):
                import re
                response_text = response.get('response', '{}')
                json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
        except Exception as e:
            print(f"[COACHING] Error generating step: {e}")
        
        return {
            'next_question': f"What's your next step toward {goal.title}?",
            'guidance': "Let's keep moving forward with your goal.",
            'action_items': []
        }
    
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
    
    def get_coaching_context_for_prompt(self, user_id: int) -> Optional[str]:
        """Get coaching context to inject into AI prompts"""
        goal = self.get_or_create_active_goal(user_id)
        if not goal:
            return None
        
        context = f"""
ACTIVE GOAL COACHING CONTEXT:
- Goal: {goal.title}
- Phase: {goal.strategy_phase}
- Progress: {goal.progress_percentage:.0f}%
- Next focus: {goal.next_action or 'Continue discovery'}

COACHING INSTRUCTIONS:
1. Always end your response with a follow-up question related to their goal
2. Provide specific, actionable guidance (not just generic advice)
3. Track progress and celebrate small wins
4. Keep the user engaged and moving forward
"""
        return context


def create_goal_coaching_system(db, ai_call_func=None) -> GoalCoachingSystem:
    """Factory function to create GoalCoachingSystem instance"""
    return GoalCoachingSystem(db, ai_call_func)

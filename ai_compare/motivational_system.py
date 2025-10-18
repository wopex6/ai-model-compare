"""
Motivational System for AI Chatbot
Handles activity tracking, reminders, progress monitoring, and motivational content
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json
import random

class ActivityStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    PAUSED = "paused"

class MotivationLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    SUPER_HIGH = "super_high"

class ReminderType(Enum):
    GENTLE = "gentle"
    ENCOURAGING = "encouraging"
    URGENT = "urgent"
    CELEBRATORY = "celebratory"

@dataclass
class Goal:
    """User goal with tracking capabilities"""
    id: str
    title: str
    description: str
    category: str
    target_date: datetime
    created_date: datetime
    status: ActivityStatus = ActivityStatus.NOT_STARTED
    progress_percentage: float = 0.0
    milestones: List[str] = field(default_factory=list)
    completed_milestones: List[str] = field(default_factory=list)
    priority: str = "medium"  # low, medium, high, critical
    estimated_duration: int = 60  # minutes
    tags: List[str] = field(default_factory=list)

@dataclass
class Activity:
    """Scheduled activity or task"""
    id: str
    title: str
    description: str
    scheduled_time: datetime
    duration: int  # minutes
    category: str
    status: ActivityStatus = ActivityStatus.NOT_STARTED
    reminders_sent: List[datetime] = field(default_factory=list)
    completion_time: Optional[datetime] = None
    notes: str = ""
    related_goal_id: Optional[str] = None

@dataclass
class ProgressFeedback:
    """User feedback on progress and motivation"""
    timestamp: datetime
    goal_id: str
    progress_rating: int  # 1-10 scale
    motivation_level: MotivationLevel
    challenges: List[str]
    achievements: List[str]
    feedback_text: str
    suggested_adjustments: List[str] = field(default_factory=list)

@dataclass
class MotivationalContent:
    """Motivational quotes, tips, and content"""
    content_type: str  # quote, tip, story, challenge
    text: str
    category: str
    mood_boost: int  # 1-10 scale
    tags: List[str] = field(default_factory=list)

class MotivationalSystem:
    """Core motivational system with activity tracking and time awareness"""
    
    def __init__(self):
        self.goals: Dict[str, Goal] = {}
        self.activities: Dict[str, Activity] = {}
        self.progress_history: List[ProgressFeedback] = []
        self.user_preferences = {
            "reminder_frequency": 30,  # minutes before activity
            "motivation_style": "energetic",  # gentle, energetic, tough_love
            "preferred_times": ["09:00", "13:00", "17:00"],  # check-in times
            "goal_categories": ["work", "health", "learning", "personal"],
            "celebration_style": "enthusiastic"
        }
        self.motivational_content = self._load_motivational_content()
        self.current_streak = 0
        self.total_achievements = 0
    
    def add_goal(self, title: str, description: str, category: str, target_date: datetime, 
                 milestones: List[str] = None, priority: str = "medium") -> str:
        """Add a new goal to track"""
        goal_id = f"goal_{len(self.goals) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        goal = Goal(
            id=goal_id,
            title=title,
            description=description,
            category=category,
            target_date=target_date,
            created_date=datetime.now(),
            milestones=milestones or [],
            priority=priority
        )
        
        self.goals[goal_id] = goal
        return goal_id
    
    def schedule_activity(self, title: str, description: str, scheduled_time: datetime,
                         duration: int, category: str, related_goal_id: str = None) -> str:
        """Schedule a new activity"""
        activity_id = f"activity_{len(self.activities) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        activity = Activity(
            id=activity_id,
            title=title,
            description=description,
            scheduled_time=scheduled_time,
            duration=duration,
            category=category,
            related_goal_id=related_goal_id
        )
        
        self.activities[activity_id] = activity
        return activity_id
    
    def update_progress(self, goal_id: str, progress_percentage: float, 
                       completed_milestones: List[str] = None) -> bool:
        """Update goal progress"""
        if goal_id not in self.goals:
            return False
        
        goal = self.goals[goal_id]
        old_progress = goal.progress_percentage
        goal.progress_percentage = min(100.0, max(0.0, progress_percentage))
        
        if completed_milestones:
            goal.completed_milestones.extend(completed_milestones)
        
        # Update status based on progress
        if goal.progress_percentage == 100.0:
            goal.status = ActivityStatus.COMPLETED
            self.total_achievements += 1
        elif goal.progress_percentage > 0:
            goal.status = ActivityStatus.IN_PROGRESS
        
        # Check if significant progress was made
        if goal.progress_percentage - old_progress >= 25:
            self.current_streak += 1
        
        return True
    
    def record_feedback(self, goal_id: str, progress_rating: int, motivation_level: MotivationLevel,
                       challenges: List[str], achievements: List[str], feedback_text: str) -> None:
        """Record user feedback on progress"""
        feedback = ProgressFeedback(
            timestamp=datetime.now(),
            goal_id=goal_id,
            progress_rating=progress_rating,
            motivation_level=motivation_level,
            challenges=challenges,
            achievements=achievements,
            feedback_text=feedback_text
        )
        
        self.progress_history.append(feedback)
        
        # Adjust motivation approach based on feedback
        self._adjust_motivation_approach(feedback)
    
    def get_pending_reminders(self) -> List[Tuple[Activity, ReminderType]]:
        """Get activities that need reminders"""
        now = datetime.now()
        reminders = []
        
        for activity in self.activities.values():
            if activity.status in [ActivityStatus.NOT_STARTED, ActivityStatus.IN_PROGRESS]:
                time_until = (activity.scheduled_time - now).total_seconds() / 60
                
                # Check if reminder is needed
                if 0 <= time_until <= self.user_preferences["reminder_frequency"]:
                    if not activity.reminders_sent or \
                       (now - activity.reminders_sent[-1]).total_seconds() > 900:  # 15 min cooldown
                        
                        # Determine reminder type based on urgency
                        if time_until <= 5:
                            reminder_type = ReminderType.URGENT
                        elif time_until <= 15:
                            reminder_type = ReminderType.ENCOURAGING
                        else:
                            reminder_type = ReminderType.GENTLE
                        
                        reminders.append((activity, reminder_type))
        
        return reminders
    
    def get_overdue_activities(self) -> List[Activity]:
        """Get activities that are overdue"""
        now = datetime.now()
        overdue = []
        
        for activity in self.activities.values():
            if activity.status != ActivityStatus.COMPLETED and activity.scheduled_time < now:
                activity.status = ActivityStatus.OVERDUE
                overdue.append(activity)
        
        return overdue
    
    def generate_motivational_message(self, context: str = "general") -> str:
        """Generate contextual motivational message"""
        user_motivation = self._assess_current_motivation()
        style = self.user_preferences["motivation_style"]
        
        # Get recent progress
        recent_feedback = self.progress_history[-3:] if self.progress_history else []
        avg_motivation = sum(f.motivation_level.value for f in recent_feedback) / len(recent_feedback) if recent_feedback else "medium"
        
        messages = self._get_motivational_messages(context, style, user_motivation)
        base_message = random.choice(messages)
        
        # Personalize with user data
        personalized = self._personalize_message(base_message, context)
        
        return personalized
    
    def get_progress_summary(self) -> Dict:
        """Get comprehensive progress summary"""
        completed_goals = sum(1 for g in self.goals.values() if g.status == ActivityStatus.COMPLETED)
        total_goals = len(self.goals)
        
        completed_activities = sum(1 for a in self.activities.values() if a.status == ActivityStatus.COMPLETED)
        total_activities = len(self.activities)
        
        # Calculate average progress
        avg_progress = sum(g.progress_percentage for g in self.goals.values()) / total_goals if total_goals > 0 else 0
        
        return {
            "goals": {
                "total": total_goals,
                "completed": completed_goals,
                "completion_rate": (completed_goals / total_goals * 100) if total_goals > 0 else 0,
                "average_progress": avg_progress
            },
            "activities": {
                "total": total_activities,
                "completed": completed_activities,
                "completion_rate": (completed_activities / total_activities * 100) if total_activities > 0 else 0
            },
            "streak": self.current_streak,
            "total_achievements": self.total_achievements,
            "motivation_trend": self._get_motivation_trend()
        }
    
    def get_upcoming_activities(self, hours_ahead: int = 24) -> List[Activity]:
        """Get activities scheduled in the next X hours"""
        now = datetime.now()
        cutoff = now + timedelta(hours=hours_ahead)
        
        upcoming = [
            activity for activity in self.activities.values()
            if now <= activity.scheduled_time <= cutoff and 
            activity.status != ActivityStatus.COMPLETED
        ]
        
        return sorted(upcoming, key=lambda a: a.scheduled_time)
    
    def _assess_current_motivation(self) -> MotivationLevel:
        """Assess user's current motivation level"""
        if not self.progress_history:
            return MotivationLevel.MEDIUM
        
        recent_feedback = self.progress_history[-3:]
        avg_rating = sum(f.progress_rating for f in recent_feedback) / len(recent_feedback)
        
        if avg_rating >= 8:
            return MotivationLevel.SUPER_HIGH
        elif avg_rating >= 6:
            return MotivationLevel.HIGH
        elif avg_rating >= 4:
            return MotivationLevel.MEDIUM
        else:
            return MotivationLevel.LOW
    
    def _adjust_motivation_approach(self, feedback: ProgressFeedback) -> None:
        """Adjust motivation approach based on user feedback"""
        if feedback.motivation_level == MotivationLevel.LOW:
            if "overwhelmed" in feedback.challenges:
                self.user_preferences["motivation_style"] = "gentle"
            elif "bored" in feedback.challenges:
                self.user_preferences["motivation_style"] = "energetic"
        elif feedback.motivation_level == MotivationLevel.SUPER_HIGH:
            self.user_preferences["motivation_style"] = "energetic"
    
    def _personalize_message(self, message: str, context: str) -> str:
        """Personalize motivational message with user data"""
        # Replace placeholders with actual data
        replacements = {
            "{streak}": str(self.current_streak),
            "{achievements}": str(self.total_achievements),
            "{progress}": f"{self.get_progress_summary()['goals']['average_progress']:.1f}%"
        }
        
        for placeholder, value in replacements.items():
            message = message.replace(placeholder, value)
        
        return message
    
    def _get_motivational_messages(self, context: str, style: str, motivation_level: MotivationLevel) -> List[str]:
        """Get appropriate motivational messages"""
        messages = {
            "gentle": [
                "You're doing great! Every small step counts. 🌟",
                "Progress is progress, no matter how small. Keep going! 💪",
                "Remember, you've got this! Take it one step at a time. ✨"
            ],
            "energetic": [
                "LET'S GO! You're absolutely crushing it! 🚀",
                "BOOM! Another step closer to your dreams! Keep that energy! ⚡",
                "You're on FIRE! {streak} day streak and counting! 🔥"
            ],
            "tough_love": [
                "No excuses! You committed to this goal - time to deliver! 💯",
                "Champions don't make excuses, they make progress! Get moving! 🏆",
                "Your future self is counting on you RIGHT NOW! Don't let them down! ⏰"
            ]
        }
        
        return messages.get(style, messages["energetic"])
    
    def _get_motivation_trend(self) -> str:
        """Analyze motivation trend over time"""
        if len(self.progress_history) < 2:
            return "stable"
        
        recent = self.progress_history[-3:]
        older = self.progress_history[-6:-3] if len(self.progress_history) >= 6 else []
        
        if not older:
            return "stable"
        
        recent_avg = sum(f.progress_rating for f in recent) / len(recent)
        older_avg = sum(f.progress_rating for f in older) / len(older)
        
        if recent_avg > older_avg + 1:
            return "improving"
        elif recent_avg < older_avg - 1:
            return "declining"
        else:
            return "stable"
    
    def _load_motivational_content(self) -> List[MotivationalContent]:
        """Load motivational quotes, tips, and content"""
        return [
            MotivationalContent("quote", "The only way to do great work is to love what you do. - Steve Jobs", "inspiration", 8),
            MotivationalContent("quote", "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill", "perseverance", 9),
            MotivationalContent("tip", "Break large goals into smaller, manageable tasks. Celebrate each small win!", "productivity", 7),
            MotivationalContent("tip", "Use the 2-minute rule: if something takes less than 2 minutes, do it now!", "productivity", 6),
            MotivationalContent("challenge", "Try the Pomodoro Technique: 25 minutes focused work, 5 minute break!", "productivity", 8),
            MotivationalContent("story", "Every expert was once a beginner. Every pro was once an amateur. Every icon was once an unknown.", "growth", 9)
        ]

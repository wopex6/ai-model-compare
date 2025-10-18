"""
Motivational Chatbot Integration
Combines the chatbot system with motivational coaching capabilities
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json

from .chatbot import AIChatbot
from .motivational_system import MotivationalSystem, ActivityStatus, MotivationLevel, ReminderType
from .chatbot_personality import PERSONALITY_PRESETS

class MotivationalChatbot(AIChatbot):
    """Enhanced chatbot with motivational coaching and time awareness"""
    
    def __init__(self, personality_preset: str = "super_motivational_coach", user_preset: str = "casual_learner"):
        super().__init__(personality_preset, user_preset)
        self.motivational_system = MotivationalSystem()
        self.last_check_in = datetime.now()
        self.reminder_active = True
        
    async def chat(self, user_message: str, include_context: bool = True) -> Dict[str, any]:
        """Enhanced chat with motivational features"""
        # Check for motivational commands first
        if await self._handle_motivational_commands(user_message):
            return await self._get_last_response()
        
        # Check for time-sensitive reminders
        await self._check_reminders()
        
        # Process normal chat with motivational context
        enhanced_message = await self._enhance_with_motivational_context(user_message)
        
        # Get base response
        response_data = await super().chat(enhanced_message, include_context)
        
        # Add motivational enhancements
        response_data = await self._add_motivational_enhancements(response_data, user_message)
        
        return response_data
    
    async def _handle_motivational_commands(self, message: str) -> bool:
        """Handle specific motivational commands"""
        message_lower = message.lower().strip()
        
        # Goal management commands
        if message_lower.startswith("add goal"):
            await self._handle_add_goal(message)
            return True
        elif message_lower.startswith("schedule activity"):
            await self._handle_schedule_activity(message)
            return True
        elif message_lower.startswith("update progress"):
            await self._handle_update_progress(message)
            return True
        elif message_lower.startswith("give feedback"):
            await self._handle_give_feedback(message)
            return True
        elif message_lower in ["show progress", "my progress", "progress report"]:
            await self._handle_show_progress()
            return True
        elif message_lower in ["upcoming activities", "what's next", "schedule"]:
            await self._handle_show_upcoming()
            return True
        elif message_lower in ["motivate me", "need motivation", "inspire me"]:
            await self._handle_motivation_request()
            return True
        
        return False
    
    async def _handle_add_goal(self, message: str):
        """Handle adding a new goal"""
        # Simple parsing - in production, use NLP
        parts = message.split('"')
        if len(parts) >= 3:
            title = parts[1]
            description = parts[3] if len(parts) >= 4 else title
            
            # Default to 30 days from now
            target_date = datetime.now() + timedelta(days=30)
            
            goal_id = self.motivational_system.add_goal(
                title=title,
                description=description,
                category="general",
                target_date=target_date
            )
            
            self.last_response = {
                "response": f"🎯 AMAZING! I've added your goal: '{title}'! This is going to be EPIC! 🚀\n\nI'll help you stay on track and celebrate every milestone. You've got this, champion! 💪\n\nGoal ID: {goal_id}",
                "character": self.personality.traits.character,
                "mood": self.personality.traits.mood.value,
                "motivational_action": "goal_added"
            }
        else:
            self.last_response = {
                "response": "Let's set up that goal! 🎯 Use this format: add goal \"Your Goal Title\" \"Description\"\n\nFor example: add goal \"Learn Python\" \"Master Python programming in 3 months\"\n\nI'm here to help you CRUSH your goals! 💪",
                "character": self.personality.traits.character,
                "mood": self.personality.traits.mood.value
            }
    
    async def _handle_schedule_activity(self, message: str):
        """Handle scheduling an activity"""
        # Simple parsing for demo
        parts = message.split('"')
        if len(parts) >= 3:
            title = parts[1]
            # Default to 1 hour from now
            scheduled_time = datetime.now() + timedelta(hours=1)
            
            activity_id = self.motivational_system.schedule_activity(
                title=title,
                description=title,
                scheduled_time=scheduled_time,
                duration=60,
                category="general"
            )
            
            self.last_response = {
                "response": f"⏰ BOOM! Activity scheduled: '{title}' 🎉\n\nI've set it for {scheduled_time.strftime('%I:%M %p')} - that's in about an hour! I'll remind you when it's time to SHINE! ✨\n\nActivity ID: {activity_id}",
                "character": self.personality.traits.character,
                "mood": self.personality.traits.mood.value,
                "motivational_action": "activity_scheduled"
            }
        else:
            self.last_response = {
                "response": "Let's schedule that activity! ⏰ Use: schedule activity \"Activity Name\"\n\nExample: schedule activity \"Gym workout\"\n\nI'll make sure you never miss a beat! 🎵💪",
                "character": self.personality.traits.character,
                "mood": self.personality.traits.mood.value
            }
    
    async def _handle_update_progress(self, message: str):
        """Handle progress updates"""
        # Extract goal ID and progress percentage
        words = message.split()
        goal_id = None
        progress = None
        
        for i, word in enumerate(words):
            if word.startswith("goal_"):
                goal_id = word
            elif word.endswith("%"):
                try:
                    progress = float(word.replace("%", ""))
                except ValueError:
                    pass
        
        if goal_id and progress is not None:
            success = self.motivational_system.update_progress(goal_id, progress)
            if success:
                celebration = self._get_celebration_message(progress)
                self.last_response = {
                    "response": f"{celebration}\n\nProgress updated to {progress}%! {self._get_progress_encouragement(progress)}",
                    "character": self.personality.traits.character,
                    "mood": self.personality.traits.mood.value,
                    "motivational_action": "progress_updated"
                }
            else:
                self.last_response = {
                    "response": "Hmm, I couldn't find that goal. Use 'show progress' to see your active goals! 🎯",
                    "character": self.personality.traits.character,
                    "mood": self.personality.traits.mood.value
                }
        else:
            self.last_response = {
                "response": "Let's update your progress! 📈 Use: update progress goal_[ID] [percentage]%\n\nExample: update progress goal_1 75%\n\nI can't wait to celebrate your wins! 🎉",
                "character": self.personality.traits.character,
                "mood": self.personality.traits.mood.value
            }
    
    async def _handle_show_progress(self):
        """Show comprehensive progress report"""
        summary = self.motivational_system.get_progress_summary()
        
        progress_report = f"""🏆 YOUR AMAZING PROGRESS REPORT! 🏆

📊 GOALS STATUS:
• Total Goals: {summary['goals']['total']}
• Completed: {summary['goals']['completed']} 
• Success Rate: {summary['goals']['completion_rate']:.1f}%
• Average Progress: {summary['goals']['average_progress']:.1f}%

⚡ ACTIVITIES:
• Total Activities: {summary['activities']['total']}
• Completed: {summary['activities']['completed']}
• Completion Rate: {summary['activities']['completion_rate']:.1f}%

🔥 STREAK & ACHIEVEMENTS:
• Current Streak: {summary['streak']} days
• Total Achievements: {summary['total_achievements']}
• Motivation Trend: {summary['motivation_trend'].upper()}

{self._get_streak_message(summary['streak'])}"""

        self.last_response = {
            "response": progress_report,
            "character": self.personality.traits.character,
            "mood": self.personality.traits.mood.value,
            "motivational_action": "progress_shown",
            "progress_data": summary
        }
    
    async def _handle_show_upcoming(self):
        """Show upcoming activities"""
        upcoming = self.motivational_system.get_upcoming_activities(24)
        
        if not upcoming:
            self.last_response = {
                "response": "Your schedule is clear for the next 24 hours! 🌟\n\nThis is a perfect time to plan something AMAZING! What goal would you like to work on? 🚀",
                "character": self.personality.traits.character,
                "mood": self.personality.traits.mood.value
            }
        else:
            activities_text = "⏰ YOUR UPCOMING ADVENTURES! ⏰\n\n"
            for activity in upcoming[:5]:  # Show max 5
                time_str = activity.scheduled_time.strftime("%I:%M %p")
                activities_text += f"🎯 {activity.title}\n   📅 {time_str} ({activity.duration} min)\n   📝 {activity.description}\n\n"
            
            activities_text += "You're going to CRUSH these! I'll remind you when it's time! 💪✨"
            
            self.last_response = {
                "response": activities_text,
                "character": self.personality.traits.character,
                "mood": self.personality.traits.mood.value,
                "upcoming_count": len(upcoming)
            }
    
    async def _handle_motivation_request(self):
        """Handle direct motivation requests"""
        motivation_msg = self.motivational_system.generate_motivational_message("boost")
        
        # Add extra enthusiasm for Max
        if self.personality.traits.character == "Max":
            motivation_msg = f"🚀 {motivation_msg} 🚀\n\nYou're UNSTOPPABLE! Every champion was once a beginner who refused to give up! TODAY IS YOUR DAY! 💪⚡🔥"
        
        self.last_response = {
            "response": motivation_msg,
            "character": self.personality.traits.character,
            "mood": self.personality.traits.mood.value,
            "motivational_action": "motivation_delivered"
        }
    
    async def _check_reminders(self):
        """Check and send time-based reminders"""
        if not self.reminder_active:
            return
        
        pending_reminders = self.motivational_system.get_pending_reminders()
        overdue_activities = self.motivational_system.get_overdue_activities()
        
        # Handle reminders (in a real app, these would be sent as notifications)
        for activity, reminder_type in pending_reminders:
            await self._send_reminder(activity, reminder_type)
        
        # Handle overdue activities
        for activity in overdue_activities:
            await self._send_overdue_notice(activity)
    
    async def _send_reminder(self, activity, reminder_type: ReminderType):
        """Send activity reminder"""
        time_until = (activity.scheduled_time - datetime.now()).total_seconds() / 60
        
        if reminder_type == ReminderType.URGENT:
            message = f"🚨 URGENT REMINDER! 🚨\n'{activity.title}' starts in {int(time_until)} minutes! Time to SHINE! ⚡"
        elif reminder_type == ReminderType.ENCOURAGING:
            message = f"⏰ Friendly reminder! '{activity.title}' is coming up in {int(time_until)} minutes! You've got this! 💪"
        else:
            message = f"🔔 Gentle reminder: '{activity.title}' is scheduled in {int(time_until)} minutes. Ready to make it happen? ✨"
        
        # Mark reminder as sent
        activity.reminders_sent.append(datetime.now())
    
    async def _enhance_with_motivational_context(self, message: str) -> str:
        """Add motivational context to user messages"""
        # Check if user seems demotivated
        demotivation_keywords = ["tired", "can't", "impossible", "give up", "too hard", "overwhelmed"]
        if any(keyword in message.lower() for keyword in demotivation_keywords):
            context = "\n\nIMPORTANT: The user seems to be struggling with motivation. Provide extra encouragement and practical support."
            return message + context
        
        # Check if user is celebrating
        celebration_keywords = ["finished", "completed", "done", "achieved", "success", "won"]
        if any(keyword in message.lower() for keyword in celebration_keywords):
            context = "\n\nIMPORTANT: The user is sharing a success! Celebrate enthusiastically and encourage continued progress."
            return message + context
        
        return message
    
    async def _add_motivational_enhancements(self, response_data: Dict, original_message: str) -> Dict:
        """Add motivational enhancements to response"""
        # Add motivational elements if using Max personality
        if self.personality.traits.character == "Max":
            response = response_data.get("response", "")
            
            # Add time awareness
            current_time = datetime.now()
            time_context = self._get_time_context(current_time)
            
            # Add progress encouragement
            progress_summary = self.motivational_system.get_progress_summary()
            if progress_summary["streak"] > 0:
                response += f"\n\n🔥 Keep that {progress_summary['streak']}-day streak alive! You're on FIRE! 🔥"
            
            # Add upcoming activity awareness
            upcoming = self.motivational_system.get_upcoming_activities(4)
            if upcoming:
                next_activity = upcoming[0]
                time_until = (next_activity.scheduled_time - current_time).total_seconds() / 3600
                if time_until <= 2:  # Within 2 hours
                    response += f"\n\n⏰ Don't forget: '{next_activity.title}' is coming up! You're going to CRUSH it! 💪"
            
            response_data["response"] = response
            response_data["time_context"] = time_context
            response_data["motivational_enhancements"] = True
        
        return response_data
    
    def _get_celebration_message(self, progress: float) -> str:
        """Get celebration message based on progress"""
        if progress >= 100:
            return "🎉🏆 GOAL COMPLETED! YOU'RE A CHAMPION! 🏆🎉"
        elif progress >= 75:
            return "🚀 WOW! You're in the final stretch! AMAZING work! 🚀"
        elif progress >= 50:
            return "💪 HALFWAY THERE! You're absolutely CRUSHING this! 💪"
        elif progress >= 25:
            return "⚡ Great progress! You're building momentum! ⚡"
        else:
            return "🌟 Every step counts! You're on your way! 🌟"
    
    def _get_progress_encouragement(self, progress: float) -> str:
        """Get encouragement based on progress level"""
        if progress >= 75:
            return "The finish line is RIGHT THERE! Don't stop now! 🏁"
        elif progress >= 50:
            return "You're past the halfway point! Momentum is building! 🚀"
        elif progress >= 25:
            return "Solid foundation! Keep building on this success! 🏗️"
        else:
            return "Every journey starts with a single step! You're moving! 👣"
    
    def _get_streak_message(self, streak: int) -> str:
        """Get message based on current streak"""
        if streak >= 30:
            return "🔥 LEGENDARY STREAK! You're in the top 1% of achievers! 🔥"
        elif streak >= 14:
            return "💎 TWO WEEKS STRONG! You've built a diamond habit! 💎"
        elif streak >= 7:
            return "⚡ ONE WEEK STREAK! You're building unstoppable momentum! ⚡"
        elif streak >= 3:
            return "🌟 THREE DAYS RUNNING! The habit is forming! 🌟"
        elif streak >= 1:
            return "🚀 STREAK STARTED! Every champion begins with day one! 🚀"
        else:
            return "💪 Ready to start your winning streak? Today is day ONE! 💪"
    
    def _get_time_context(self, current_time: datetime) -> str:
        """Get motivational context based on time of day"""
        hour = current_time.hour
        
        if 5 <= hour < 12:
            return "morning_energy"
        elif 12 <= hour < 17:
            return "afternoon_momentum"
        elif 17 <= hour < 21:
            return "evening_achievement"
        else:
            return "night_reflection"
    
    async def _get_last_response(self) -> Dict[str, any]:
        """Get the last stored response"""
        return getattr(self, 'last_response', {
            "response": "I'm here to help you achieve AMAZING things! 🚀",
            "character": self.personality.traits.character,
            "mood": self.personality.traits.mood.value
        })
    
    def toggle_reminders(self, active: bool):
        """Toggle reminder system on/off"""
        self.reminder_active = active
    
    def get_motivational_stats(self) -> Dict:
        """Get comprehensive motivational statistics"""
        return {
            "system_stats": self.motivational_system.get_progress_summary(),
            "personality": {
                "character": self.personality.traits.character,
                "mood": self.personality.traits.mood.value,
                "goal": self.personality.traits.goal.value
            },
            "reminder_active": self.reminder_active,
            "last_check_in": self.last_check_in.isoformat(),
            "total_goals": len(self.motivational_system.goals),
            "total_activities": len(self.motivational_system.activities)
        }

"""
Personality Assessment UI Components
Provides feedback window and assessment interface for personality profiling
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from .personality_profiler import PersonalityProfiler, PersonalityProfile
from .adaptive_personality import AdaptivePersonality

class PersonalityFeedbackWindow:
    """Manages personality feedback display and user interaction"""
    
    def __init__(self, user_id: str, profiler: PersonalityProfiler):
        self.user_id = user_id
        self.profiler = profiler
        self.adaptive_personality = AdaptivePersonality(user_id, profiler)
        self.feedback_history = []
        
    def get_current_feedback(self) -> Dict:
        """Get current personality feedback for display"""
        feedback = self.adaptive_personality.get_personality_feedback()
        
        # Enhance feedback with UI-specific information
        ui_feedback = {
            "window_title": "Personality Profile Feedback",
            "timestamp": datetime.now().isoformat(),
            "user_id": self.user_id,
            "profile_data": feedback,
            "visual_indicators": self._create_visual_indicators(feedback),
            "action_buttons": self._get_action_buttons(feedback),
            "progress_info": self._get_progress_info(feedback)
        }
        
        self.feedback_history.append(ui_feedback)
        return ui_feedback
    
    def _create_visual_indicators(self, feedback: Dict) -> Dict:
        """Create visual indicators for personality traits"""
        if feedback["status"] == "no_profile":
            return {
                "confidence_bar": {"value": 0, "color": "gray", "label": "No Assessment"},
                "trait_indicators": {},
                "adaptation_status": "default"
            }
        
        confidence = feedback["confidence"]
        traits = feedback.get("traits", {})
        
        # Confidence bar
        confidence_color = "red" if confidence < 0.3 else "yellow" if confidence < 0.7 else "green"
        
        # Trait indicators
        trait_indicators = {}
        for trait_name, trait_value in traits.items():
            trait_indicators[trait_name] = {
                "value": trait_value,
                "display_name": trait_name.replace("_", " ").title(),
                "description": self._get_trait_description(trait_name, trait_value)
            }
        
        # Adaptation status
        adaptations = feedback.get("adaptations", {})
        adaptation_status = "active" if any(v != "balanced" and v != "medium" for v in adaptations.values()) else "default"
        
        return {
            "confidence_bar": {
                "value": int(confidence * 100),
                "color": confidence_color,
                "label": f"Profile Confidence: {int(confidence * 100)}%"
            },
            "trait_indicators": trait_indicators,
            "adaptation_status": adaptation_status,
            "adaptations": adaptations
        }
    
    def _get_trait_description(self, trait_name: str, trait_value: str) -> str:
        """Get human-readable description of personality traits"""
        descriptions = {
            "communication_style": {
                "direct": "Prefers clear, concise communication",
                "diplomatic": "Values tactful, considerate responses", 
                "analytical": "Enjoys detailed, data-driven explanations",
                "creative": "Appreciates analogies and creative examples",
                "supportive": "Benefits from encouraging, positive feedback"
            },
            "learning_preference": {
                "visual": "Learns best with diagrams and visual aids",
                "auditory": "Prefers verbal explanations and discussions",
                "kinesthetic": "Learns through hands-on practice",
                "reading": "Enjoys detailed written documentation",
                "social": "Thrives in collaborative learning environments",
                "solitary": "Prefers independent study and reflection"
            },
            "goal_orientation": {
                "achievement": "Motivated by measurable results and success",
                "exploration": "Driven by curiosity and discovery",
                "social": "Focused on helping others and building connections",
                "security": "Values stability and reliable solutions",
                "creativity": "Seeks to create unique and innovative solutions"
            }
        }
        
        return descriptions.get(trait_name, {}).get(trait_value, f"Preference: {trait_value}")
    
    def _get_action_buttons(self, feedback: Dict) -> List[Dict]:
        """Get available action buttons based on current state"""
        buttons = []
        
        if feedback["status"] == "no_profile":
            buttons.append({
                "id": "start_assessment",
                "label": "Start Personality Assessment",
                "style": "primary",
                "description": "Take a quick assessment to personalize your experience"
            })
        elif feedback["confidence"] < 0.5:
            buttons.append({
                "id": "continue_assessment", 
                "label": "Improve Profile Accuracy",
                "style": "secondary",
                "description": "Answer more questions to improve personalization"
            })
        
        if feedback["status"] != "no_profile":
            buttons.append({
                "id": "view_detailed_profile",
                "label": "View Detailed Profile",
                "style": "info",
                "description": "See complete personality analysis"
            })
            
            buttons.append({
                "id": "reset_profile",
                "label": "Reset Profile",
                "style": "warning", 
                "description": "Start personality assessment over"
            })
        
        buttons.append({
            "id": "close_feedback",
            "label": "Close",
            "style": "default",
            "description": "Close feedback window"
        })
        
        return buttons
    
    def _get_progress_info(self, feedback: Dict) -> Dict:
        """Get progress information for assessment"""
        if feedback["status"] == "no_profile":
            return {
                "stage": "Not Started",
                "progress_percent": 0,
                "next_step": "Take personality assessment",
                "estimated_time": "3-5 minutes"
            }
        
        stage_info = {
            "initial": {"name": "Initial Assessment", "progress": 25},
            "partial": {"name": "Partial Profile", "progress": 60},
            "complete": {"name": "Complete Profile", "progress": 85},
            "ongoing": {"name": "Adaptive Learning", "progress": 100}
        }
        
        current_stage = stage_info.get(feedback["status"], {"name": "Unknown", "progress": 0})
        
        return {
            "stage": current_stage["name"],
            "progress_percent": current_stage["progress"],
            "next_step": self._get_next_step(feedback["status"]),
            "estimated_time": "1-2 minutes" if feedback["status"] in ["partial", "complete"] else "3-5 minutes"
        }
    
    def _get_next_step(self, status: str) -> str:
        """Get next recommended step based on current status"""
        next_steps = {
            "initial": "Continue with more assessment questions",
            "partial": "Complete remaining assessment questions",
            "complete": "Profile will adapt automatically during conversations",
            "ongoing": "Profile continuously improves with each interaction"
        }
        
        return next_steps.get(status, "Take personality assessment")

class PersonalityAssessmentUI:
    """Manages the personality assessment user interface"""
    
    def __init__(self, profiler: PersonalityProfiler):
        self.profiler = profiler
        self.current_sessions = {}
    
    def start_assessment_ui(self, user_id: str) -> Dict:
        """Start assessment UI for user"""
        # Get assessment prompt
        adaptive_personality = AdaptivePersonality(user_id, self.profiler)
        prompt_info = adaptive_personality.get_assessment_prompt()
        
        # Start assessment session
        session = self.profiler.start_assessment(user_id)
        self.current_sessions[user_id] = session
        
        return {
            "ui_type": "assessment_intro",
            "title": prompt_info["title"],
            "message": prompt_info["message"],
            "estimated_time": prompt_info["estimated_time"],
            "benefits": prompt_info["benefits"],
            "can_pause": True,
            "can_skip": True,
            "buttons": [
                {"id": "start_questions", "label": "Start Assessment", "style": "primary"},
                {"id": "maybe_later", "label": "Maybe Later", "style": "secondary"},
                {"id": "skip_assessment", "label": "Skip", "style": "default"}
            ]
        }
    
    def get_current_question_ui(self, user_id: str) -> Optional[Dict]:
        """Get current question UI"""
        question_data = self.profiler.get_next_question(user_id)
        
        if not question_data:
            # Check if user has an active session (means assessment is complete in this session)
            # vs no session at all (means they haven't started or need to check saved profile)
            if user_id in self.profiler.assessment_sessions:
                session = self.profiler.assessment_sessions[user_id]
                # If current_question >= total questions, assessment is complete
                if session["current_question"] >= len(session["questions"]):
                    return self._get_assessment_complete_ui(user_id)
            
            # No active session - check if user has a saved completed profile
            saved_profile = self.profiler.load_profile(user_id)
            if saved_profile and saved_profile.assessment_stage == "complete":
                # User has completed assessment previously
                return self._get_assessment_complete_ui(user_id)
            
            # No session and no completed profile - return None so frontend shows welcome screen
            return None
        
        return {
            "ui_type": "assessment_question",
            "question": question_data["text"],
            "options": question_data["options"],
            "progress": question_data["progress"],
            "question_id": question_data["question_id"],
            "can_skip": question_data["can_skip"],
            "can_pause": question_data["can_pause"],
            "selected_option": question_data.get("selected_option"),  # Pass through selected option for highlight
            "buttons": [
                {"id": "pause_assessment", "label": "Pause", "style": "secondary"}
            ]
        }
    
    def process_question_response(self, user_id: str, question_id: str, option_id: int) -> Dict:
        """Process user's response to assessment question"""
        success = self.profiler.record_response(user_id, question_id, option_id)
        
        if not success:
            return {"error": "Failed to record response"}
        
        # Get next question or completion
        next_question = self.get_current_question_ui(user_id)
        
        if next_question and next_question.get("ui_type") == "assessment_complete":
            # Assessment completed, analyze and save profile
            profile = self.profiler.analyze_responses(user_id)
            self.profiler.save_profile(profile)
            
            return next_question
        
        return next_question or {"error": "Assessment error"}
    
    def _get_assessment_complete_ui(self, user_id: str) -> Dict:
        """Get assessment completion UI"""
        profile = self.profiler.analyze_responses(user_id)
        
        return {
            "ui_type": "assessment_complete",
            "title": "Assessment Complete!",
            "message": "Thank you for completing the personality assessment. Your responses will help me provide more personalized assistance.",
            "profile_summary": {
                "communication_style": profile.communication_style.value,
                "learning_preference": profile.learning_preference.value,
                "goal_orientation": profile.goal_orientation.value,
                "confidence_level": f"{int(profile.confidence_level * 100)}%"
            },
            "next_steps": [
                "Your AI responses will now be personalized",
                "The system will continue learning from our interactions",
                "You can view or update your profile anytime"
            ],
            "buttons": [
                {"id": "view_profile", "label": "View Full Profile", "style": "primary"},
                {"id": "start_chatting", "label": "Start Chatting", "style": "secondary"},
                {"id": "close", "label": "Close", "style": "default"}
            ]
        }
    
    def pause_assessment(self, user_id: str) -> Dict:
        """Pause current assessment"""
        # Save session to disk
        saved = self.profiler.pause_session(user_id)
        
        if saved and user_id in self.current_sessions:
            session = self.current_sessions[user_id]
            return {
                "ui_type": "assessment_paused",
                "title": "Assessment Paused",
                "message": f"Progress saved! You can resume anytime. Progress: {session['current_question']}/{len(session['questions'])}",
                "buttons": [
                    {"id": "resume_assessment", "label": "Resume", "style": "primary"},
                    {"id": "close", "label": "Close", "style": "default"}
                ]
            }
        
        return {"error": "No active assessment session"}
    
    def get_detailed_profile_ui(self, user_id: str) -> Dict:
        """Get detailed profile view UI"""
        profile = self.profiler.load_profile(user_id)
        
        if not profile:
            return {"error": "No profile found"}
        
        return {
            "ui_type": "detailed_profile",
            "title": "Your Personality Profile",
            "profile": {
                "Big Five Traits": {
                    "Extraversion": f"{int(profile.extraversion * 100)}%",
                    "Agreeableness": f"{int(profile.agreeableness * 100)}%", 
                    "Conscientiousness": f"{int(profile.conscientiousness * 100)}%",
                    "Emotional Stability": f"{int((1 - profile.neuroticism) * 100)}%",
                    "Openness": f"{int(profile.openness * 100)}%"
                },
                "Communication Preferences": {
                    "Style": profile.communication_style.value.title(),
                    "Learning": profile.learning_preference.value.title(),
                    "Goals": profile.goal_orientation.value.title()
                },
                "Assessment Info": {
                    "Confidence": f"{int(profile.confidence_level * 100)}%",
                    "Stage": profile.assessment_stage.title(),
                    "Interactions": profile.interaction_count,
                    "Last Updated": profile.updated_at[:10]
                }
            },
            "buttons": [
                {"id": "update_profile", "label": "Update Profile", "style": "primary"},
                {"id": "export_profile", "label": "Export Profile", "style": "secondary"},
                {"id": "close", "label": "Close", "style": "default"}
            ]
        }

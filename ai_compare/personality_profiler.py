"""
Psychological Assessment System for User Personality Profiling
Uses psychology-based questions to determine user character and adapt AI conversation style
"""

import json
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path

class PersonalityDimension(Enum):
    """Big Five personality dimensions plus additional traits"""
    EXTRAVERSION = "extraversion"
    AGREEABLENESS = "agreeableness"
    CONSCIENTIOUSNESS = "conscientiousness"
    NEUROTICISM = "neuroticism"
    OPENNESS = "openness"
    COMMUNICATION_STYLE = "communication_style"
    LEARNING_PREFERENCE = "learning_preference"
    GOAL_ORIENTATION = "goal_orientation"

class CommunicationStyle(Enum):
    """Communication preferences"""
    DIRECT = "direct"
    DIPLOMATIC = "diplomatic"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    SUPPORTIVE = "supportive"

class LearningPreference(Enum):
    """Learning style preferences"""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING = "reading"
    SOCIAL = "social"
    SOLITARY = "solitary"

class GoalOrientation(Enum):
    """Goal and motivation types"""
    ACHIEVEMENT = "achievement"
    EXPLORATION = "exploration"
    SOCIAL = "social"
    SECURITY = "security"
    CREATIVITY = "creativity"

@dataclass
class PersonalityProfile:
    """User personality profile with scores and preferences"""
    user_id: str
    extraversion: float = 0.5  # 0-1 scale
    agreeableness: float = 0.5
    conscientiousness: float = 0.5
    neuroticism: float = 0.5
    openness: float = 0.5
    communication_style: CommunicationStyle = CommunicationStyle.SUPPORTIVE
    learning_preference: LearningPreference = LearningPreference.VISUAL
    goal_orientation: GoalOrientation = GoalOrientation.ACHIEVEMENT
    confidence_level: float = 0.5  # How confident we are in this profile
    assessment_stage: str = "initial"  # initial, partial, complete, ongoing
    created_at: str = ""
    updated_at: str = ""
    interaction_count: int = 0
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

class PersonalityQuestion:
    """Individual personality assessment question"""
    
    def __init__(self, question_id: str, text: str, dimension: PersonalityDimension, 
                 options: List[Tuple[str, float]], weight: float = 1.0):
        self.question_id = question_id
        self.text = text
        self.dimension = dimension
        self.options = options  # (option_text, score_impact)
        self.weight = weight

class PersonalityProfiler:
    """Main personality profiling system"""
    
    def __init__(self, profiles_dir: str = "personality_profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(exist_ok=True)
        self.questions = self._initialize_questions()
        self.assessment_sessions = {}  # Track ongoing assessments
        
    def _initialize_questions(self) -> List[PersonalityQuestion]:
        """Initialize psychology-based assessment questions"""
        questions = [
            # Extraversion questions
            PersonalityQuestion(
                "ext_1", 
                "When facing a challenging problem, what's your first instinct?",
                PersonalityDimension.EXTRAVERSION,
                [
                    ("Discuss it with others to get different perspectives", 0.8),
                    ("Think it through on my own first", 0.2),
                    ("Look for similar problems others have solved", 0.5),
                    ("Break it down into smaller parts immediately", 0.4)
                ]
            ),
            PersonalityQuestion(
                "ext_2",
                "How do you prefer to receive feedback?",
                PersonalityDimension.EXTRAVERSION,
                [
                    ("In a group discussion with multiple viewpoints", 0.9),
                    ("One-on-one private conversation", 0.3),
                    ("Written feedback I can review at my own pace", 0.1),
                    ("Quick, direct verbal feedback", 0.6)
                ]
            ),
            
            # Agreeableness questions
            PersonalityQuestion(
                "agr_1",
                "When someone disagrees with your idea, how do you typically respond?",
                PersonalityDimension.AGREEABLENESS,
                [
                    ("Try to understand their perspective and find common ground", 0.9),
                    ("Present more evidence to support my position", 0.3),
                    ("Ask questions to better understand their concerns", 0.8),
                    ("Stick to my position if I believe it's correct", 0.2)
                ]
            ),
            
            # Conscientiousness questions
            PersonalityQuestion(
                "con_1",
                "How do you approach learning something new?",
                PersonalityDimension.CONSCIENTIOUSNESS,
                [
                    ("Create a structured plan and follow it step by step", 0.9),
                    ("Jump in and learn as I go", 0.2),
                    ("Research thoroughly before starting", 0.8),
                    ("Find examples and try to replicate them", 0.5)
                ]
            ),
            
            # Neuroticism (emotional stability) questions
            PersonalityQuestion(
                "neu_1",
                "When you encounter unexpected setbacks, how do you typically feel?",
                PersonalityDimension.NEUROTICISM,
                [
                    ("Stressed and worried about the implications", 0.8),
                    ("Frustrated but ready to find solutions", 0.4),
                    ("Calm and focused on next steps", 0.1),
                    ("Excited by the new challenge", 0.0)
                ]
            ),
            
            # Openness questions
            PersonalityQuestion(
                "ope_1",
                "What type of conversations do you find most engaging?",
                PersonalityDimension.OPENNESS,
                [
                    ("Abstract concepts and theoretical discussions", 0.9),
                    ("Practical problem-solving discussions", 0.3),
                    ("Personal experiences and stories", 0.6),
                    ("Current events and factual information", 0.4)
                ]
            ),
            
            # Communication style questions
            PersonalityQuestion(
                "com_1",
                "How do you prefer explanations to be structured?",
                PersonalityDimension.COMMUNICATION_STYLE,
                [
                    ("Direct and to the point", 0.0),  # DIRECT
                    ("Gentle with context and reasoning", 0.25),  # DIPLOMATIC
                    ("Detailed with data and examples", 0.5),  # ANALYTICAL
                    ("Creative with analogies and stories", 0.75),  # CREATIVE
                    ("Encouraging with positive reinforcement", 1.0)  # SUPPORTIVE
                ]
            ),
            
            # Learning preference questions
            PersonalityQuestion(
                "lea_1",
                "What helps you understand complex topics best?",
                PersonalityDimension.LEARNING_PREFERENCE,
                [
                    ("Visual diagrams and charts", 0.0),  # VISUAL
                    ("Verbal explanations and discussions", 0.2),  # AUDITORY
                    ("Hands-on practice and experimentation", 0.4),  # KINESTHETIC
                    ("Reading detailed documentation", 0.6),  # READING
                    ("Group learning and collaboration", 0.8),  # SOCIAL
                    ("Independent study and reflection", 1.0)  # SOLITARY
                ]
            ),
            
            # Goal orientation questions
            PersonalityQuestion(
                "goa_1",
                "What motivates you most when working on a project?",
                PersonalityDimension.GOAL_ORIENTATION,
                [
                    ("Achieving specific measurable results", 0.0),  # ACHIEVEMENT
                    ("Discovering new possibilities and ideas", 0.25),  # EXPLORATION
                    ("Helping others and making connections", 0.5),  # SOCIAL
                    ("Building stable, reliable solutions", 0.75),  # SECURITY
                    ("Creating something unique and innovative", 1.0)  # CREATIVITY
                ]
            )
        ]
        
        return questions
    
    def start_assessment(self, user_id: str) -> Dict:
        """Start a new personality assessment session"""
        if user_id in self.assessment_sessions:
            return self.assessment_sessions[user_id]
        
        # Select initial questions (start with 3-4 key questions)
        initial_questions = random.sample(self.questions[:6], 3)
        
        session = {
            "user_id": user_id,
            "questions": initial_questions,
            "current_question": 0,
            "responses": {},
            "estimated_time": "3-5 minutes",
            "can_pause": True,
            "stage": "initial"
        }
        
        self.assessment_sessions[user_id] = session
        return session
    
    def get_next_question(self, user_id: str) -> Optional[Dict]:
        """Get the next question in the assessment"""
        if user_id not in self.assessment_sessions:
            return None
        
        session = self.assessment_sessions[user_id]
        
        if session["current_question"] >= len(session["questions"]):
            return None  # Assessment complete
        
        question = session["questions"][session["current_question"]]
        
        return {
            "question_id": question.question_id,
            "text": question.text,
            "options": [{"id": i, "text": opt[0]} for i, opt in enumerate(question.options)],
            "progress": f"{session['current_question'] + 1}/{len(session['questions'])}",
            "can_skip": True,
            "can_pause": True
        }
    
    def record_response(self, user_id: str, question_id: str, option_id: int) -> bool:
        """Record user's response to a question"""
        if user_id not in self.assessment_sessions:
            return False
        
        session = self.assessment_sessions[user_id]
        question = session["questions"][session["current_question"]]
        
        if question.question_id != question_id:
            return False
        
        if option_id >= len(question.options):
            return False
        
        session["responses"][question_id] = {
            "option_id": option_id,
            "option_text": question.options[option_id][0],
            "score_impact": question.options[option_id][1],
            "dimension": question.dimension.value,
            "timestamp": datetime.now().isoformat()
        }
        
        session["current_question"] += 1
        return True
    
    def analyze_responses(self, user_id: str) -> PersonalityProfile:
        """Analyze responses and create personality profile"""
        if user_id not in self.assessment_sessions:
            return PersonalityProfile(user_id)
        
        session = self.assessment_sessions[user_id]
        responses = session["responses"]
        
        # Initialize scores
        dimension_scores = {dim.value: [] for dim in PersonalityDimension}
        
        # Calculate scores for each dimension
        for response in responses.values():
            dimension = response["dimension"]
            score = response["score_impact"]
            dimension_scores[dimension].append(score)
        
        # Create profile
        profile = PersonalityProfile(user_id)
        
        # Calculate average scores
        if dimension_scores[PersonalityDimension.EXTRAVERSION.value]:
            profile.extraversion = sum(dimension_scores[PersonalityDimension.EXTRAVERSION.value]) / len(dimension_scores[PersonalityDimension.EXTRAVERSION.value])
        
        if dimension_scores[PersonalityDimension.AGREEABLENESS.value]:
            profile.agreeableness = sum(dimension_scores[PersonalityDimension.AGREEABLENESS.value]) / len(dimension_scores[PersonalityDimension.AGREEABLENESS.value])
        
        if dimension_scores[PersonalityDimension.CONSCIENTIOUSNESS.value]:
            profile.conscientiousness = sum(dimension_scores[PersonalityDimension.CONSCIENTIOUSNESS.value]) / len(dimension_scores[PersonalityDimension.CONSCIENTIOUSNESS.value])
        
        if dimension_scores[PersonalityDimension.NEUROTICISM.value]:
            profile.neuroticism = sum(dimension_scores[PersonalityDimension.NEUROTICISM.value]) / len(dimension_scores[PersonalityDimension.NEUROTICISM.value])
        
        if dimension_scores[PersonalityDimension.OPENNESS.value]:
            profile.openness = sum(dimension_scores[PersonalityDimension.OPENNESS.value]) / len(dimension_scores[PersonalityDimension.OPENNESS.value])
        
        # Determine communication style
        if dimension_scores[PersonalityDimension.COMMUNICATION_STYLE.value]:
            com_score = sum(dimension_scores[PersonalityDimension.COMMUNICATION_STYLE.value]) / len(dimension_scores[PersonalityDimension.COMMUNICATION_STYLE.value])
            if com_score <= 0.2:
                profile.communication_style = CommunicationStyle.DIRECT
            elif com_score <= 0.4:
                profile.communication_style = CommunicationStyle.DIPLOMATIC
            elif com_score <= 0.6:
                profile.communication_style = CommunicationStyle.ANALYTICAL
            elif com_score <= 0.8:
                profile.communication_style = CommunicationStyle.CREATIVE
            else:
                profile.communication_style = CommunicationStyle.SUPPORTIVE
        
        # Determine learning preference
        if dimension_scores[PersonalityDimension.LEARNING_PREFERENCE.value]:
            learn_score = sum(dimension_scores[PersonalityDimension.LEARNING_PREFERENCE.value]) / len(dimension_scores[PersonalityDimension.LEARNING_PREFERENCE.value])
            if learn_score <= 0.16:
                profile.learning_preference = LearningPreference.VISUAL
            elif learn_score <= 0.33:
                profile.learning_preference = LearningPreference.AUDITORY
            elif learn_score <= 0.5:
                profile.learning_preference = LearningPreference.KINESTHETIC
            elif learn_score <= 0.66:
                profile.learning_preference = LearningPreference.READING
            elif learn_score <= 0.83:
                profile.learning_preference = LearningPreference.SOCIAL
            else:
                profile.learning_preference = LearningPreference.SOLITARY
        
        # Determine goal orientation
        if dimension_scores[PersonalityDimension.GOAL_ORIENTATION.value]:
            goal_score = sum(dimension_scores[PersonalityDimension.GOAL_ORIENTATION.value]) / len(dimension_scores[PersonalityDimension.GOAL_ORIENTATION.value])
            if goal_score <= 0.2:
                profile.goal_orientation = GoalOrientation.ACHIEVEMENT
            elif goal_score <= 0.4:
                profile.goal_orientation = GoalOrientation.EXPLORATION
            elif goal_score <= 0.6:
                profile.goal_orientation = GoalOrientation.SOCIAL
            elif goal_score <= 0.8:
                profile.goal_orientation = GoalOrientation.SECURITY
            else:
                profile.goal_orientation = GoalOrientation.CREATIVITY
        
        # Calculate confidence level based on number of responses
        response_count = len(responses)
        total_questions = len(self.questions)
        profile.confidence_level = min(response_count / total_questions, 1.0)
        
        if response_count >= 3:
            profile.assessment_stage = "partial"
        if response_count >= 6:
            profile.assessment_stage = "complete"
        
        return profile
    
    def save_profile(self, profile: PersonalityProfile):
        """Save personality profile to file"""
        profile_file = self.profiles_dir / f"{profile.user_id}_profile.json"
        
        with open(profile_file, 'w') as f:
            json.dump(asdict(profile), f, indent=2)
    
    def load_profile(self, user_id: str) -> Optional[PersonalityProfile]:
        """Load existing personality profile"""
        profile_file = self.profiles_dir / f"{user_id}_profile.json"
        
        if not profile_file.exists():
            return None
        
        try:
            with open(profile_file, 'r') as f:
                data = json.load(f)
            
            # Convert enum strings back to enums
            if 'communication_style' in data:
                data['communication_style'] = CommunicationStyle(data['communication_style'])
            if 'learning_preference' in data:
                data['learning_preference'] = LearningPreference(data['learning_preference'])
            if 'goal_orientation' in data:
                data['goal_orientation'] = GoalOrientation(data['goal_orientation'])
            
            return PersonalityProfile(**data)
        except Exception as e:
            print(f"Error loading profile for {user_id}: {e}")
            return None
    
    def update_profile_from_interaction(self, user_id: str, interaction_data: Dict):
        """Update profile based on ongoing interactions"""
        profile = self.load_profile(user_id)
        if not profile:
            return
        
        # Analyze interaction patterns and adjust profile
        # This is where ongoing analysis happens
        profile.interaction_count += 1
        profile.updated_at = datetime.now().isoformat()
        profile.assessment_stage = "ongoing"
        
        # Example adjustments based on interaction patterns
        if interaction_data.get('asks_many_questions'):
            profile.openness = min(profile.openness + 0.05, 1.0)
        
        if interaction_data.get('prefers_detailed_responses'):
            profile.conscientiousness = min(profile.conscientiousness + 0.03, 1.0)
        
        if interaction_data.get('responds_quickly'):
            profile.extraversion = min(profile.extraversion + 0.02, 1.0)
        
        self.save_profile(profile)
    
    def get_ai_adaptation_settings(self, profile: PersonalityProfile) -> Dict:
        """Get AI behavior settings based on user personality"""
        settings = {
            "response_style": "balanced",
            "detail_level": "medium",
            "encouragement_level": "medium",
            "formality": "casual",
            "explanation_style": "step_by_step"
        }
        
        # Adapt based on communication style
        if profile.communication_style == CommunicationStyle.DIRECT:
            settings["response_style"] = "concise"
            settings["detail_level"] = "low"
            settings["formality"] = "professional"
        elif profile.communication_style == CommunicationStyle.ANALYTICAL:
            settings["detail_level"] = "high"
            settings["explanation_style"] = "detailed_analysis"
        elif profile.communication_style == CommunicationStyle.SUPPORTIVE:
            settings["encouragement_level"] = "high"
            settings["response_style"] = "encouraging"
        
        # Adapt based on learning preference
        if profile.learning_preference == LearningPreference.VISUAL:
            settings["use_examples"] = True
            settings["suggest_diagrams"] = True
        elif profile.learning_preference == LearningPreference.READING:
            settings["provide_references"] = True
            settings["detail_level"] = "high"
        
        # Adapt based on personality dimensions
        if profile.extraversion > 0.7:
            settings["interaction_style"] = "conversational"
        elif profile.extraversion < 0.3:
            settings["interaction_style"] = "focused"
        
        if profile.neuroticism > 0.6:
            settings["reassurance_level"] = "high"
            settings["error_handling"] = "gentle"
        
        if profile.openness > 0.7:
            settings["creativity_level"] = "high"
            settings["suggest_alternatives"] = True
        
        return settings

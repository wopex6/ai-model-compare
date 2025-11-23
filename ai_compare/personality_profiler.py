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
        self.sessions_dir = self.profiles_dir / "sessions"
        self.sessions_dir.mkdir(exist_ok=True)
        self.questions = self._initialize_questions()
        self.assessment_sessions = {}  # Track ongoing assessments
        self._load_active_sessions()  # Load any paused sessions from disk
        
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
            ),
            
            # Additional Extraversion questions
            PersonalityQuestion(
                "ext_3",
                "After a long day, what helps you recharge?",
                PersonalityDimension.EXTRAVERSION,
                [
                    ("Socializing with friends or colleagues", 0.9),
                    ("Quiet time alone with a book or hobby", 0.1),
                    ("Light socializing in small groups", 0.6),
                    ("A mix of social and alone time", 0.5)
                ]
            ),
            
            # Additional Agreeableness questions
            PersonalityQuestion(
                "agr_2",
                "When making team decisions, what's your priority?",
                PersonalityDimension.AGREEABLENESS,
                [
                    ("Everyone feels heard and valued", 0.9),
                    ("The best logical outcome", 0.2),
                    ("Quick consensus to move forward", 0.6),
                    ("The option that benefits most people", 0.8)
                ]
            ),
            
            # Additional Conscientiousness questions
            PersonalityQuestion(
                "con_2",
                "How do you handle deadlines?",
                PersonalityDimension.CONSCIENTIOUSNESS,
                [
                    ("Plan ahead and finish early", 0.9),
                    ("Work steadily to meet the deadline", 0.7),
                    ("Do my best work under pressure", 0.3),
                    ("Flexible - depends on the task", 0.5)
                ]
            ),
            
            # Additional Neuroticism questions
            PersonalityQuestion(
                "neu_2",
                "How often do you worry about future events?",
                PersonalityDimension.NEUROTICISM,
                [
                    ("Frequently - I plan for many scenarios", 0.9),
                    ("Sometimes - mainly for important events", 0.6),
                    ("Rarely - I deal with things as they come", 0.2),
                    ("Almost never - I'm very optimistic", 0.0)
                ]
            ),
            
            # Additional Openness questions
            PersonalityQuestion(
                "ope_2",
                "When learning something new, you prefer:",
                PersonalityDimension.OPENNESS,
                [
                    ("Exploring creative and unconventional methods", 0.9),
                    ("Following proven, traditional approaches", 0.2),
                    ("Mixing traditional and innovative methods", 0.6),
                    ("Experimenting with various approaches", 0.8)
                ]
            ),
            
            # Additional Communication questions
            PersonalityQuestion(
                "com_2",
                "When giving feedback, you tend to:",
                PersonalityDimension.COMMUNICATION_STYLE,
                [
                    ("Be direct and straightforward", 0.0),
                    ("Sandwich criticism with positives", 0.5),
                    ("Use data and specific examples", 0.3),
                    ("Focus on encouragement and growth", 1.0)
                ]
            ),
            
            # Additional Learning questions
            PersonalityQuestion(
                "lea_2",
                "You retain information best through:",
                PersonalityDimension.LEARNING_PREFERENCE,
                [
                    ("Seeing demonstrations and visuals", 0.0),
                    ("Listening to explanations", 0.2),
                    ("Trying it yourself", 0.4),
                    ("Writing notes and summaries", 0.6)
                ]
            ),
            
            # Additional Goal Orientation questions
            PersonalityQuestion(
                "goa_2",
                "What gives you the most satisfaction?",
                PersonalityDimension.GOAL_ORIENTATION,
                [
                    ("Completing challenging tasks successfully", 0.0),
                    ("Learning and discovering new things", 0.25),
                    ("Helping others achieve their goals", 0.5),
                    ("Building something lasting and reliable", 0.75)
                ]
            ),
            
            # More Extraversion questions
            PersonalityQuestion(
                "ext_4",
                "In a meeting, you typically:",
                PersonalityDimension.EXTRAVERSION,
                [
                    ("Actively participate and share ideas", 0.9),
                    ("Listen mostly, speak when necessary", 0.2),
                    ("Contribute when asked or when I have expertise", 0.5),
                    ("Prefer to discuss ideas with individuals after", 0.1)
                ]
            ),
            PersonalityQuestion(
                "ext_5",
                "How do you prefer to celebrate achievements?",
                PersonalityDimension.EXTRAVERSION,
                [
                    ("With a big group celebration", 0.9),
                    ("Quiet personal acknowledgment", 0.1),
                    ("Small gathering with close friends", 0.6),
                    ("Don't need much celebration", 0.3)
                ]
            ),
            
            # More Agreeableness questions
            PersonalityQuestion(
                "agr_3",
                "When conflicts arise, your approach is:",
                PersonalityDimension.AGREEABLENESS,
                [
                    ("Seek compromise and mutual understanding", 0.9),
                    ("Stand firm on principles", 0.2),
                    ("Avoid confrontation if possible", 0.6),
                    ("Analyze the situation logically", 0.4)
                ]
            ),
            PersonalityQuestion(
                "agr_4",
                "How important is it for you to maintain harmony?",
                PersonalityDimension.AGREEABLENESS,
                [
                    ("Very important - I work hard to keep peace", 0.9),
                    ("Somewhat important - but truth matters more", 0.4),
                    ("Not a priority - results matter most", 0.1),
                    ("Important in personal, less in professional", 0.6)
                ]
            ),
            
            # More Conscientiousness questions
            PersonalityQuestion(
                "con_3",
                "Your workspace is typically:",
                PersonalityDimension.CONSCIENTIOUSNESS,
                [
                    ("Very organized and systematic", 0.9),
                    ("Organized enough to find things", 0.6),
                    ("Creative chaos - I know where things are", 0.3),
                    ("Depends on current workload", 0.5)
                ]
            ),
            PersonalityQuestion(
                "con_4",
                "When planning a project, you:",
                PersonalityDimension.CONSCIENTIOUSNESS,
                [
                    ("Create detailed timelines and checklists", 0.9),
                    ("Have general goals and adapt as you go", 0.3),
                    ("Plan key milestones, flexible on details", 0.6),
                    ("Prefer to start and figure out as you go", 0.1)
                ]
            ),
            
            # More Neuroticism questions
            PersonalityQuestion(
                "neu_3",
                "When facing criticism, you:",
                PersonalityDimension.NEUROTICISM,
                [
                    ("Take it very personally and worry", 0.9),
                    ("Feel briefly upset but recover quickly", 0.5),
                    ("See it as opportunity for growth", 0.1),
                    ("Analyze it objectively", 0.2)
                ]
            ),
            PersonalityQuestion(
                "neu_4",
                "How do you handle uncertainty?",
                PersonalityDimension.NEUROTICISM,
                [
                    ("Find it stressful and anxiety-inducing", 0.9),
                    ("Manage it with careful planning", 0.6),
                    ("Accept it as part of life", 0.2),
                    ("Find it exciting and full of possibilities", 0.0)
                ]
            ),
            
            # More Openness questions
            PersonalityQuestion(
                "ope_3",
                "Your ideal weekend activity:",
                PersonalityDimension.OPENNESS,
                [
                    ("Trying something new and adventurous", 0.9),
                    ("Familiar activities you enjoy", 0.2),
                    ("Mix of new and familiar", 0.6),
                    ("Whatever feels right in the moment", 0.7)
                ]
            ),
            PersonalityQuestion(
                "ope_4",
                "When reading or learning, you prefer:",
                PersonalityDimension.OPENNESS,
                [
                    ("Philosophy, art, abstract concepts", 0.9),
                    ("Practical how-to guides", 0.2),
                    ("Historical facts and biographies", 0.4),
                    ("Science and technical topics", 0.6)
                ]
            ),
            
            # More Communication questions
            PersonalityQuestion(
                "com_3",
                "When explaining complex ideas, you:",
                PersonalityDimension.COMMUNICATION_STYLE,
                [
                    ("Get straight to the key points", 0.0),
                    ("Build context gradually", 0.25),
                    ("Use logical step-by-step breakdown", 0.5),
                    ("Use metaphors and analogies", 0.75),
                    ("Check understanding and adjust approach", 1.0)
                ]
            ),
            PersonalityQuestion(
                "com_4",
                "Your preferred writing style is:",
                PersonalityDimension.COMMUNICATION_STYLE,
                [
                    ("Brief and efficient", 0.0),
                    ("Thoughtful and considerate", 0.5),
                    ("Precise with technical detail", 0.3),
                    ("Engaging with storytelling", 0.8)
                ]
            ),
            
            # More Learning questions
            PersonalityQuestion(
                "lea_3",
                "In a training session, you learn best by:",
                PersonalityDimension.LEARNING_PREFERENCE,
                [
                    ("Watching demonstrations", 0.0),
                    ("Listening to expert lectures", 0.2),
                    ("Hands-on practice immediately", 0.4),
                    ("Reading materials first", 0.6),
                    ("Discussion with peers", 0.8),
                    ("Self-paced independent study", 1.0)
                ]
            ),
            PersonalityQuestion(
                "lea_4",
                "When troubleshooting a problem, you:",
                PersonalityDimension.LEARNING_PREFERENCE,
                [
                    ("Look for visual diagrams or screenshots", 0.0),
                    ("Ask someone to explain it", 0.2),
                    ("Experiment until you figure it out", 0.4),
                    ("Read documentation thoroughly", 0.6)
                ]
            ),
            
            # More Goal Orientation questions
            PersonalityQuestion(
                "goa_3",
                "Success means:",
                PersonalityDimension.GOAL_ORIENTATION,
                [
                    ("Reaching concrete measurable goals", 0.0),
                    ("Continuously learning and growing", 0.25),
                    ("Positive impact on others", 0.5),
                    ("Long-term stability and security", 0.75),
                    ("Creating unique and original work", 1.0)
                ]
            ),
            PersonalityQuestion(
                "goa_4",
                "When choosing projects, priority goes to:",
                PersonalityDimension.GOAL_ORIENTATION,
                [
                    ("Clear objectives with measurable outcomes", 0.0),
                    ("Opportunities to learn new things", 0.25),
                    ("Helping or collaborating with others", 0.5),
                    ("Building something sustainable", 0.75)
                ]
            ),
            
            # Additional diverse questions for better profiling
            PersonalityQuestion(
                "ext_6",
                "Your energy level is highest:",
                PersonalityDimension.EXTRAVERSION,
                [
                    ("When surrounded by people and activity", 0.9),
                    ("In quiet, peaceful environments", 0.1),
                    ("Varies based on the situation", 0.5),
                    ("When focused on interesting work", 0.4)
                ]
            ),
            PersonalityQuestion(
                "agr_5",
                "When someone makes a mistake, you:",
                PersonalityDimension.AGREEABLENESS,
                [
                    ("Focus on understanding and helping them improve", 0.9),
                    ("Point out the error and correct approach", 0.2),
                    ("Mention it gently with encouragement", 0.7),
                    ("Fix it yourself without mentioning", 0.5)
                ]
            ),
            PersonalityQuestion(
                "con_5",
                "You view rules and procedures as:",
                PersonalityDimension.CONSCIENTIOUSNESS,
                [
                    ("Important guidelines to follow carefully", 0.9),
                    ("Suggestions that can be adapted", 0.3),
                    ("Necessary but sometimes constraining", 0.5),
                    ("Starting points for improvement", 0.4)
                ]
            ),
            PersonalityQuestion(
                "neu_5",
                "Your stress management approach:",
                PersonalityDimension.NEUROTICISM,
                [
                    ("I get stressed easily and need support", 0.9),
                    ("I manage stress with specific techniques", 0.4),
                    ("Stress doesn't affect me much", 0.1),
                    ("I thrive under moderate pressure", 0.2)
                ]
            ),
            PersonalityQuestion(
                "ope_5",
                "When presented with a new idea, you:",
                PersonalityDimension.OPENNESS,
                [
                    ("Embrace it enthusiastically", 0.9),
                    ("Evaluate it carefully first", 0.3),
                    ("Consider both pros and cons", 0.6),
                    ("Prefer proven approaches", 0.1)
                ]
            ),
            PersonalityQuestion(
                "com_5",
                "In conversations, you prioritize:",
                PersonalityDimension.COMMUNICATION_STYLE,
                [
                    ("Efficiency and clarity", 0.0),
                    ("Maintaining positive relationships", 0.8),
                    ("Accuracy and completeness", 0.3),
                    ("Creativity and engagement", 0.7)
                ]
            ),
            PersonalityQuestion(
                "lea_5",
                "Your ideal learning environment:",
                PersonalityDimension.LEARNING_PREFERENCE,
                [
                    ("Visual presentations and demos", 0.0),
                    ("Interactive discussions", 0.2),
                    ("Hands-on lab or workshop", 0.4),
                    ("Library or quiet study space", 0.6),
                    ("Collaborative group setting", 0.8),
                    ("Self-directed online learning", 1.0)
                ]
            ),
            PersonalityQuestion(
                "goa_5",
                "You feel most accomplished when:",
                PersonalityDimension.GOAL_ORIENTATION,
                [
                    ("You exceed performance targets", 0.0),
                    ("You discover something new", 0.25),
                    ("You help someone succeed", 0.5),
                    ("You build something reliable", 0.75),
                    ("You create something innovative", 1.0)
                ]
            ),
            
            # Final round of questions for comprehensive assessment
            PersonalityQuestion(
                "ext_7",
                "Networking events make you feel:",
                PersonalityDimension.EXTRAVERSION,
                [
                    ("Energized and excited", 0.9),
                    ("Drained but manageable", 0.3),
                    ("Uncomfortable and exhausting", 0.1),
                    ("Depends on the people and topic", 0.6)
                ]
            ),
            PersonalityQuestion(
                "agr_6",
                "When giving advice, you're typically:",
                PersonalityDimension.AGREEABLENESS,
                [
                    ("Empathetic and supportive", 0.9),
                    ("Direct and honest", 0.2),
                    ("Balanced and diplomatic", 0.7),
                    ("Analytical and objective", 0.4)
                ]
            ),
            PersonalityQuestion(
                "con_6",
                "For long-term goals, you:",
                PersonalityDimension.CONSCIENTIOUSNESS,
                [
                    ("Create detailed multi-year plans", 0.9),
                    ("Have general direction, plan quarterly", 0.6),
                    ("Adapt goals based on opportunities", 0.3),
                    ("Focus on present, future unfolds naturally", 0.1)
                ]
            ),
            PersonalityQuestion(
                "neu_6",
                "When things don't go as planned:",
                PersonalityDimension.NEUROTICISM,
                [
                    ("I feel anxious and overthink it", 0.9),
                    ("I feel disappointed but move on", 0.4),
                    ("I quickly pivot to plan B", 0.1),
                    ("I see it as a learning opportunity", 0.2)
                ]
            ),
            PersonalityQuestion(
                "ope_6",
                "Your approach to traditions:",
                PersonalityDimension.OPENNESS,
                [
                    ("Value and respect tradition", 0.2),
                    ("Question and often change traditions", 0.9),
                    ("Appreciate some, question others", 0.6),
                    ("Create new traditions", 0.8)
                ]
            ),
            PersonalityQuestion(
                "com_6",
                "When someone is upset, you:",
                PersonalityDimension.COMMUNICATION_STYLE,
                [
                    ("Offer direct solutions", 0.0),
                    ("Listen empathetically and comfort", 1.0),
                    ("Ask questions to understand the problem", 0.5),
                    ("Give space until they're ready", 0.3)
                ]
            ),
            PersonalityQuestion(
                "lea_6",
                "To master a skill, you prefer:",
                PersonalityDimension.LEARNING_PREFERENCE,
                [
                    ("Watch experts perform it", 0.0),
                    ("Have someone guide you through it", 0.2),
                    ("Practice repeatedly on your own", 0.4),
                    ("Study the theory then apply", 0.6),
                    ("Learn with a study group", 0.8),
                    ("Figure it out through trial and error", 1.0)
                ]
            ),
            PersonalityQuestion(
                "goa_6",
                "Your work motivation comes from:",
                PersonalityDimension.GOAL_ORIENTATION,
                [
                    ("Competition and achievement", 0.0),
                    ("Curiosity and discovery", 0.25),
                    ("Making a difference for others", 0.5),
                    ("Building lasting value", 0.75),
                    ("Self-expression and innovation", 1.0)
                ]
            )
        ]
        
        return questions
    
    def start_assessment(self, user_id: str) -> Dict:
        """Start a new personality assessment session"""
        if user_id in self.assessment_sessions:
            return self.assessment_sessions[user_id]
        
        # Use ALL questions, shuffled once at the start
        all_questions = random.sample(self.questions, len(self.questions))
        
        session = {
            "user_id": user_id,
            "questions": all_questions,
            "current_question": 0,
            "responses": {},
            "estimated_time": "10-15 minutes",
            "can_pause": True,
            "stage": "full"
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
        
        # Check if this question was already answered (e.g., when going back)
        selected_option = None
        if question.question_id in session["responses"]:
            selected_option = session["responses"][question.question_id]["option_id"]
        
        return {
            "question_id": question.question_id,
            "text": question.text,
            "options": [{"id": i, "text": opt[0]} for i, opt in enumerate(question.options)],
            "progress": f"{session['current_question'] + 1}/{len(session['questions'])}",
            "can_skip": False,
            "can_pause": True,
            "selected_option": selected_option  # Include previously selected answer
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
        
        # Auto-save progress after each response
        self._save_session(user_id)
        
        return True
    
    def go_back(self, user_id: str) -> bool:
        """Go back to previous question"""
        if user_id not in self.assessment_sessions:
            return False
        
        session = self.assessment_sessions[user_id]
        
        # Can't go back from first question
        if session["current_question"] <= 0:
            return False
        
        # Go back one question
        session["current_question"] -= 1
        
        # Keep the previous response so it can be shown as selected
        # User can change it by selecting a different option
        
        # Save the updated session
        self._save_session(user_id)
        
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
        
        # Determine assessment stage
        if response_count >= total_questions:
            profile.assessment_stage = "complete"
        elif response_count >= total_questions * 0.5:
            profile.assessment_stage = "partial"
        else:
            profile.assessment_stage = "initial"
        
        return profile
    
    def save_profile(self, profile: PersonalityProfile):
        """Save personality profile to file and database with history"""
        profile_file = self.profiles_dir / f"{profile.user_id}_profile.json"
        
        # Convert profile to dict and handle enum serialization
        profile_dict = asdict(profile)
        
        # Convert enums to their string values (handle both enum objects and strings)
        for enum_field in ['communication_style', 'learning_preference', 'goal_orientation']:
            value = profile_dict.get(enum_field)
            if hasattr(value, 'value'):
                # It's an enum object - get the string value
                profile_dict[enum_field] = value.value
            elif isinstance(value, str):
                # Already a string - keep it
                pass
            else:
                # Unknown type - try to convert to string
                profile_dict[enum_field] = str(value)
        
        with open(profile_file, 'w') as f:
            json.dump(profile_dict, f, indent=2)
        
        # Also save to database if we have a user_profile_manager
        try:
            from integrated_database import IntegratedDatabase
            db = IntegratedDatabase()
            
            # Get existing profile to maintain history
            existing_profile = db.get_user_profile_by_username(profile.user_id)
            if existing_profile:
                user_id = existing_profile['id']
                current_prefs = existing_profile.get('preferences', {})
                assessment_history = current_prefs.get('assessment_history', [])
                
                # Create new assessment entry with timestamp
                new_assessment = {
                    'timestamp': profile.updated_at,
                    'jung_types': {
                        'extraversion_introversion': (profile.extraversion - 0.5) * 20,  # Convert 0-1 to -10 to +10
                        'sensing_intuition': (profile.openness - 0.5) * 20,
                        'thinking_feeling': (profile.agreeableness - 0.5) * 20,
                        'judging_perceiving': (profile.conscientiousness - 0.5) * 20
                    },
                    'big_five': {
                        'openness': int(profile.openness * 10),
                        'conscientiousness': int(profile.conscientiousness * 10),
                        'extraversion': int(profile.extraversion * 10),
                        'agreeableness': int(profile.agreeableness * 10),
                        'neuroticism': int(profile.neuroticism * 10)
                    }
                }
                
                # Add to history
                assessment_history.append(new_assessment)
                
                # Keep only last 10 assessments
                if len(assessment_history) > 10:
                    assessment_history = assessment_history[-10:]
                
                # Update preferences with current traits and history
                psychological_attributes = {
                    'jung_types': new_assessment['jung_types'],
                    'big_five': new_assessment['big_five'],
                    'assessment_completed_at': profile.updated_at,
                    'assessment_history': assessment_history
                }
                
                db.update_user_preferences(user_id, psychological_attributes)
        except Exception as e:
            print(f"Warning: Could not save to database: {e}")
            # Continue even if database save fails
    
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
    
    def _save_session(self, user_id: str):
        """Save assessment session to disk"""
        if user_id not in self.assessment_sessions:
            return
        
        session = self.assessment_sessions[user_id].copy()
        
        # Convert PersonalityQuestion objects to serializable format
        serializable_questions = []
        for q in session["questions"]:
            serializable_questions.append({
                "question_id": q.question_id,
                "text": q.text,
                "dimension": q.dimension.value,
                "options": q.options,
                "weight": q.weight
            })
        
        session["questions"] = serializable_questions
        
        # Save to file
        session_file = self.sessions_dir / f"{user_id}_session.json"
        with open(session_file, 'w') as f:
            json.dump(session, f, indent=2)
    
    def _load_active_sessions(self):
        """Load all paused sessions from disk"""
        if not self.sessions_dir.exists():
            return
        
        for session_file in self.sessions_dir.glob("*_session.json"):
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                
                # Reconstruct PersonalityQuestion objects
                questions = []
                for q_data in session_data["questions"]:
                    dimension = PersonalityDimension(q_data["dimension"])
                    questions.append(PersonalityQuestion(
                        q_data["question_id"],
                        q_data["text"],
                        dimension,
                        q_data["options"],
                        q_data.get("weight", 1.0)
                    ))
                
                session_data["questions"] = questions
                user_id = session_data["user_id"]
                self.assessment_sessions[user_id] = session_data
                
            except Exception as e:
                print(f"Error loading session {session_file}: {e}")
    
    def pause_session(self, user_id: str) -> bool:
        """Pause and save assessment session"""
        if user_id in self.assessment_sessions:
            self._save_session(user_id)
            return True
        return False
    
    def clear_session(self, user_id: str):
        """Clear session from memory and disk"""
        # Remove from memory
        if user_id in self.assessment_sessions:
            del self.assessment_sessions[user_id]
        
        # Remove from disk
        session_file = self.sessions_dir / f"{user_id}_session.json"
        if session_file.exists():
            session_file.unlink()

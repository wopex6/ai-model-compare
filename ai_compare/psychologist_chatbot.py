"""
Psychologist Chatbot - Dr. Elena
A compassionate, evidence-based psychologist offering therapeutic insights
"""
from typing import Dict, List, Optional
import random
from .chatbot import AIChatbot
from .knowledge_enhanced_chatbot import KnowledgeEnhancedMixin


class PsychologistChatbot(KnowledgeEnhancedMixin, AIChatbot):
    """
    Dr. Elena - A compassionate psychologist chatbot
    Offers evidence-based psychological insights, therapeutic techniques, and emotional support
    """
    
    def __init__(self, personality_preset: str = "psychologist", user_preset: str = "casual_learner"):
        super().__init__(personality_preset, user_preset)
        
        # Setup knowledge system for psychology sources (optional - requires ChromaDB)
        try:
            self.setup_knowledge("psychologist")
        except ImportError as e:
            print(f"Knowledge system not available: {e}")
            self._knowledge_enabled = False
        
        # Initialize therapeutic approaches
        self.therapeutic_approaches = self._initialize_approaches()
        self.psychological_concepts = self._initialize_concepts()
        self.coping_strategies = self._initialize_coping_strategies()
        self.assessment_questions = self._initialize_assessment_questions()
    
    def _initialize_approaches(self) -> Dict[str, Dict]:
        """Initialize therapeutic approaches and their key principles"""
        return {
            "cognitive_behavioral": {
                "name": "Cognitive Behavioral Therapy (CBT)",
                "focus": "Identifying and changing negative thought patterns",
                "key_concepts": [
                    "cognitive distortions",
                    "automatic thoughts",
                    "behavioral activation",
                    "cognitive restructuring"
                ],
                "techniques": [
                    "thought records",
                    "behavioral experiments",
                    "exposure therapy",
                    "activity scheduling"
                ]
            },
            "humanistic": {
                "name": "Humanistic/Person-Centered Therapy",
                "focus": "Self-actualization and personal growth",
                "key_concepts": [
                    "unconditional positive regard",
                    "self-actualization",
                    "congruence",
                    "empathic understanding"
                ],
                "techniques": [
                    "active listening",
                    "reflection",
                    "genuineness",
                    "non-directive support"
                ]
            },
            "existential": {
                "name": "Existential Therapy",
                "focus": "Finding meaning and purpose in life",
                "key_concepts": [
                    "meaning and purpose",
                    "freedom and responsibility",
                    "death and mortality",
                    "isolation and connection"
                ],
                "techniques": [
                    "existential inquiry",
                    "meaning-making",
                    "values clarification",
                    "choice awareness"
                ]
            },
            "positive": {
                "name": "Positive Psychology",
                "focus": "Building strengths and well-being",
                "key_concepts": [
                    "character strengths",
                    "flourishing",
                    "gratitude",
                    "resilience"
                ],
                "techniques": [
                    "gratitude practices",
                    "strengths assessment",
                    "savoring exercises",
                    "optimism building"
                ]
            }
        }
    
    def _initialize_concepts(self) -> Dict[str, str]:
        """Initialize key psychological concepts and explanations"""
        return {
            "self_actualization": "The realization of one's full potential and capabilities",
            "cognitive_distortions": "Patterns of biased thinking that negatively impact emotions",
            "defense_mechanisms": "Unconscious strategies to protect the ego from anxiety",
            "attachment_theory": "How early relationships shape our ability to connect with others",
            "emotional_regulation": "The ability to manage and respond to emotional experiences",
            "mindfulness": "Present-moment awareness without judgment",
            "schema": "Core beliefs about ourselves, others, and the world",
            "transference": "Unconsciously redirecting feelings from past relationships to present ones",
            "resilience": "The ability to bounce back from adversity",
            "neuroplasticity": "The brain's ability to reorganize and form new neural connections"
        }
    
    def _initialize_coping_strategies(self) -> Dict[str, List[str]]:
        """Initialize evidence-based coping strategies"""
        return {
            "anxiety": [
                "Deep breathing exercises (4-7-8 technique)",
                "Progressive muscle relaxation",
                "Grounding techniques (5-4-3-2-1 method)",
                "Cognitive reframing of anxious thoughts",
                "Gradual exposure to feared situations"
            ],
            "depression": [
                "Behavioral activation (scheduling pleasant activities)",
                "Exercise and physical movement",
                "Social connection and support",
                "Challenging negative automatic thoughts",
                "Establishing a regular sleep schedule"
            ],
            "stress": [
                "Time management and prioritization",
                "Setting healthy boundaries",
                "Mindfulness meditation",
                "Physical exercise and self-care",
                "Problem-solving strategies"
            ],
            "relationship": [
                "Active listening and validation",
                "Using 'I' statements",
                "Identifying and expressing needs clearly",
                "Practicing empathy and perspective-taking",
                "Taking time-outs when emotions escalate"
            ],
            "self_esteem": [
                "Identifying and challenging self-critical thoughts",
                "Practicing self-compassion",
                "Recognizing and celebrating achievements",
                "Setting and achieving small goals",
                "Surrounding yourself with supportive people"
            ]
        }
    
    def _initialize_assessment_questions(self) -> Dict[str, List[str]]:
        """Questions to better understand the person's situation"""
        return {
            "emotional_state": [
                "Can you tell me more about how you've been feeling lately?",
                "What emotions have been most present for you?",
                "How would you describe your mood over the past few weeks?"
            ],
            "situation": [
                "What brings you here today?",
                "Can you describe what's been happening?",
                "What would you like to work on or understand better?"
            ],
            "coping": [
                "What have you tried so far to address this?",
                "What usually helps you feel better in difficult times?",
                "Who or what do you turn to for support?"
            ],
            "goals": [
                "What would you like to be different?",
                "How would you know things are getting better?",
                "What does healing or growth look like for you?"
            ]
        }
    
    async def chat(self, user_message: str, include_context: bool = True) -> Dict:
        """
        Enhanced chat with psychological insights
        Detects emotional content and provides appropriate therapeutic responses
        """
        # Detect topic area
        topic_area = self._detect_topic_area(user_message)
        
        # Check if asking about specific approach or concept
        if topic_area == "concept_inquiry":
            return await self._explain_concept(user_message)
        
        if topic_area == "coping_request":
            return await self._provide_coping_strategies(user_message)
        
        if topic_area == "therapy_question":
            return await self._explain_therapy_approach(user_message)
        
        # For general conversation, use knowledge-enhanced chat if available
        # This will search psychology literature and add relevant context
        if hasattr(self, '_knowledge_enabled') and self._knowledge_enabled:
            response = await self.chat_with_knowledge(user_message, include_context)
        else:
            response = await super().chat(user_message, include_context)
        
        # Add therapeutic enhancement
        response = self._add_therapeutic_elements(response, user_message)
        
        return response
    
    def _detect_topic_area(self, message: str) -> str:
        """Detect what type of psychological inquiry this is"""
        message_lower = message.lower()
        
        # Check for concept questions
        concept_keywords = ["what is", "explain", "define", "tell me about", "what does", "meaning of"]
        if any(kw in message_lower for kw in concept_keywords):
            if any(concept in message_lower for concept in self.psychological_concepts.keys()):
                return "concept_inquiry"
        
        # Check for coping strategy requests
        coping_keywords = ["how do i", "help me", "what should i do", "how can i cope", 
                          "strategies for", "techniques for", "dealing with"]
        if any(kw in message_lower for kw in coping_keywords):
            return "coping_request"
        
        # Check for therapy approach questions
        therapy_keywords = ["cbt", "cognitive behavioral", "humanistic", "person-centered",
                          "existential", "positive psychology", "therapy approach"]
        if any(kw in message_lower for kw in therapy_keywords):
            return "therapy_question"
        
        return "general"
    
    async def _explain_concept(self, message: str) -> Dict:
        """Explain a psychological concept"""
        message_lower = message.lower()
        
        # Find matching concept
        for concept_key, explanation in self.psychological_concepts.items():
            concept_display = concept_key.replace("_", " ")
            if concept_display in message_lower or concept_key in message_lower:
                response = f"Let me explain **{concept_display}**:\n\n{explanation}\n\n"
                
                # Add related therapeutic context
                if concept_key in ["cognitive_distortions", "emotional_regulation"]:
                    response += "This concept is central to Cognitive Behavioral Therapy (CBT), "
                    response += "which helps people identify and change unhelpful patterns.\n\n"
                elif concept_key in ["self_actualization", "unconditional_positive_regard"]:
                    response += "This is a key concept in Humanistic Psychology, pioneered by "
                    response += "Carl Rogers and Abraham Maslow.\n\n"
                
                response += "Would you like to know more about how this applies to your situation, "
                response += "or explore related concepts?"
                
                return {"response": response, "concept_explained": concept_key}
        
        # If no specific concept found, use knowledge-enhanced chat if available
        if hasattr(self, '_knowledge_enabled') and self._knowledge_enabled:
            return await self.chat_with_knowledge(message)
        else:
            return await super().chat(message)
    
    async def _provide_coping_strategies(self, message: str) -> Dict:
        """Provide evidence-based coping strategies (CONTEXT-AWARE)"""
        message_lower = message.lower()
        
        # Extract explicit context if present
        context_data = self._extract_context_from_message(message)
        
        # Detect issue area
        issue_area = None
        if any(word in message_lower for word in ["anxious", "anxiety", "worried", "panic", "fear"]):
            issue_area = "anxiety"
        elif any(word in message_lower for word in ["depressed", "depression", "sad", "hopeless", "down"]):
            issue_area = "depression"
        elif any(word in message_lower for word in ["stressed", "stress", "overwhelmed", "pressure"]):
            issue_area = "stress"
        elif any(word in message_lower for word in ["relationship", "partner", "conflict", "communication"]):
            issue_area = "relationship"
        elif any(word in message_lower for word in ["self-esteem", "confidence", "worth", "value"]):
            issue_area = "self_esteem"
        
        if issue_area and issue_area in self.coping_strategies:
            strategies = self.coping_strategies[issue_area]
            
            # Context-aware intro
            if context_data:
                emotion = context_data.get('emotion', issue_area.replace('_', ' '))
                goal = context_data.get('goal', '')
                
                if goal:
                    response = f"I can see you're experiencing {emotion} while working toward {goal}. That's a significant challenge, and your feelings are completely valid. "
                else:
                    response = f"I hear that you're experiencing {emotion}. Your feelings are valid and understandable. "
            else:
                response = f"I hear that you're dealing with **{issue_area.replace('_', '-')}**. "
            
            response += "Here are some evidence-based strategies that many people find helpful:\n\n"
            
            for i, strategy in enumerate(strategies, 1):
                response += f"{i}. {strategy}\n"
            
            response += "\n**Important note**: These strategies work best when practiced regularly. "
            response += "Start with one or two that resonate with you, rather than trying everything at once.\n\n"
            
            # Context-aware closing
            if context_data and context_data.get('goal'):
                response += f"💡 These strategies can help you manage {issue_area} while staying focused on {context_data['goal']}. "
            
            response += "Would you like me to elaborate on any of these strategies, or discuss "
            response += "what might work best for your specific situation?"
            
            return {"response": response, "strategies_provided": issue_area, "context_used": bool(context_data)}
        
        # General coping response
        if hasattr(self, '_knowledge_enabled') and self._knowledge_enabled:
            return await self.chat_with_knowledge(message)
        else:
            return await super().chat(message)
    
    async def _explain_therapy_approach(self, message: str) -> Dict:
        """Explain a therapeutic approach"""
        message_lower = message.lower()
        
        for approach_key, approach_info in self.therapeutic_approaches.items():
            if approach_key.replace("_", " ") in message_lower or approach_info["name"].lower() in message_lower:
                response = f"**{approach_info['name']}**\n\n"
                response += f"**Focus**: {approach_info['focus']}\n\n"
                response += "**Key Concepts**:\n"
                for concept in approach_info['key_concepts']:
                    response += f"• {concept}\n"
                response += "\n**Common Techniques**:\n"
                for technique in approach_info['techniques']:
                    response += f"• {technique}\n"
                
                response += "\nThis approach can be particularly helpful for certain concerns. "
                response += "Would you like to know more about how it might apply to your situation?"
                
                return {"response": response, "approach_explained": approach_key}
        
        if hasattr(self, '_knowledge_enabled') and self._knowledge_enabled:
            return await self.chat_with_knowledge(message)
        else:
            return await super().chat(message)
    
    def _add_therapeutic_elements(self, response: Dict, user_message: str) -> Dict:
        """Add therapeutic elements like validation and reflection"""
        original_response = response.get("response", "")
        
        # Detect emotional content
        emotion_detected = self._detect_emotions(user_message)
        
        if emotion_detected:
            # Add validation
            validations = [
                "I can sense this is challenging for you. ",
                "It sounds like you're going through a difficult time. ",
                "Thank you for sharing that with me. ",
                "I appreciate your openness in discussing this. "
            ]
            validation = random.choice(validations)
            
            # Prepend validation to response
            response["response"] = validation + original_response
        
        # Add therapeutic closing
        closings = [
            "\n\nRemember, seeking understanding is a sign of strength, not weakness.",
            "\n\nTake your time processing this. Growth happens at your own pace.",
            "\n\nI'm here to support you on this journey of self-discovery.",
            "\n\nYour feelings are valid, and working through them takes courage."
        ]
        
        response["response"] += random.choice(closings)
        
        return response
    
    def _detect_emotions(self, message: str) -> bool:
        """Detect if message contains emotional content"""
        emotion_words = [
            "feel", "feeling", "felt", "anxious", "worried", "sad", "happy",
            "angry", "frustrated", "confused", "scared", "afraid", "hurt",
            "lonely", "overwhelmed", "stressed", "depressed", "hopeless"
        ]
        message_lower = message.lower()
        return any(word in message_lower for word in emotion_words)
    
    def get_daily_insight(self) -> str:
        """Get a daily psychological insight"""
        insights = [
            "Self-compassion is not self-indulgence. Treating yourself with kindness strengthens resilience.",
            "Your thoughts are not facts. Learning to observe them without judgment creates emotional freedom.",
            "Connection with others is a fundamental human need. Nurture your relationships.",
            "Meaning and purpose aren't found; they're created through your choices and actions.",
            "Vulnerability is the birthplace of innovation, creativity, and change. - Brené Brown",
            "Between stimulus and response there is a space. In that space is our power to choose. - Viktor Frankl",
            "The curious paradox is that when I accept myself just as I am, then I can change. - Carl Rogers",
            "What we resist persists. Acceptance is the first step toward transformation.",
            "You are not your anxiety. You are the awareness that notices the anxiety.",
            "Growth happens at the edge of your comfort zone, not in the middle of it."
        ]
        return random.choice(insights)
    
    def get_psychologist_stats(self) -> Dict:
        """Get statistics about the psychologist's knowledge"""
        stats = self.get_knowledge_stats()
        stats["therapeutic_approaches"] = len(self.therapeutic_approaches)
        stats["psychological_concepts"] = len(self.psychological_concepts)
        stats["coping_strategy_categories"] = len(self.coping_strategies)
        return stats

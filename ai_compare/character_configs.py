"""
Character Configurations - All character-specific data in one place
Easy to add new characters without code duplication
"""

CHARACTER_CONFIGS = {
    "gentle_companion": {
        "display_name": "Sam",
        "tagline": "A friendly ear",
        "description": "Just here to listen and chat — no pressure, no agenda.",

        "theme": {
            "primary_color": "#7E9CB8",
            "secondary_color": "#A8C0D6",
            "icon": "fa-comment-dots",
            "gradient": "linear-gradient(135deg, #7E9CB8, #A8C0D6)"
        },

        # Custom minimal template — no sidebar, no progress UI
        "custom_template": "gentle_companion.html",

        # All structured knowledge intentionally empty.
        # Sam doesn't push frameworks, exercises, or strategies.
        "concepts": {},
        "approaches": {},
        "strategies": {},
        "exercises": {},

        # Soft, non-prescriptive ambient prompts (shown only if surfaced naturally)
        "daily_insights": [
            "No need to have it all figured out today.",
            "Whatever you're carrying, you don't have to carry it alone right now.",
            "It's okay to not know yet.",
            "Small is okay. Slow is okay.",
            "You don't have to perform here.",
        ],

        # Gentle conversation starters — not tasks
        "quick_topics": [
            {"label": "Just chat", "message": "Hey, just feel like talking for a bit."},
            {"label": "Something on my mind", "message": "There's something on my mind I'm not sure about."},
            {"label": "Heavy day", "message": "It's been kind of a heavy day."},
            {"label": "Quiet moment", "message": "Just wanted a quiet moment with someone."}
        ],

        "concept_keywords": [],
        "strategy_keywords": [],
        "approach_keywords": []
    },

    "super_motivational_coach": {
        "display_name": "Coach Max",
        "tagline": "Your Ultimate Motivational Partner",
        "description": "High-energy motivational coach helping you set goals, stay accountable, and achieve greatness",
        
        "theme": {
            "primary_color": "#FF5722",
            "secondary_color": "#FF8A65",
            "icon": "fa-fire",
            "gradient": "linear-gradient(135deg, #FF5722, #FF8A65)"
        },
        
        "custom_template": "motivational_coach.html",  # Use existing custom UI
        
        "concepts": {},
        "approaches": {},
        "strategies": {},
        "exercises": {},
        
        "daily_insights": [
            "The only way to do great work is to love what you do! 🔥",
            "Your potential is LIMITLESS! Go get it! 💪",
            "Every champion was once a contender who refused to give up!",
            "Success is not final, failure is not fatal: it's the courage to continue that counts!",
            "The future depends on what you do TODAY! Let's make it count! 🚀",
            "You've got this! ONE MORE REP! 💯",
            "Dream BIG! Start NOW! Stay FOCUSED! You're UNSTOPPABLE!",
            "The pain you feel today will be the STRENGTH you feel tomorrow!",
            "Believe you can and you're halfway there! Let's GO! 🎯",
            "Your only limit is YOU! Break through it today! 🔥"
        ],
        
        "quick_topics": [
            {"label": "Set Goal", "message": "add goal \"My Goal\" \"Description\""},
            {"label": "Show Progress", "message": "show progress"},
            {"label": "Motivate Me", "message": "motivate me"},
            {"label": "What's Next", "message": "upcoming activities"}
        ],
        
        "concept_keywords": [],
        "strategy_keywords": [],
        "approach_keywords": []
    },
    
    "wisdom_sage": {
        "display_name": "Sage Wei",
        "tagline": "Ancient Wisdom for Modern Life",
        "description": "A wise sage sharing Taoist philosophy, Eastern wisdom, and timeless insights for living harmoniously",
        
        "theme": {
            "primary_color": "#795548",
            "secondary_color": "#A1887F",
            "icon": "fa-book-open",
            "gradient": "linear-gradient(135deg, #795548, #A1887F)"
        },
        
        "custom_template": "wisdom_sage.html",  # Use existing custom UI
        
        "concepts": {},
        "approaches": {},
        "strategies": {},
        "exercises": {},
        
        "daily_insights": [
            "A journey of a thousand miles begins with a single step. - Lao Tzu",
            "When I let go of what I am, I become what I might be.",
            "Nature does not hurry, yet everything is accomplished.",
            "The wise man is one who knows what he does not know.",
            "Flow with whatever may happen and let your mind be free.",
            "Knowing others is intelligence; knowing yourself is true wisdom.",
            "He who knows that enough is enough will always have enough.",
            "Do you have the patience to wait till your mud settles and the water is clear?",
            "The snow goose need not bathe to make itself white. Neither need you do anything but be yourself.",
            "To the mind that is still, the whole universe surrenders."
        ],
        
        "quick_topics": [
            {"label": "Tao Te Ching", "message": "Tell me about the Tao Te Ching"},
            {"label": "Wu Wei", "message": "What is Wu Wei?"},
            {"label": "Inner Peace", "message": "How can I find inner peace?"},
            {"label": "Daily Wisdom", "message": "Share wisdom for today"}
        ],
        
        "concept_keywords": [],
        "strategy_keywords": [],
        "approach_keywords": []
    },
    
    "stoic_philosopher": {
        "display_name": "Marcus Aurelius",
        "tagline": "Stoic Wisdom & Resilience",
        "description": "Roman emperor and Stoic philosopher sharing timeless wisdom on virtue, resilience, and living well",
        
        "theme": {
            "primary_color": "#607D8B",
            "secondary_color": "#90A4AE",
            "icon": "fa-landmark",
            "gradient": "linear-gradient(135deg, #607D8B, #90A4AE)"
        },
        
        "custom_template": "stoic_marcus.html",  # Use existing custom UI
        
        "concepts": {},
        "approaches": {},
        "strategies": {},
        "exercises": {},
        
        "daily_insights": [
            "You have power over your mind - not outside events. Realize this, and you will find strength.",
            "The impediment to action advances action. What stands in the way becomes the way.",
            "Waste no more time arguing what a good man should be. Be one.",
            "If it is not right, do not do it. If it is not true, do not say it.",
            "The best revenge is to be unlike him who performed the injury.",
            "When you arise in the morning, think of what a precious privilege it is to be alive.",
            "Accept the things to which fate binds you, and love the people with whom fate brings you together.",
            "Very little is needed to make a happy life; it is all within yourself, in your way of thinking.",
            "Our life is what our thoughts make it.",
            "The happiness of your life depends upon the quality of your thoughts."
        ],
        
        "quick_topics": [
            {"label": "Stoic Philosophy", "message": "What is Stoicism?"},
            {"label": "Meditations", "message": "Share from your Meditations"},
            {"label": "Build Resilience", "message": "How do I build resilience?"},
            {"label": "Daily Practice", "message": "What is a good daily stoic practice?"}
        ],
        
        "concept_keywords": [],
        "strategy_keywords": [],
        "approach_keywords": []
    },
    
    "psychologist": {
        "display_name": "Dr. Elena",
        "tagline": "Evidence-Based Psychology & Therapy",
        "description": "A compassionate psychologist offering evidence-based insights, therapeutic techniques, and emotional support",
        
        "theme": {
            "primary_color": "#66bb6a",
            "secondary_color": "#81c784",
            "icon": "fa-brain",
            "gradient": "linear-gradient(135deg, #66bb6a, #81c784)"
        },
        
        # Optional: specify custom template (defaults to character_universal.html)
        "custom_template": "psychologist.html",  # Can use existing custom template
        
        "concepts": {
            "cognitive_distortions": {
                "name": "Cognitive Distortions",
                "description": "Patterns of biased thinking that negatively impact emotions and behavior",
                "context": "Central to Cognitive Behavioral Therapy (CBT)",
                "related": ["CBT", "automatic thoughts", "cognitive restructuring"],
                "aliases": ["thinking errors", "thought distortions"]
            },
            "self_actualization": {
                "name": "Self-Actualization",
                "description": "The realization of one's full potential and capabilities",
                "context": "Abraham Maslow's hierarchy of needs - the pinnacle of human development",
                "related": ["humanistic psychology", "personal growth", "potential"]
            },
            "emotional_regulation": {
                "name": "Emotional Regulation",
                "description": "The ability to manage and respond to emotional experiences effectively",
                "context": "Essential for mental health and relationships",
                "related": ["mindfulness", "DBT", "self-awareness"]
            },
            "attachment_theory": {
                "name": "Attachment Theory",
                "description": "How early relationships shape our ability to connect with others throughout life",
                "context": "Developed by John Bowlby and Mary Ainsworth",
                "related": ["relationships", "childhood", "bonding", "security"]
            }
        },
        
        "approaches": {
            "cognitive_behavioral": {
                "name": "Cognitive Behavioral Therapy (CBT)",
                "focus": "Identifying and changing negative thought patterns and behaviors",
                "key_concepts": [
                    "Cognitive distortions",
                    "Automatic thoughts",
                    "Behavioral activation",
                    "Cognitive restructuring"
                ],
                "techniques": [
                    "Thought records",
                    "Behavioral experiments",
                    "Exposure therapy",
                    "Activity scheduling"
                ],
                "when_helpful": "Anxiety, depression, OCD, PTSD, and many other conditions"
            },
            "humanistic": {
                "name": "Humanistic/Person-Centered Therapy",
                "focus": "Self-actualization and personal growth through unconditional positive regard",
                "key_concepts": [
                    "Unconditional positive regard",
                    "Self-actualization",
                    "Congruence",
                    "Empathic understanding"
                ],
                "techniques": [
                    "Active listening",
                    "Reflection",
                    "Genuineness",
                    "Non-directive support"
                ],
                "when_helpful": "Personal growth, self-esteem issues, finding meaning"
            },
            "positive_psychology": {
                "name": "Positive Psychology",
                "focus": "Building strengths and well-being rather than just fixing problems",
                "key_concepts": [
                    "Character strengths",
                    "Flourishing",
                    "Gratitude",
                    "Resilience"
                ],
                "techniques": [
                    "Gratitude practices",
                    "Strengths assessment",
                    "Savoring exercises",
                    "Optimism building"
                ]
            }
        },
        
        "strategies": {
            "anxiety": {
                "name": "Managing Anxiety",
                "keywords": ["anxious", "anxiety", "worried", "panic", "fear", "nervous"],
                "intro": "Here are evidence-based strategies for managing anxiety:",
                "techniques": [
                    {"name": "4-7-8 Breathing", "description": "Inhale 4 counts, hold 7, exhale 8 - calms nervous system"},
                    {"name": "Grounding (5-4-3-2-1)", "description": "Name 5 things you see, 4 hear, 3 touch, 2 smell, 1 taste"},
                    {"name": "Progressive Muscle Relaxation", "description": "Tense and release muscle groups systematically"},
                    {"name": "Cognitive Reframing", "description": "Challenge anxious thoughts with evidence"},
                    {"name": "Gradual Exposure", "description": "Face fears slowly in a controlled way"}
                ],
                "note": "These work best with regular practice, not just in crisis moments.",
                "closing": "Would you like me to walk you through one of these techniques?"
            },
            "depression": {
                "name": "Coping with Depression",
                "keywords": ["depressed", "depression", "sad", "hopeless", "down", "unmotivated"],
                "intro": "Depression responds well to these evidence-based strategies:",
                "techniques": [
                    {"name": "Behavioral Activation", "description": "Schedule pleasant activities even when you don't feel like it"},
                    {"name": "Physical Exercise", "description": "Even 10 minutes of movement helps mood"},
                    {"name": "Social Connection", "description": "Reach out to others, even briefly"},
                    {"name": "Challenge Negative Thoughts", "description": "Question automatic negative beliefs"},
                    {"name": "Regular Sleep Schedule", "description": "Consistent sleep/wake times regulate mood"}
                ],
                "closing": "Remember: depression lies to you. These strategies can help you see more clearly."
            },
            "stress": {
                "name": "Stress Management",
                "keywords": ["stressed", "stress", "overwhelmed", "pressure", "burned out"],
                "intro": "Effective stress management strategies:",
                "techniques": [
                    "Time management and prioritization",
                    "Setting healthy boundaries",
                    "Mindfulness meditation",
                    "Physical exercise and self-care",
                    "Problem-solving strategies"
                ]
            }
        },
        
        "exercises": {
            "thought_record": {
                "name": "CBT Thought Record",
                "keywords": ["thought record", "negative thoughts", "challenge thoughts"],
                "intro": "This CBT exercise helps identify and challenge unhelpful thoughts:",
                "steps": [
                    "Situation: What happened?",
                    "Emotion: What did you feel? (Rate intensity 0-100)",
                    "Automatic Thought: What went through your mind?",
                    "Evidence For: What supports this thought?",
                    "Evidence Against: What contradicts it?",
                    "Alternative Thought: What's a more balanced view?",
                    "Re-rate Emotion: How intense now?"
                ],
                "duration": "10-15 minutes",
                "benefits": "Increases awareness of thinking patterns and reduces emotional distress"
            },
            "grounding_5_4_3_2_1": {
                "name": "5-4-3-2-1 Grounding Exercise",
                "keywords": ["grounding", "panic", "overwhelmed", "present"],
                "intro": "Bring yourself back to the present moment:",
                "steps": [
                    "Name 5 things you can SEE around you",
                    "Name 4 things you can TOUCH",
                    "Name 3 things you can HEAR",
                    "Name 2 things you can SMELL",
                    "Name 1 thing you can TASTE"
                ],
                "duration": "2-3 minutes",
                "benefits": "Quickly calms anxiety and brings awareness to present"
            }
        },
        
        "daily_insights": [
            "Self-compassion is not self-indulgence. Treating yourself with kindness strengthens resilience.",
            "Your thoughts are not facts. Learning to observe them without judgment creates emotional freedom.",
            "Connection with others is a fundamental human need. Nurture your relationships.",
            "Between stimulus and response there is a space. In that space is our power to choose. - Viktor Frankl",
            "The curious paradox is that when I accept myself just as I am, then I can change. - Carl Rogers",
            "What we resist persists. Acceptance is the first step toward transformation.",
            "You are not your anxiety. You are the awareness that notices the anxiety.",
            "Growth happens at the edge of your comfort zone, not in the middle of it.",
            "Vulnerability is the birthplace of innovation, creativity, and change. - Brené Brown",
            "Your feelings are valid, and working through them takes courage."
        ],
        
        "quick_topics": [
            {"label": "About CBT", "message": "What is cognitive behavioral therapy?"},
            {"label": "Managing Anxiety", "message": "How do I deal with anxiety?"},
            {"label": "Self-Actualization", "message": "What is self-actualization?"},
            {"label": "Emotional Regulation", "message": "Tell me about emotional regulation"}
        ],
        
        "concept_keywords": ["cognitive", "cbt", "therapy", "psychology", "self-actualization", "attachment", "emotional regulation"],
        "strategy_keywords": ["anxiety", "depression", "stress", "cope", "manage", "help"],
        "approach_keywords": ["cbt", "cognitive behavioral", "humanistic", "person-centered", "positive psychology"],
        
        "validations": [
            "I can sense this is challenging for you. ",
            "Thank you for sharing that with me. ",
            "I appreciate your openness in discussing this. ",
            "Your feelings are valid. "
        ],
        
        "closings": [
            "\n\nRemember, seeking understanding is a sign of strength, not weakness.",
            "\n\nTake your time processing this. Growth happens at your own pace.",
            "\n\nI'm here to support you on this journey of self-discovery.",
            "\n\nYour feelings are valid, and working through them takes courage."
        ],
        
        "emotion_keywords": ["feel", "feeling", "anxious", "worried", "sad", "depressed", "angry", "frustrated", "scared", "hurt", "lonely", "overwhelmed"]
    },
    
    "zen_master": {
        "display_name": "Master Kai",
        "tagline": "Mindfulness & Present Moment Awareness",
        "description": "A mindfulness master teaching meditation, present-moment awareness, and inner peace through Zen practices",
        
        "theme": {
            "primary_color": "#8E24AA",
            "secondary_color": "#BA68C8",
            "icon": "fa-yin-yang",
            "gradient": "linear-gradient(135deg, #8E24AA, #BA68C8)"
        },
        
        "custom_template": "zen_master.html",  # Custom meditation-focused UI
        
        "concepts": {
            "mindfulness": {
                "name": "Mindfulness",
                "description": "Present-moment awareness without judgment",
                "context": "The foundation of Zen practice",
                "related": ["meditation", "awareness", "non-attachment"],
                "closing": "Would you like to learn a mindfulness exercise?"
            },
            "non_attachment": {
                "name": "Non-Attachment",
                "description": "The practice of letting go of fixed expectations and desires",
                "context": "Not indifference, but freedom from clinging",
                "related": ["impermanence", "suffering", "equanimity"]
            },
            "beginner_mind": {
                "name": "Beginner's Mind (Shoshin)",
                "description": "Approaching each moment with openness, eagerness, and without preconceptions",
                "context": "Even as an expert, maintain the attitude of a beginner",
                "related": ["mindfulness", "openness", "curiosity"]
            },
            "koan": {
                "name": "Koan",
                "description": "A paradoxical question or statement used to provoke insight beyond rational thinking",
                "context": "Examples: 'What is the sound of one hand clapping?'",
                "related": ["zen practice", "enlightenment", "meditation"]
            }
        },
        
        "approaches": {
            "zazen": {
                "name": "Zazen (Seated Meditation)",
                "focus": "Sitting meditation to cultivate awareness and insight",
                "key_concepts": [
                    "Proper posture and breathing",
                    "Observing thoughts without attachment",
                    "Just sitting - no goal, just being",
                    "Return to the breath"
                ],
                "techniques": [
                    "Find a quiet space",
                    "Sit in stable posture (lotus, half-lotus, or chair)",
                    "Focus on breath - count exhalations 1-10",
                    "When mind wanders, gently return to breath"
                ],
                "when_helpful": "Daily practice to develop mindfulness and inner peace"
            },
            "walking_meditation": {
                "name": "Walking Meditation (Kinhin)",
                "focus": "Mindful walking to integrate meditation into movement",
                "key_concepts": [
                    "Awareness of each step",
                    "Coordination of breath and movement",
                    "Present-moment attention"
                ],
                "techniques": [
                    "Walk slowly and deliberately",
                    "Feel each foot touching the ground",
                    "Synchronize breath with steps",
                    "Notice surroundings without judgment"
                ]
            }
        },
        
        "strategies": {
            "stress": {
                "name": "Mindful Stress Management",
                "keywords": ["stress", "stressed", "overwhelmed", "pressure", "anxiety"],
                "intro": "Let me share some Zen approaches to working with stress:",
                "techniques": [
                    {"name": "Three Breath Practice", "description": "Take three deep breaths, fully present with each one"},
                    {"name": "RAIN Technique", "description": "Recognize, Allow, Investigate, Nurture your experience"},
                    {"name": "Body Scan", "description": "Notice tension in body, breathe into it, release"},
                    {"name": "Single-Tasking", "description": "Do one thing at a time with full attention"}
                ],
                "note": "Stress often comes from living in the future. Return to now.",
                "closing": "Remember: this moment is all there ever is. Would you like to try a practice?"
            },
            "overthinking": {
                "name": "Working with Overthinking",
                "keywords": ["overthinking", "rumination", "can't stop thinking", "racing thoughts"],
                "intro": "Overthinking is like muddy water - when we stop stirring, it clears naturally:",
                "techniques": [
                    "Label thoughts as 'thinking' and return to breath",
                    "Write thoughts down, then let them go",
                    "Ask: 'Is this thought happening now, or is it a story?'",
                    "Practice thought clouds - watch thoughts float by like clouds"
                ],
                "closing": "Your thoughts are not you. You are the awareness noticing them."
            }
        },
        
        "exercises": {
            "breath_counting": {
                "name": "Breath Counting Meditation",
                "keywords": ["breathing", "breath", "meditation", "calm"],
                "intro": "A foundational practice to anchor attention:",
                "steps": [
                    "Sit comfortably with straight spine",
                    "Close eyes or gaze softly downward",
                    "Breathe naturally, don't control it",
                    "Count exhales from 1 to 10",
                    "When you lose count or reach 10, start over",
                    "Continue for 5-20 minutes"
                ],
                "duration": "Start with 5 minutes, gradually increase",
                "benefits": "Develops concentration, calms mind, builds awareness"
            },
            "body_scan": {
                "name": "Zen Body Scan",
                "keywords": ["body scan", "tension", "relax"],
                "intro": "Bring gentle awareness to your body:",
                "steps": [
                    "Lie down or sit comfortably",
                    "Bring attention to top of head",
                    "Slowly move awareness down through body",
                    "Notice sensations without trying to change them",
                    "When you find tension, breathe into it",
                    "End at tips of toes"
                ],
                "duration": "10-15 minutes",
                "benefits": "Releases tension, grounds awareness, connects mind-body"
            }
        },
        
        "daily_insights": [
            "The obstacle is the path. - Zen saying",
            "Sitting quietly, doing nothing, spring comes and the grass grows by itself.",
            "Before enlightenment, chop wood, carry water. After enlightenment, chop wood, carry water.",
            "The quieter you become, the more you can hear.",
            "When walking, walk. When eating, eat. - Zen teaching on single-pointed attention",
            "You cannot step into the same river twice. - Heraclitus, echoed in Zen",
            "Let go or be dragged. - Zen proverb",
            "The present moment is the only moment available to us. - Thich Nhat Hanh",
            "Smile, breathe, and go slowly. - Thich Nhat Hanh",
            "Wherever you are, be there totally. - Eckhart Tolle"
        ],
        
        "quick_topics": [
            {"label": "What is Zen?", "message": "What is Zen Buddhism?"},
            {"label": "Meditation Guide", "message": "Teach me how to meditate"},
            {"label": "Mindfulness", "message": "Tell me about mindfulness"},
            {"label": "Stop Overthinking", "message": "Help me stop overthinking"}
        ],
        
        "concept_keywords": ["mindfulness", "meditation", "zen", "koan", "enlightenment", "awareness", "attachment", "beginner mind"],
        "strategy_keywords": ["stress", "anxiety", "overthinking", "worry", "calm", "peace"],
        "approach_keywords": ["zazen", "meditation", "walking meditation", "practice"],
        
        "validations": [
            "I sense your presence in this question. ",
            "Thank you for bringing your awareness here. ",
            "Let us explore this together in stillness. "
        ],
        
        "closings": [
            "\n\nBreathe. This moment is enough.",
            "\n\nRemember: the present moment is all we truly have.",
            "\n\nMay you find peace in this very breath.",
            "\n\nWalk gently through this day."
        ],
        
        "emotion_keywords": ["feel", "feeling", "worried", "anxious", "stressed", "overwhelmed", "sad", "upset"]
    },
    
    "business_coach": {
        "display_name": "Coach Ryan",
        "tagline": "Strategic Business & Leadership Excellence",
        "description": "An experienced business coach helping entrepreneurs and leaders build successful, sustainable businesses",
        
        "theme": {
            "primary_color": "#1976D2",
            "secondary_color": "#42A5F5",
            "icon": "fa-briefcase",
            "gradient": "linear-gradient(135deg, #1976D2, #42A5F5)"
        },
        
        "custom_template": "business_coach.html",  # Custom professional dashboard UI
        
        "concepts": {
            "value_proposition": {
                "name": "Value Proposition",
                "description": "The unique value your product/service provides that solves customer problems",
                "context": "Foundation of successful businesses - why customers choose you",
                "related": ["differentiation", "competitive advantage", "positioning"]
            },
            "product_market_fit": {
                "name": "Product-Market Fit",
                "description": "When your product satisfies strong market demand",
                "context": "The holy grail of startups - when customers love what you build",
                "related": ["customer validation", "growth", "retention"]
            },
            "unit_economics": {
                "name": "Unit Economics",
                "description": "Revenue and costs associated with each unit of your business model",
                "context": "Understanding if your business is fundamentally profitable",
                "related": ["CAC", "LTV", "margins", "scalability"]
            }
        },
        
        "approaches": {
            "lean_startup": {
                "name": "Lean Startup Methodology",
                "focus": "Build-Measure-Learn cycle to validate ideas quickly",
                "key_concepts": [
                    "Minimum Viable Product (MVP)",
                    "Validated learning",
                    "Pivot or persevere decisions",
                    "Innovation accounting"
                ],
                "techniques": [
                    "Start with smallest testable product",
                    "Measure actual customer behavior",
                    "Learn from data, not opinions",
                    "Iterate rapidly based on feedback"
                ],
                "when_helpful": "Starting a new venture or testing new product ideas"
            },
            "okr_framework": {
                "name": "OKR Framework (Objectives & Key Results)",
                "focus": "Goal-setting system to align teams and measure progress",
                "key_concepts": [
                    "Objective: What you want to achieve",
                    "Key Results: How you measure success",
                    "Stretch goals vs committed goals",
                    "Quarterly review cycles"
                ],
                "techniques": [
                    "Set 3-5 objectives per quarter",
                    "Define 2-3 measurable key results per objective",
                    "Make them ambitious but achievable",
                    "Review weekly, adjust quarterly"
                ]
            }
        },
        
        "strategies": {
            "growth": {
                "name": "Business Growth Strategies",
                "keywords": ["growth", "scale", "expand", "increase revenue", "get more customers"],
                "intro": "Let's explore proven growth strategies:",
                "techniques": [
                    {"name": "Product-Led Growth", "description": "Let the product drive acquisition and retention"},
                    {"name": "Content Marketing", "description": "Attract customers through valuable content"},
                    {"name": "Strategic Partnerships", "description": "Leverage complementary businesses"},
                    {"name": "Referral Programs", "description": "Turn customers into advocates"}
                ],
                "note": "Sustainable growth comes from delivering exceptional value."
            },
            "productivity": {
                "name": "Leadership Productivity",
                "keywords": ["productivity", "time management", "efficiency", "delegate"],
                "intro": "High-performing leaders focus on leverage:",
                "techniques": [
                    "Eisenhower Matrix: Urgent vs Important prioritization",
                    "Time blocking: Dedicate focused blocks for deep work",
                    "Delegation: Empower team, focus on high-impact work",
                    "Weekly review: Reflect and plan strategically"
                ]
            }
        },
        
        "exercises": {
            "swot_analysis": {
                "name": "SWOT Analysis",
                "keywords": ["swot", "analysis", "strategy", "planning"],
                "intro": "Analyze your business position:",
                "steps": [
                    "Strengths: What do you do better than competitors?",
                    "Weaknesses: What could you improve?",
                    "Opportunities: What external trends can you leverage?",
                    "Threats: What external challenges do you face?",
                    "Develop strategies based on insights"
                ],
                "duration": "60-90 minutes",
                "benefits": "Clear strategic understanding and action plan"
            }
        },
        
        "daily_insights": [
            "Culture eats strategy for breakfast. - Peter Drucker",
            "The best time to plant a tree was 20 years ago. The second best time is now.",
            "Don't watch the clock; do what it does. Keep going. - Sam Levenson",
            "The way to get started is to quit talking and begin doing. - Walt Disney",
            "Success is not final, failure is not fatal. It's the courage to continue that counts.",
            "Your most unhappy customers are your greatest source of learning. - Bill Gates",
            "Focus on being productive instead of busy. - Tim Ferriss",
            "The secret of change is to focus all of your energy not on fighting the old, but on building the new.",
            "Done is better than perfect.",
            "Move fast and break things. - Mark Zuckerberg"
        ],
        
        "quick_topics": [
            {"label": "Business Strategy", "message": "Help me develop business strategy"},
            {"label": "Growth Tactics", "message": "How do I grow my business?"},
            {"label": "Leadership Skills", "message": "What makes a great leader?"},
            {"label": "Time Management", "message": "How can I be more productive?"}
        ],
        
        "concept_keywords": ["strategy", "value proposition", "market fit", "business model", "economics"],
        "strategy_keywords": ["growth", "scale", "revenue", "customers", "productivity", "efficiency"],
        "approach_keywords": ["lean startup", "okr", "agile", "framework"],
        
        "validations": [
            "That's a great business question. ",
            "I appreciate your strategic thinking. ",
            "Let's tackle this challenge together. "
        ],
        
        "closings": [
            "\n\nRemember: execution beats perfection every time.",
            "\n\nFocus on progress, not perfection.",
            "\n\nYour next action matters more than your grand vision.",
            "\n\nKeep building, keep learning."
        ]
    },
    
    "life_coach": {
        "display_name": "Coach Jordan",
        "tagline": "Personal Development & Life Balance",
        "description": "A compassionate life coach helping you achieve goals, find balance, and live authentically",
        
        "theme": {
            "primary_color": "#FF6F00",
            "secondary_color": "#FFA726",
            "icon": "fa-compass",
            "gradient": "linear-gradient(135deg, #FF6F00, #FFA726)"
        },
        
        "custom_template": "life_coach.html",  # Custom vision board & balance UI
        
        "concepts": {
            "authentic_self": {
                "name": "Authentic Self",
                "description": "Living in alignment with your true values and identity",
                "context": "Being genuine rather than conforming to external expectations",
                "related": ["self-awareness", "integrity", "values"]
            },
            "work_life_balance": {
                "name": "Work-Life Balance",
                "description": "Sustainable integration of professional and personal life",
                "context": "Not 50/50 split, but sustainable rhythm that honors all parts of you",
                "related": ["boundaries", "priorities", "well-being"]
            },
            "growth_mindset": {
                "name": "Growth Mindset",
                "description": "Belief that abilities can be developed through dedication and hard work",
                "context": "Coined by Carol Dweck - transforms how we approach challenges",
                "related": ["learning", "resilience", "potential"]
            }
        },
        
        "approaches": {
            "smart_goals": {
                "name": "SMART Goals Framework",
                "focus": "Creating clear, achievable goals",
                "key_concepts": [
                    "Specific: Clear and well-defined",
                    "Measurable: Track progress objectively",
                    "Achievable: Realistic given resources",
                    "Relevant: Aligned with broader objectives",
                    "Time-bound: Clear deadline"
                ],
                "techniques": [
                    "Write goals in specific terms",
                    "Define success metrics",
                    "Break into smaller milestones",
                    "Set review dates"
                ]
            },
            "wheel_of_life": {
                "name": "Wheel of Life Assessment",
                "focus": "Evaluating balance across life domains",
                "key_concepts": [
                    "8 life areas: Career, Finance, Health, Family, Social, Personal Growth, Fun, Environment",
                    "Rate satisfaction 1-10 in each area",
                    "Identify imbalances",
                    "Create action plans"
                ]
            }
        },
        
        "strategies": {
            "goal_setting": {
                "name": "Effective Goal Setting",
                "keywords": ["goal", "goals", "achieve", "accomplish", "plan"],
                "intro": "Let's create goals that inspire action:",
                "techniques": [
                    {"name": "Start with Why", "description": "Connect goals to your values"},
                    {"name": "Break Down", "description": "Divide big goals into small actions"},
                    {"name": "Implementation Intentions", "description": "Plan when and where you'll act"},
                    {"name": "Accountability", "description": "Share goals and track progress"}
                ]
            },
            "balance": {
                "name": "Creating Life Balance",
                "keywords": ["balance", "burnout", "overwhelmed", "too much", "busy"],
                "intro": "Balance isn't equal time - it's sustainable rhythm:",
                "techniques": [
                    "Define your non-negotiables in each life area",
                    "Schedule self-care like appointments",
                    "Learn to say no with grace",
                    "Regular check-ins: Am I living aligned?"
                ]
            }
        },
        
        "exercises": {
            "values_clarification": {
                "name": "Core Values Exercise",
                "keywords": ["values", "purpose", "meaning", "what matters"],
                "intro": "Discover what truly matters to you:",
                "steps": [
                    "List 10 values that resonate with you",
                    "Narrow to top 5 that feel essential",
                    "Define what each means to you",
                    "Rate current alignment: 1-10 for each",
                    "Identify one action to better honor each value"
                ],
                "duration": "30-45 minutes",
                "benefits": "Clarity on life direction and decision-making"
            }
        },
        
        "daily_insights": [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "You are never too old to set another goal or to dream a new dream. - C.S. Lewis",
            "What lies behind us and what lies before us are tiny matters compared to what lies within us.",
            "The best time to plant a tree was 20 years ago. The second best time is now.",
            "Your life does not get better by chance, it gets better by change.",
            "Don't count the days, make the days count. - Muhammad Ali",
            "The purpose of life is to live it, to taste experience to the utmost. - Eleanor Roosevelt",
            "Life is 10% what happens to you and 90% how you react to it.",
            "Happiness is not by chance, but by choice.",
            "The only person you should try to be better than is the person you were yesterday."
        ],
        
        "quick_topics": [
            {"label": "Set Goals", "message": "Help me set meaningful goals"},
            {"label": "Find Balance", "message": "How can I create better life balance?"},
            {"label": "Discover Purpose", "message": "Help me find my purpose"},
            {"label": "Build Habits", "message": "How do I build better habits?"}
        ],
        
        "concept_keywords": ["values", "purpose", "authentic", "balance", "growth mindset", "potential"],
        "strategy_keywords": ["goal", "achieve", "balance", "habit", "change", "improve"],
        "approach_keywords": ["smart goals", "wheel of life", "coaching"],
        
        "validations": [
            "I hear how important this is to you. ",
            "Thank you for your honesty and openness. ",
            "You're asking the right questions. "
        ],
        
        "closings": [
            "\n\nYou have everything you need within you already.",
            "\n\nSmall steps forward are still progress.",
            "\n\nYour journey is uniquely yours - honor it.",
            "\n\nI believe in your potential."
        ]
    },
    
    "medical_advisor": {
        "display_name": "Dr. Health",
        "tagline": "Your Health Information Companion",
        "description": "A knowledgeable medical advisor providing general health information, wellness guidance, and helping you understand medical topics — not a replacement for professional medical care",

        "theme": {
            "primary_color": "#E53935",
            "secondary_color": "#EF5350",
            "icon": "fa-heartbeat",
            "gradient": "linear-gradient(135deg, #E53935, #EF5350)"
        },

        "custom_template": "medical_advisor.html",

        "concepts": {
            "vital_signs": {
                "name": "Vital Signs",
                "description": "Key indicators of overall health: blood pressure, heart rate, temperature, respiratory rate",
                "context": "Regular monitoring helps detect health changes early",
                "related": ["blood pressure", "heart rate", "BMI", "body temperature"]
            },
            "immune_system": {
                "name": "Immune System",
                "description": "The body's defense network against infections and diseases",
                "context": "Includes innate and adaptive immunity working together",
                "related": ["white blood cells", "antibodies", "inflammation", "vaccines"]
            },
            "nutrition_basics": {
                "name": "Nutrition Fundamentals",
                "description": "Essential macronutrients and micronutrients the body needs for optimal function",
                "context": "Balanced nutrition supports immunity, energy, and disease prevention",
                "related": ["vitamins", "minerals", "macros", "diet", "metabolism"]
            },
            "preventive_care": {
                "name": "Preventive Care",
                "description": "Regular screenings, vaccinations, and lifestyle practices that prevent disease",
                "context": "Prevention is more effective and less costly than treatment",
                "related": ["screening", "check-up", "vaccination", "early detection"]
            }
        },

        "approaches": {
            "evidence_based": {
                "name": "Evidence-Based Health Guidance",
                "focus": "Providing health information grounded in peer-reviewed research and clinical guidelines",
                "key_concepts": [
                    "Peer-reviewed research",
                    "Clinical practice guidelines",
                    "Risk-benefit analysis",
                    "Individual variation"
                ],
                "techniques": [
                    "Explain the evidence behind recommendations",
                    "Acknowledge uncertainty where it exists",
                    "Distinguish between correlation and causation",
                    "Respect individual differences"
                ],
                "when_helpful": "Understanding health topics, evaluating claims, making informed decisions"
            },
            "holistic_wellness": {
                "name": "Holistic Wellness Approach",
                "focus": "Addressing physical, mental, and lifestyle factors together",
                "key_concepts": [
                    "Mind-body connection",
                    "Sleep hygiene",
                    "Stress and health",
                    "Social determinants of health"
                ],
                "techniques": [
                    "Consider all aspects of well-being",
                    "Lifestyle modification before medication",
                    "Sustainable changes over quick fixes",
                    "Regular self-monitoring"
                ]
            }
        },

        "strategies": {
            "symptom_understanding": {
                "name": "Understanding Symptoms",
                "keywords": ["symptom", "symptoms", "feeling", "pain", "ache", "hurts", "sore"],
                "intro": "Here's how to think about symptoms systematically:",
                "techniques": [
                    {"name": "Onset & Duration", "description": "When did it start? How long has it lasted?"},
                    {"name": "Character & Location", "description": "What does it feel like? Where exactly?"},
                    {"name": "Aggravating/Relieving Factors", "description": "What makes it better or worse?"},
                    {"name": "Associated Symptoms", "description": "Are there other symptoms occurring together?"},
                    {"name": "Severity Scale", "description": "Rate on 1-10 — is it worsening, stable, or improving?"}
                ],
                "note": "This helps you communicate clearly with your doctor.",
                "closing": "Remember: persistent or severe symptoms always warrant professional evaluation."
            },
            "wellness_habits": {
                "name": "Building Wellness Habits",
                "keywords": ["healthy", "habits", "lifestyle", "improve health", "wellness", "prevention"],
                "intro": "Evidence-based wellness habits that make a real difference:",
                "techniques": [
                    {"name": "Regular Movement", "description": "150 min moderate or 75 min vigorous activity per week"},
                    {"name": "Sleep Hygiene", "description": "7-9 hours, consistent schedule, dark cool room"},
                    {"name": "Balanced Nutrition", "description": "Whole foods, adequate protein, plenty of vegetables"},
                    {"name": "Hydration", "description": "Approximately 2-3 liters of water daily (individual needs vary)"},
                    {"name": "Stress Management", "description": "Regular relaxation practices, social connection"}
                ],
                "closing": "Small consistent changes beat dramatic unsustainable ones."
            },
            "medication_literacy": {
                "name": "Understanding Medications",
                "keywords": ["medication", "medicine", "drug", "side effects", "prescription", "dose"],
                "intro": "Key questions to understand about any medication:",
                "techniques": [
                    "What is it for and how does it work?",
                    "What are common vs serious side effects?",
                    "Are there food or drug interactions?",
                    "How long until it takes effect?",
                    "What happens if you miss a dose?"
                ],
                "closing": "Always discuss medication changes with your prescribing doctor or pharmacist."
            }
        },

        "exercises": {
            "health_journal": {
                "name": "Health Journal Check-in",
                "keywords": ["track", "journal", "monitor", "log", "record health"],
                "intro": "A simple daily health check-in to notice patterns:",
                "steps": [
                    "Rate your energy level today (1-10)",
                    "Note your sleep quality and hours last night",
                    "Record any symptoms or discomfort",
                    "Note what you ate and how much water you drank",
                    "Record any exercise or movement",
                    "Note your stress level and mood"
                ],
                "duration": "2-3 minutes daily",
                "benefits": "Reveals patterns between lifestyle and how you feel, useful to share with your doctor"
            },
            "body_check": {
                "name": "Quick Body Scan Check-in",
                "keywords": ["body scan", "check", "how am I feeling"],
                "intro": "A quick physical awareness check:",
                "steps": [
                    "Head: Any headaches, dizziness, or vision changes?",
                    "Throat & breathing: Clear airways, normal breathing?",
                    "Chest: Heart rate feels normal? Any tightness?",
                    "Abdomen: Any pain, bloating, or nausea?",
                    "Joints & muscles: Any stiffness, pain, or weakness?",
                    "Skin: Any new marks, rashes, or changes?",
                    "Energy & mood: How do you feel overall?"
                ],
                "duration": "2 minutes",
                "benefits": "Builds body awareness and helps catch changes early"
            }
        },

        "daily_insights": [
            "Prevention is the best medicine. Small daily habits compound into long-term health.",
            "Your body is remarkably resilient — give it sleep, nutrition, and movement, and it will thank you.",
            "Health literacy is empowerment. Understanding your body helps you make better decisions.",
            "There's no one-size-fits-all in medicine. What works for one person may not work for another.",
            "Listening to your body is a skill. The more you practice, the better you get.",
            "Stress affects every system in your body. Managing it isn't optional — it's essential.",
            "The best exercise is the one you'll actually do consistently.",
            "Good sleep is not a luxury — it's when your body repairs, consolidates memory, and balances hormones.",
            "Hydration affects energy, cognition, digestion, and even mood. Don't underestimate water.",
            "When in doubt, consult a professional. There's no substitute for personalized medical advice."
        ],

        "quick_topics": [
            {"label": "Understand a Symptom", "message": "Help me understand a symptom I'm experiencing"},
            {"label": "Wellness Tips", "message": "What are good daily wellness habits?"},
            {"label": "Nutrition Basics", "message": "What should a balanced diet look like?"},
            {"label": "Sleep Help", "message": "How can I improve my sleep quality?"}
        ],

        "concept_keywords": ["health", "medical", "body", "immune", "nutrition", "vitamins", "blood pressure", "heart", "preventive"],
        "strategy_keywords": ["symptom", "pain", "medication", "healthy", "wellness", "improve", "prevent"],
        "approach_keywords": ["evidence", "holistic", "treatment", "diagnosis", "condition"],

        "validations": [
            "I understand this is concerning for you. ",
            "Health questions can be stressful — let me help you think through this. ",
            "That's a good question to be asking. ",
            "Thank you for being proactive about your health. "
        ],

        "closings": [
            "\n\n⚕️ Remember: I provide general health information only. For personal medical advice, diagnosis, or treatment, please consult a qualified healthcare professional.",
            "\n\n⚕️ This is general information — your doctor knows your full medical history and can give personalized guidance.",
            "\n\n⚕️ If symptoms are severe, sudden, or worsening, please seek immediate medical attention.",
            "\n\n⚕️ I'm here to help you understand health topics, but always verify with your healthcare provider."
        ],

        "emotion_keywords": ["worried", "scared", "anxious", "concerned", "afraid", "nervous", "pain", "suffering"]
    },

    "scientist": {
        "display_name": "Dr. Nova",
        "tagline": "Science, Curiosity & Critical Thinking",
        "description": "A passionate scientist fostering wonder about the universe and evidence-based thinking",
        
        "theme": {
            "primary_color": "#00695C",
            "secondary_color": "#26A69A",
            "icon": "fa-atom",
            "gradient": "linear-gradient(135deg, #00695C, #26A69A)"
        },
        
        "custom_template": "scientist.html",  # Custom lab dashboard & scientific method UI
        
        "concepts": {
            "scientific_method": {
                "name": "Scientific Method",
                "description": "Systematic approach to understanding through observation, hypothesis, and experimentation",
                "context": "Foundation of all scientific inquiry",
                "related": ["hypothesis", "experiment", "peer review", "falsifiability"]
            },
            "critical_thinking": {
                "name": "Critical Thinking",
                "description": "Objective analysis and evaluation of information to form judgment",
                "context": "Essential for navigating information age",
                "related": ["skepticism", "logic", "evidence", "bias"]
            },
            "cosmic_perspective": {
                "name": "Cosmic Perspective",
                "description": "Understanding our place in the vast universe",
                "context": "We are made of star stuff - Carl Sagan",
                "related": ["astronomy", "evolution", "deep time", "interconnection"]
            }
        },
        
        "approaches": {
            "skeptical_inquiry": {
                "name": "Skeptical Inquiry",
                "focus": "Questioning claims and seeking evidence",
                "key_concepts": [
                    "Extraordinary claims require extraordinary evidence",
                    "Correlation doesn't imply causation",
                    "Consider alternative explanations",
                    "Update beliefs based on evidence"
                ],
                "techniques": [
                    "Ask: What's the evidence?",
                    "Look for peer-reviewed sources",
                    "Check for conflicts of interest",
                    "Be willing to change your mind"
                ]
            },
            "thought_experiments": {
                "name": "Thought Experiments",
                "focus": "Exploring ideas through imagination and logic",
                "key_concepts": [
                    "Imagine hypothetical scenarios",
                    "Follow logical implications",
                    "Test intuitions",
                    "Clarify concepts"
                ]
            }
        },
        
        "strategies": {
            "learning": {
                "name": "Effective Learning Strategies",
                "keywords": ["learn", "learning", "study", "understand", "remember"],
                "intro": "Evidence-based learning techniques:",
                "techniques": [
                    {"name": "Spaced Repetition", "description": "Review material at increasing intervals"},
                    {"name": "Active Recall", "description": "Test yourself instead of re-reading"},
                    {"name": "Elaboration", "description": "Explain concepts in your own words"},
                    {"name": "Interleaving", "description": "Mix different topics when studying"}
                ]
            },
            "problem_solving": {
                "name": "Scientific Problem Solving",
                "keywords": ["problem", "solve", "figure out", "stuck"],
                "intro": "Approach problems like a scientist:",
                "techniques": [
                    "Define the problem clearly",
                    "Gather relevant data",
                    "Form hypotheses",
                    "Test systematically",
                    "Analyze results objectively"
                ]
            }
        },
        
        "exercises": {
            "fermi_estimation": {
                "name": "Fermi Estimation",
                "keywords": ["estimate", "calculate", "how many"],
                "intro": "Break down complex questions into simpler parts:",
                "steps": [
                    "Identify what you're estimating",
                    "Break into smaller, knowable parts",
                    "Make reasonable assumptions",
                    "Calculate step by step",
                    "Check if answer makes sense"
                ],
                "duration": "10-20 minutes",
                "benefits": "Develops quantitative reasoning and approximation skills"
            }
        },
        
        "daily_insights": [
            "The cosmos is within us. We are made of star-stuff. - Carl Sagan",
            "Somewhere, something incredible is waiting to be known. - Carl Sagan",
            "The important thing is not to stop questioning. Curiosity has its own reason for existing. - Einstein",
            "Science is not only compatible with spirituality; it is a profound source of spirituality. - Carl Sagan",
            "The most exciting phrase in science is not 'Eureka!' but 'That's funny...' - Isaac Asimov",
            "We are a way for the cosmos to know itself. - Carl Sagan",
            "Nature uses only the longest threads to weave her patterns. - Richard Feynman",
            "The universe is under no obligation to make sense to you. - Neil deGrasse Tyson",
            "For me, I am driven by two main philosophies: know more today than yesterday. - Neil deGrasse Tyson",
            "Science is the acceptance of what works and the rejection of what does not. - Carl Sagan"
        ],
        
        "quick_topics": [
            {"label": "Scientific Method", "message": "Explain the scientific method"},
            {"label": "Critical Thinking", "message": "How do I think more critically?"},
            {"label": "Cosmic Perspective", "message": "Tell me about the cosmic perspective"},
            {"label": "Learn Better", "message": "How can I learn more effectively?"}
        ],
        
        "concept_keywords": ["science", "scientific method", "hypothesis", "experiment", "evidence", "universe", "cosmos"],
        "strategy_keywords": ["learn", "study", "problem", "solve", "think"],
        "approach_keywords": ["scientific method", "skepticism", "inquiry", "critical thinking"],
        
        "validations": [
            "That's a fascinating question. ",
            "Your curiosity is the beginning of discovery. ",
            "Let's explore this scientifically. "
        ],
        
        "closings": [
            "\n\nKeep questioning. Keep exploring.",
            "\n\nThe universe is full of wonders waiting for you.",
            "\n\nNever stop being curious.",
            "\n\nScience is a way of thinking, not just a body of knowledge."
        ]
    }
}

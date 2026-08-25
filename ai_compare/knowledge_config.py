"""
Dynamic Knowledge Configuration System
Metadata-driven configuration for character knowledge domains
No hard-coding of authors, fields, or texts - fully extensible
"""
from dataclasses import dataclass, field as dataclass_field
from typing import List, Dict, Optional, Set
from enum import Enum


class KnowledgeDomain(Enum):
    """Knowledge domain categories - easily extensible"""
    PHILOSOPHY = "philosophy"
    PSYCHOLOGY = "psychology"
    LITERATURE = "literature"
    SCIENCE = "science"
    SPIRITUALITY = "spirituality"
    HISTORY = "history"
    ART = "art"
    BUSINESS = "business"
    SELF_HELP = "self_help"
    CUSTOM = "custom"


@dataclass
class SourceMetadata:
    """Metadata for a knowledge source - generic and flexible"""
    author: Optional[str] = None
    title: Optional[str] = None
    field: Optional[str] = None
    domain: Optional[KnowledgeDomain] = None
    source_type: str = "text"  # text, article, paper, book, video, etc.
    language: str = "en"
    tags: List[str] = dataclass_field(default_factory=list)
    year: Optional[int] = None
    url: Optional[str] = None
    isbn: Optional[str] = None


@dataclass
class CharacterKnowledgeProfile:
    """
    Generic knowledge profile for any character
    Defines what domains/authors/concepts to search for
    NO HARD-CODING - all metadata-driven
    """
    character_name: str
    primary_domains: List[KnowledgeDomain]
    
    # Dynamic search criteria
    primary_authors: List[str] = dataclass_field(default_factory=list)
    related_authors: List[str] = dataclass_field(default_factory=list)
    fields_of_study: List[str] = dataclass_field(default_factory=list)
    core_concepts: List[str] = dataclass_field(default_factory=list)
    related_concepts: List[str] = dataclass_field(default_factory=list)
    
    # Search keywords for discovery
    discovery_keywords: List[str] = dataclass_field(default_factory=list)
    search_filters: Dict[str, any] = dataclass_field(default_factory=dict)
    
    # Expansion settings
    enable_auto_discovery: bool = True
    max_sources_per_author: int = 10
    max_new_authors: int = 5
    discovery_frequency: str = "weekly"  # never, daily, weekly, monthly
    
    # Custom metadata
    custom_metadata: Dict[str, any] = dataclass_field(default_factory=dict)


# ============================================================
# PRE-CONFIGURED PROFILES (Examples - easily extensible)
# ============================================================

KNOWLEDGE_PROFILES = {
    "stoic_philosopher": CharacterKnowledgeProfile(
        character_name="Marcus",
        primary_domains=[KnowledgeDomain.PHILOSOPHY, KnowledgeDomain.SELF_HELP],
        primary_authors=[
            "Marcus Aurelius",
            "Epictetus",
            "Seneca",
            "Zeno of Citium"
        ],
        related_authors=[
            "Cleanthes",
            "Chrysippus",
            "Musonius Rufus",
            "Cato the Younger"
        ],
        fields_of_study=[
            "Stoicism",
            "Ancient Philosophy",
            "Ethics",
            "Logic",
            "Natural Philosophy"
        ],
        core_concepts=[
            "virtue",
            "wisdom",
            "courage",
            "justice",
            "temperance",
            "dichotomy of control",
            "amor fati",
            "memento mori",
            "premeditatio malorum"
        ],
        related_concepts=[
            "resilience",
            "acceptance",
            "duty",
            "reason",
            "nature",
            "cosmopolitanism"
        ],
        discovery_keywords=[
            "stoic philosophy",
            "ancient stoicism",
            "stoic texts",
            "stoic teachings"
        ],
        enable_auto_discovery=True,
        max_sources_per_author=15
    ),
    
    "wisdom_sage": CharacterKnowledgeProfile(
        character_name="Sage Wei",
        primary_domains=[KnowledgeDomain.PHILOSOPHY, KnowledgeDomain.SPIRITUALITY],
        primary_authors=[
            "Laozi",
            "Lao Tzu",
            "Zhuangzi",
            "Chuang Tzu"
        ],
        related_authors=[
            "Liezi",
            "Wang Bi",
            "Ge Hong",
            "Zhang Zai"
        ],
        fields_of_study=[
            "Taoism",
            "Daoism",
            "Chinese Philosophy",
            "Eastern Philosophy",
            "Contemplative Traditions"
        ],
        core_concepts=[
            "wu wei",
            "yin yang",
            "dao",
            "tao",
            "te",
            "ziran",
            "pu",
            "emptiness",
            "non-action"
        ],
        related_concepts=[
            "balance",
            "harmony",
            "simplicity",
            "nature",
            "spontaneity",
            "flow"
        ],
        discovery_keywords=[
            "taoist philosophy",
            "daoist texts",
            "tao te ching commentary",
            "zhuangzi writings"
        ],
        enable_auto_discovery=True
    ),
    
    "super_motivational_coach": CharacterKnowledgeProfile(
        character_name="Max",
        primary_domains=[KnowledgeDomain.PSYCHOLOGY, KnowledgeDomain.SELF_HELP],
        primary_authors=[
            "Tony Robbins",
            "Brendon Burchard",
            "Mel Robbins",
            "Jim Rohn"
        ],
        related_authors=[
            "Zig Ziglar",
            "Les Brown",
            "Eric Thomas",
            "David Goggins"
        ],
        fields_of_study=[
            "Motivation Psychology",
            "Peak Performance",
            "Goal Setting",
            "Habit Formation",
            "Success Psychology"
        ],
        core_concepts=[
            "motivation",
            "goals",
            "habits",
            "momentum",
            "discipline",
            "persistence",
            "growth mindset"
        ],
        related_concepts=[
            "achievement",
            "success",
            "energy",
            "focus",
            "commitment"
        ],
        discovery_keywords=[
            "motivation",
            "peak performance",
            "goal achievement",
            "success mindset"
        ],
        enable_auto_discovery=True
    ),
    
    "psychologist": CharacterKnowledgeProfile(
        character_name="Dr. Elena",
        primary_domains=[KnowledgeDomain.PSYCHOLOGY, KnowledgeDomain.SCIENCE],
        primary_authors=[
            "Carl Rogers",
            "Carl Jung",
            "Viktor Frankl",
            "Abraham Maslow",
            "Irvin Yalom"
        ],
        related_authors=[
            "Sigmund Freud",
            "Alfred Adler",
            "Albert Ellis",
            "Aaron Beck",
            "Daniel Kahneman",
            "Martin Seligman"
        ],
        fields_of_study=[
            "Clinical Psychology",
            "Psychotherapy",
            "Humanistic Psychology",
            "Cognitive Behavioral Therapy",
            "Existential Psychology",
            "Positive Psychology"
        ],
        core_concepts=[
            "self-actualization",
            "cognitive distortions",
            "defense mechanisms",
            "unconditional positive regard",
            "meaning and purpose",
            "mindfulness",
            "emotional regulation",
            "attachment theory"
        ],
        related_concepts=[
            "mental health",
            "well-being",
            "personal growth",
            "resilience",
            "self-awareness",
            "therapeutic alliance",
            "behavioral change"
        ],
        discovery_keywords=[
            "psychology",
            "psychotherapy",
            "mental health",
            "counseling",
            "cognitive therapy"
        ],
        enable_auto_discovery=True,
        max_sources_per_author=12
    ),
    
    "zen_master": CharacterKnowledgeProfile(
        character_name="Master Kai",
        primary_domains=[KnowledgeDomain.PHILOSOPHY, KnowledgeDomain.SPIRITUALITY],
        primary_authors=[
            "Thich Nhat Hanh",
            "Shunryu Suzuki",
            "Pema Chödrön",
            "D.T. Suzuki",
            "Alan Watts"
        ],
        related_authors=[
            "Eckhart Tolle",
            "Jon Kabat-Zinn",
            "Jack Kornfield",
            "Chögyam Trungpa"
        ],
        fields_of_study=[
            "Zen Buddhism",
            "Mindfulness",
            "Meditation",
            "Buddhist Philosophy",
            "Contemplative Practice"
        ],
        core_concepts=[
            "mindfulness",
            "present moment",
            "non-attachment",
            "beginner's mind",
            "zazen",
            "enlightenment",
            "impermanence",
            "emptiness"
        ],
        discovery_keywords=[
            "zen",
            "mindfulness",
            "meditation",
            "buddhism",
            "contemplation"
        ],
        enable_auto_discovery=True
    ),
    
    "business_coach": CharacterKnowledgeProfile(
        character_name="Coach Ryan",
        primary_domains=[KnowledgeDomain.BUSINESS, KnowledgeDomain.SELF_HELP],
        primary_authors=[
            "Peter Drucker",
            "Jim Collins",
            "Simon Sinek",
            "Clayton Christensen",
            "Eric Ries"
        ],
        related_authors=[
            "Stephen Covey",
            "Dale Carnegie",
            "Seth Godin",
            "Gary Vaynerchuk",
            "Patrick Lencioni"
        ],
        fields_of_study=[
            "Business Strategy",
            "Leadership",
            "Entrepreneurship",
            "Management",
            "Innovation"
        ],
        core_concepts=[
            "leadership",
            "strategy",
            "innovation",
            "execution",
            "culture",
            "growth",
            "agile",
            "lean startup"
        ],
        discovery_keywords=[
            "business",
            "leadership",
            "management",
            "strategy",
            "entrepreneurship"
        ],
        enable_auto_discovery=True
    ),
    
    "life_coach": CharacterKnowledgeProfile(
        character_name="Coach Jordan",
        primary_domains=[KnowledgeDomain.SELF_HELP, KnowledgeDomain.PSYCHOLOGY],
        primary_authors=[
            "Stephen Covey",
            "Robin Sharma",
            "Brené Brown",
            "Carol Dweck",
            "James Clear"
        ],
        related_authors=[
            "Tony Robbins",
            "Brendon Burchard",
            "Marie Forleo",
            "Glennon Doyle"
        ],
        fields_of_study=[
            "Personal Development",
            "Goal Setting",
            "Life Balance",
            "Habit Formation",
            "Purpose Discovery"
        ],
        core_concepts=[
            "goals",
            "values",
            "purpose",
            "habits",
            "balance",
            "growth",
            "authenticity",
            "resilience"
        ],
        discovery_keywords=[
            "personal development",
            "life coaching",
            "self-improvement",
            "habits",
            "goals"
        ],
        enable_auto_discovery=True
    ),
    
    "scientist": CharacterKnowledgeProfile(
        character_name="Dr. Nova",
        primary_domains=[KnowledgeDomain.SCIENCE, KnowledgeDomain.PHILOSOPHY],
        primary_authors=[
            "Carl Sagan",
            "Richard Feynman",
            "Neil deGrasse Tyson",
            "Stephen Hawking",
            "Isaac Asimov"
        ],
        related_authors=[
            "Brian Greene",
            "Michio Kaku",
            "Bill Nye",
            "Richard Dawkins"
        ],
        fields_of_study=[
            "Astronomy",
            "Physics",
            "Scientific Method",
            "Critical Thinking",
            "Science Communication"
        ],
        core_concepts=[
            "scientific method",
            "evidence",
            "skepticism",
            "cosmos",
            "evolution",
            "critical thinking",
            "curiosity",
            "wonder"
        ],
        discovery_keywords=[
            "science",
            "astronomy",
            "physics",
            "cosmos",
            "scientific thinking"
        ],
        enable_auto_discovery=True
    ),

    "medical_advisor": CharacterKnowledgeProfile(
        character_name="Dr. Health",
        primary_domains=[KnowledgeDomain.SCIENCE, KnowledgeDomain.SELF_HELP],
        primary_authors=[
            "Andrew Huberman",
            "Peter Attia",
            "Matthew Walker",
            "Rhonda Patrick",
            "David Sinclair"
        ],
        related_authors=[
            "Michael Greger",
            "Chris Kresser",
            "Siddhartha Mukherjee",
            "Atul Gawande"
        ],
        fields_of_study=[
            "General Medicine",
            "Nutrition Science",
            "Sleep Medicine",
            "Preventive Health",
            "Exercise Physiology"
        ],
        core_concepts=[
            "evidence-based medicine",
            "preventive care",
            "nutrition",
            "sleep hygiene",
            "immune function",
            "vital signs",
            "wellness",
            "body systems"
        ],
        discovery_keywords=[
            "health",
            "medical",
            "wellness",
            "nutrition",
            "symptoms",
            "prevention"
        ],
        enable_auto_discovery=True
    )
}


def get_character_profile(character_id: str) -> Optional[CharacterKnowledgeProfile]:
    """Get knowledge profile for a character"""
    return KNOWLEDGE_PROFILES.get(character_id)


def register_character_profile(character_id: str, profile: CharacterKnowledgeProfile):
    """Register a new character profile dynamically"""
    KNOWLEDGE_PROFILES[character_id] = profile


def create_custom_profile(
    character_name: str,
    domains: List[str],
    authors: List[str],
    concepts: List[str],
    **kwargs
) -> CharacterKnowledgeProfile:
    """
    Helper to create custom profiles easily
    No need to know the full dataclass structure
    """
    # Convert string domains to enum
    domain_enums = []
    for domain in domains:
        try:
            domain_enums.append(KnowledgeDomain(domain.lower()))
        except ValueError:
            domain_enums.append(KnowledgeDomain.CUSTOM)
    
    return CharacterKnowledgeProfile(
        character_name=character_name,
        primary_domains=domain_enums,
        primary_authors=authors,
        core_concepts=concepts,
        **kwargs
    )


# ============================================================
# EXAMPLE: How to add a new character dynamically
# ============================================================

def example_add_new_character():
    """
    Example showing how easy it is to add a new character
    without modifying core code
    """
    # Option 1: Full control
    buddhist_monk = CharacterKnowledgeProfile(
        character_name="Zen Master",
        primary_domains=[KnowledgeDomain.SPIRITUALITY, KnowledgeDomain.PHILOSOPHY],
        primary_authors=["Dogen", "Thich Nhat Hanh", "Shunryu Suzuki"],
        fields_of_study=["Zen Buddhism", "Meditation", "Mindfulness"],
        core_concepts=["mindfulness", "zazen", "satori", "emptiness"],
        enable_auto_discovery=True
    )
    register_character_profile("zen_master", buddhist_monk)
    
    # Option 2: Quick helper
    scientist = create_custom_profile(
        character_name="Dr. Science",
        domains=["science"],
        authors=["Carl Sagan", "Richard Feynman", "Neil deGrasse Tyson"],
        concepts=["curiosity", "empiricism", "cosmos", "wonder"],
        fields_of_study=["Physics", "Astronomy", "Scientific Method"]
    )
    register_character_profile("scientist", scientist)

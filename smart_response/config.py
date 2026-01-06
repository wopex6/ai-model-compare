"""
Smart Response System Configuration
Centralized configuration for all magic numbers and thresholds
"""

# ==================== OUTCOME RECORDING ====================
# Satisfaction scores based on follow-up timing
SATISFACTION_QUICK_FOLLOWUP = 0.8      # < 60 seconds = engaged
SATISFACTION_NORMAL_FOLLOWUP = 0.6     # 60-300 seconds = normal
SATISFACTION_SLOW_FOLLOWUP = 0.4       # > 300 seconds = long gap

# Time thresholds (seconds)
QUICK_FOLLOWUP_THRESHOLD = 60          # seconds
NORMAL_FOLLOWUP_THRESHOLD = 300        # seconds (5 minutes)

# ==================== CHARACTER MATCHING ====================
# Match score threshold for using character style
CHARACTER_MATCH_THRESHOLD = 0.5        # 0-1, higher = stricter matching

# Urgency threshold for direct/concise responses
URGENCY_THRESHOLD = 0.7                # 0-1, higher = more urgent

# ==================== TRAIT-SPACE GAP DETECTION ====================
# Distance threshold for identifying gaps (12D Euclidean distance)
GAP_DISTANCE_THRESHOLD = 1.5           # Gap if nearest char > this distance
GAP_SCORE_NORMALIZATION = 2.0          # Divide excess distance by this for 0-1 score

# Maximum distance in 12D unit space (sqrt(12) ≈ 3.46)
MAX_TRAIT_DISTANCE = 3.46

# ==================== CHARACTER EXPANSION ====================
# Maximum characters to add per expansion run
MAX_CHARACTERS_PER_RUN = 1

# Minimum gap score to trigger character generation
MIN_GAP_SCORE_FOR_GENERATION = 0.3     # 0-1, higher = only fill severe gaps

# ==================== EXPLICIT CONTEXT ====================
# Expiration times for different context types (hours)
CONTEXT_EXPIRATION = {
    'emotional_state': 24,             # Emotional states expire after 24 hours
    'goal': 168,                       # Goals persist for 1 week
    'preference': 720,                 # Preferences persist for 30 days
    'need': 72,                        # Needs persist for 3 days
    'self_description': 2160,          # Self descriptions persist for 90 days
    'intention': 48,                   # Intentions persist for 2 days
    'value': 8760,                     # Values persist for 1 year
}

# Default expiration for unknown types
DEFAULT_CONTEXT_EXPIRATION_HOURS = 168  # 1 week

# ==================== AI BUDGET (Reference - actual in ai_budget_manager) ====================
# These are reference values - actual enforcement is in ai_budget_manager.py
DAILY_AI_LIMIT = 100                   # Maximum AI calls per day
BACKGROUND_AI_LIMIT = 10               # Background tasks AI limit per day
HOURLY_AI_LIMIT = 30                   # Maximum AI calls per hour
RATE_LIMIT_PER_MINUTE = 20             # Maximum AI calls per minute

# Warning thresholds
BUDGET_WARNING_THRESHOLD = 0.8         # Warn at 80% usage
BUDGET_CRITICAL_THRESHOLD = 1.0        # Stop at 100% usage

# ==================== PROACTIVE CLARIFICATION ====================
CLARIFICATION_CONFIDENCE_THRESHOLD = 0.6  # Ask clarification if confidence < this

# ==================== HISTORY SYSTEM ====================
# Maximum conversation history to keep in memory
MAX_HISTORY_MESSAGES = 20

# Progress tracking interval (days)
PROGRESS_TRACKING_INTERVAL_DAYS = 7

# ==================== BACKGROUND SCHEDULER ====================
# Task schedules (24-hour format)
DAILY_MAINTENANCE_TIME = "02:00"       # 2 AM
WEEKLY_PATTERN_EXPANSION_DAY = "sunday"
WEEKLY_PATTERN_EXPANSION_TIME = "03:00"
WEEKLY_CHARACTER_EXPANSION_DAY = "wednesday"
WEEKLY_CHARACTER_EXPANSION_TIME = "03:30"
MONTHLY_CLEANUP_DAY = 1                # First of month
MONTHLY_CLEANUP_TIME = "04:00"

# ==================== DATABASE ====================
DEFAULT_DATABASE_PATH = 'integrated_users.db'

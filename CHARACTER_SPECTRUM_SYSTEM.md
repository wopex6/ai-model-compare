# 🎭 Character Spectrum & AI-Powered Expansion System
## **Multi-Perspective Context Analysis with Controlled AI Growth**

---

## **Core Vision**

> **Different philosophical lenses view the same event differently.**
> **Match users to the character-philosophy that serves them best.**
> **Expand intelligently with strict cost controls.**

---

## **1. 🎯 CRITICAL: AI Usage Monitoring & Cost Control**

### **The Problem**
- AI calls are expensive ($0.002 per message)
- Background AI expansion could cause runaway costs
- Self-improving systems can spiral out of control
- Need strict monitoring, logging, and circuit breakers

### **The Solution: AI Budget Management System**

```python
class AIBudgetManager:
    """
    Strict cost control and monitoring for all AI calls
    Prevents runaway expenses with circuit breakers
    """
    
    # COST CONSTANTS (update as pricing changes)
    COST_PER_CALL = 0.002  # $0.002 per message
    COST_PER_ANALYSIS = 0.005  # $0.005 for deeper analysis
    COST_PER_GENERATION = 0.01  # $0.01 for character generation
    
    # BUDGET LIMITS (configurable)
    DAILY_BUDGET = 10.00  # $10/day maximum
    HOURLY_BUDGET = 2.00  # $2/hour maximum
    BACKGROUND_BUDGET = 1.00  # $1/day for background tasks
    
    # CIRCUIT BREAKER THRESHOLDS
    CALLS_PER_MINUTE = 60  # Max 60 calls/minute
    CALLS_PER_HOUR = 1000  # Max 1000 calls/hour
    UNUSUAL_PATTERN_THRESHOLD = 5  # Flag if pattern detected 5x
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._init_tables()
        self.circuit_breaker_active = False
    
    def _init_tables(self):
        """Create tables for AI usage tracking"""
        cursor = self.db.cursor()
        
        # Track every AI call
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- What was called
                call_type TEXT NOT NULL,  -- 'user_chat', 'background_analysis', 'character_gen'
                character TEXT,
                user_id INTEGER,
                
                -- Cost tracking
                estimated_cost FLOAT NOT NULL,
                
                -- Context
                purpose TEXT,  -- Why this call was made
                input_tokens INTEGER,
                output_tokens INTEGER,
                
                -- Result
                success BOOLEAN,
                error_message TEXT,
                
                -- Flags
                is_background BOOLEAN DEFAULT 0,
                is_automated BOOLEAN DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_usage_timestamp 
            ON ai_usage_log(timestamp)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_usage_type 
            ON ai_usage_log(call_type, timestamp)
        ''')
        
        # Track daily/hourly budgets
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_budget_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period_type TEXT NOT NULL,  -- 'daily', 'hourly'
                period_start TIMESTAMP NOT NULL,
                period_end TIMESTAMP NOT NULL,
                
                -- Spending
                total_calls INTEGER DEFAULT 0,
                total_cost FLOAT DEFAULT 0.0,
                background_cost FLOAT DEFAULT 0.0,
                
                -- Status
                budget_exceeded BOOLEAN DEFAULT 0,
                circuit_breaker_triggered BOOLEAN DEFAULT 0
            )
        ''')
        
        # Track unusual patterns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_usage_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Pattern details
                pattern_type TEXT NOT NULL,  -- 'spike', 'loop', 'error_cascade'
                severity TEXT NOT NULL,  -- 'low', 'medium', 'high', 'critical'
                
                -- Data
                call_count INTEGER,
                time_window_minutes INTEGER,
                cost_impact FLOAT,
                
                -- Action taken
                action_taken TEXT,  -- 'logged', 'throttled', 'circuit_breaker'
                resolved_at TIMESTAMP
            )
        ''')
        
        self.db.commit()
        print("✓ AI Budget Management tables initialized")
    
    def request_ai_call(self, call_type: str, purpose: str,
                       user_id: Optional[int] = None,
                       character: Optional[str] = None,
                       is_background: bool = False) -> Tuple[bool, str]:
        """
        Request permission to make an AI call
        
        Returns:
            (allowed, reason) - If False, reason explains why denied
        """
        
        # CIRCUIT BREAKER CHECK
        if self.circuit_breaker_active:
            return False, "Circuit breaker active - AI calls temporarily halted"
        
        # Estimate cost
        if call_type == 'user_chat':
            estimated_cost = self.COST_PER_CALL
        elif call_type == 'background_analysis':
            estimated_cost = self.COST_PER_ANALYSIS
        elif call_type == 'character_generation':
            estimated_cost = self.COST_PER_GENERATION
        else:
            estimated_cost = self.COST_PER_CALL
        
        # Check hourly budget
        hourly_spent = self._get_spending_last_n_hours(1)
        if hourly_spent + estimated_cost > self.HOURLY_BUDGET:
            self._trigger_throttle("Hourly budget exceeded")
            return False, f"Hourly budget limit reached: ${hourly_spent:.2f}/${self.HOURLY_BUDGET}"
        
        # Check daily budget
        daily_spent = self._get_spending_last_n_days(1)
        if daily_spent + estimated_cost > self.DAILY_BUDGET:
            self._trigger_circuit_breaker("Daily budget exceeded")
            return False, f"Daily budget limit reached: ${daily_spent:.2f}/${self.DAILY_BUDGET}"
        
        # Check background budget (if background call)
        if is_background:
            background_spent = self._get_background_spending_today()
            if background_spent + estimated_cost > self.BACKGROUND_BUDGET:
                return False, f"Background budget limit reached: ${background_spent:.2f}/${self.BACKGROUND_BUDGET}"
        
        # Check rate limits
        calls_last_minute = self._get_calls_last_n_minutes(1)
        if calls_last_minute >= self.CALLS_PER_MINUTE:
            self._trigger_throttle("Rate limit: calls per minute")
            return False, f"Rate limit: {calls_last_minute} calls in last minute"
        
        calls_last_hour = self._get_calls_last_n_minutes(60)
        if calls_last_hour >= self.CALLS_PER_HOUR:
            self._trigger_circuit_breaker("Rate limit: calls per hour")
            return False, f"Rate limit: {calls_last_hour} calls in last hour"
        
        # Check for unusual patterns
        pattern = self._detect_unusual_pattern()
        if pattern and pattern['severity'] == 'critical':
            self._trigger_circuit_breaker(f"Unusual pattern: {pattern['pattern_type']}")
            return False, f"Unusual usage pattern detected: {pattern['pattern_type']}"
        
        # APPROVED
        return True, "OK"
    
    def log_ai_call(self, call_type: str, purpose: str,
                   estimated_cost: float,
                   success: bool,
                   user_id: Optional[int] = None,
                   character: Optional[str] = None,
                   is_background: bool = False,
                   input_tokens: int = 0,
                   output_tokens: int = 0,
                   error_message: Optional[str] = None):
        """Log every AI call for tracking and analysis"""
        
        cursor = self.db.cursor()
        
        cursor.execute('''
            INSERT INTO ai_usage_log
            (call_type, character, user_id, estimated_cost, purpose,
             input_tokens, output_tokens, success, error_message,
             is_background, is_automated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            call_type, character, user_id, estimated_cost, purpose,
            input_tokens, output_tokens, success, error_message,
            is_background, is_background  # Automated if background
        ))
        
        self.db.commit()
        
        # Update budget tracking
        self._update_budget_tracking(estimated_cost, is_background)
    
    def _get_spending_last_n_hours(self, n: int) -> float:
        """Get total spending in last N hours"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT COALESCE(SUM(estimated_cost), 0)
            FROM ai_usage_log
            WHERE timestamp > datetime('now', '-' || ? || ' hours')
            AND success = 1
        ''', (n,))
        
        return cursor.fetchone()[0]
    
    def _get_spending_last_n_days(self, n: int) -> float:
        """Get total spending in last N days"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT COALESCE(SUM(estimated_cost), 0)
            FROM ai_usage_log
            WHERE timestamp > datetime('now', '-' || ? || ' days')
            AND success = 1
        ''', (n,))
        
        return cursor.fetchone()[0]
    
    def _get_background_spending_today(self) -> float:
        """Get background task spending today"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT COALESCE(SUM(estimated_cost), 0)
            FROM ai_usage_log
            WHERE DATE(timestamp) = DATE('now')
            AND is_background = 1
            AND success = 1
        ''')
        
        return cursor.fetchone()[0]
    
    def _get_calls_last_n_minutes(self, n: int) -> int:
        """Get number of calls in last N minutes"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT COUNT(*)
            FROM ai_usage_log
            WHERE timestamp > datetime('now', '-' || ? || ' minutes')
        ''', (n,))
        
        return cursor.fetchone()[0]
    
    def _detect_unusual_pattern(self) -> Optional[Dict]:
        """
        Detect unusual usage patterns that might indicate:
        - Infinite loops
        - Runaway processes
        - Attack attempts
        """
        cursor = self.db.cursor()
        
        # Pattern 1: Spike in calls (>50 calls in 5 minutes)
        cursor.execute('''
            SELECT COUNT(*) FROM ai_usage_log
            WHERE timestamp > datetime('now', '-5 minutes')
        ''')
        recent_calls = cursor.fetchone()[0]
        
        if recent_calls > 50:
            self._log_pattern('spike', 'critical', recent_calls, 5)
            return {
                'pattern_type': 'spike',
                'severity': 'critical',
                'call_count': recent_calls
            }
        
        # Pattern 2: Loop detection (same call_type rapidly repeated)
        cursor.execute('''
            SELECT call_type, COUNT(*) as cnt
            FROM ai_usage_log
            WHERE timestamp > datetime('now', '-2 minutes')
            GROUP BY call_type
            HAVING cnt > 20
        ''')
        
        loop_detected = cursor.fetchone()
        if loop_detected:
            self._log_pattern('loop', 'high', loop_detected[1], 2)
            return {
                'pattern_type': 'loop',
                'severity': 'high',
                'call_count': loop_detected[1]
            }
        
        # Pattern 3: Error cascade (multiple errors in sequence)
        cursor.execute('''
            SELECT COUNT(*) FROM ai_usage_log
            WHERE timestamp > datetime('now', '-5 minutes')
            AND success = 0
        ''')
        error_count = cursor.fetchone()[0]
        
        if error_count > 10:
            self._log_pattern('error_cascade', 'high', error_count, 5)
            return {
                'pattern_type': 'error_cascade',
                'severity': 'high',
                'call_count': error_count
            }
        
        return None
    
    def _log_pattern(self, pattern_type: str, severity: str,
                    call_count: int, time_window: int):
        """Log detected unusual pattern"""
        cursor = self.db.cursor()
        
        # Check if already logged recently (avoid duplicate alerts)
        cursor.execute('''
            SELECT id FROM ai_usage_patterns
            WHERE pattern_type = ?
            AND detected_at > datetime('now', '-10 minutes')
            AND resolved_at IS NULL
        ''', (pattern_type,))
        
        if cursor.fetchone():
            return  # Already logged
        
        cursor.execute('''
            INSERT INTO ai_usage_patterns
            (pattern_type, severity, call_count, time_window_minutes)
            VALUES (?, ?, ?, ?)
        ''', (pattern_type, severity, call_count, time_window))
        
        self.db.commit()
    
    def _trigger_throttle(self, reason: str):
        """Throttle AI calls (soft limit)"""
        print(f"⚠️ AI THROTTLE: {reason}")
        # Log the throttle event
        cursor = self.db.cursor()
        cursor.execute('''
            UPDATE ai_usage_patterns
            SET action_taken = 'throttled'
            WHERE resolved_at IS NULL
        ''')
        self.db.commit()
    
    def _trigger_circuit_breaker(self, reason: str):
        """EMERGENCY: Stop all AI calls (hard limit)"""
        self.circuit_breaker_active = True
        print(f"🚨 CIRCUIT BREAKER ACTIVATED: {reason}")
        print(f"   All AI calls halted. Manual reset required.")
        
        # Log to database
        cursor = self.db.cursor()
        cursor.execute('''
            UPDATE ai_usage_patterns
            SET action_taken = 'circuit_breaker'
            WHERE resolved_at IS NULL
        ''')
        self.db.commit()
        
        # Send alert (email/notification in production)
        self._send_alert(reason)
    
    def reset_circuit_breaker(self, admin_authorization: str):
        """Reset circuit breaker (requires admin action)"""
        # In production, verify admin authorization
        self.circuit_breaker_active = False
        print("✅ Circuit breaker reset")
        
        cursor = self.db.cursor()
        cursor.execute('''
            UPDATE ai_usage_patterns
            SET resolved_at = CURRENT_TIMESTAMP
            WHERE resolved_at IS NULL
        ''')
        self.db.commit()
    
    def _update_budget_tracking(self, cost: float, is_background: bool):
        """Update budget tracking tables"""
        # Implementation for tracking budgets by period
        pass
    
    def _send_alert(self, reason: str):
        """Send alert to administrators"""
        # In production: email, SMS, Slack, etc.
        print(f"📧 ALERT SENT: {reason}")
    
    def get_usage_report(self, period: str = 'today') -> Dict:
        """Get usage report for monitoring dashboard"""
        cursor = self.db.cursor()
        
        if period == 'today':
            time_filter = "DATE(timestamp) = DATE('now')"
        elif period == 'this_hour':
            time_filter = "timestamp > datetime('now', '-1 hour')"
        else:
            time_filter = "1=1"
        
        # Total calls and cost
        cursor.execute(f'''
            SELECT 
                COUNT(*) as total_calls,
                SUM(estimated_cost) as total_cost,
                SUM(CASE WHEN is_background = 1 THEN estimated_cost ELSE 0 END) as background_cost,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as error_count
            FROM ai_usage_log
            WHERE {time_filter}
        ''')
        
        row = cursor.fetchone()
        
        # Breakdown by call type
        cursor.execute(f'''
            SELECT call_type, COUNT(*), SUM(estimated_cost)
            FROM ai_usage_log
            WHERE {time_filter}
            GROUP BY call_type
        ''')
        
        breakdown = {row[0]: {'calls': row[1], 'cost': row[2]} 
                    for row in cursor.fetchall()}
        
        # Recent patterns
        cursor.execute('''
            SELECT pattern_type, severity, detected_at
            FROM ai_usage_patterns
            WHERE detected_at > datetime('now', '-24 hours')
            ORDER BY detected_at DESC
            LIMIT 5
        ''')
        
        patterns = [
            {'type': row[0], 'severity': row[1], 'time': row[2]}
            for row in cursor.fetchall()
        ]
        
        return {
            'total_calls': row[0] or 0,
            'total_cost': round(row[1] or 0, 2),
            'background_cost': round(row[2] or 0, 2),
            'error_count': row[3] or 0,
            'breakdown': breakdown,
            'recent_patterns': patterns,
            'circuit_breaker_active': self.circuit_breaker_active,
            'budget_status': {
                'hourly': {
                    'spent': round(self._get_spending_last_n_hours(1), 2),
                    'limit': self.HOURLY_BUDGET,
                    'remaining': round(self.HOURLY_BUDGET - self._get_spending_last_n_hours(1), 2)
                },
                'daily': {
                    'spent': round(self._get_spending_last_n_days(1), 2),
                    'limit': self.DAILY_BUDGET,
                    'remaining': round(self.DAILY_BUDGET - self._get_spending_last_n_days(1), 2)
                },
                'background_today': {
                    'spent': round(self._get_background_spending_today(), 2),
                    'limit': self.BACKGROUND_BUDGET,
                    'remaining': round(self.BACKGROUND_BUDGET - self._get_background_spending_today(), 2)
                }
            }
        }
```

### **Usage Pattern**

```python
# Initialize budget manager
budget_manager = AIBudgetManager(db_connection)

# Before EVERY AI call:
allowed, reason = budget_manager.request_ai_call(
    call_type='user_chat',
    purpose='User asking about fitness goals',
    user_id=123,
    character='coach',
    is_background=False
)

if not allowed:
    print(f"AI call denied: {reason}")
    # Use fallback response
    return quick_reply_or_cached_response()

# Make the AI call
try:
    response = ai_model.chat(message)
    success = True
    error = None
except Exception as e:
    success = False
    error = str(e)

# Log the call
budget_manager.log_ai_call(
    call_type='user_chat',
    purpose='User fitness goal discussion',
    estimated_cost=0.002,
    success=success,
    user_id=123,
    character='coach',
    input_tokens=50,
    output_tokens=200,
    error_message=error
)
```

---

## **2. 🎭 Character Trait Spectrum System**

### **The Concept**
> Characters are not discrete entities, but **points in trait-space**

### **Implementation**

```python
class CharacterTraitSystem:
    """
    Define characters as combinations of traits (0-1 spectrum)
    """
    
    # Core trait dimensions (expandable)
    TRAIT_DIMENSIONS = {
        # Philosophical approach
        'stoicism': (0, 1),  # 0=emotional, 1=rational
        'optimism': (0, 1),  # 0=realistic, 1=optimistic
        'directness': (0, 1),  # 0=gentle, 1=direct
        
        # Coaching style
        'supportiveness': (0, 1),  # 0=challenging, 1=supportive
        'structure': (0, 1),  # 0=flexible, 1=structured
        'depth': (0, 1),  # 0=practical, 1=philosophical
        
        # Communication
        'formality': (0, 1),  # 0=casual, 1=formal
        'verbosity': (0, 1),  # 0=concise, 1=detailed
        
        # Focus areas
        'action_oriented': (0, 1),  # 0=reflective, 1=action
        'present_focus': (0, 1),  # 0=past/future, 1=present
        
        # Emotional approach
        'empathy': (0, 1),  # 0=logical, 1=empathetic
        'intensity': (0, 1),  # 0=calm, 1=intense
    }
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._init_tables()
        self._load_base_characters()
    
    def _init_tables(self):
        """Create character database"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS character_library (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT,
                
                -- Historical/theoretical basis
                historical_figure TEXT,  -- "Marcus Aurelius", "Carl Rogers", etc.
                philosophical_school TEXT,  -- "Stoicism", "CBT", etc.
                time_period TEXT,
                
                -- Trait vector (JSON)
                trait_vector TEXT NOT NULL,
                
                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_ai_generated BOOLEAN DEFAULT 0,
                generation_context TEXT,  -- Why this character was created
                
                -- Usage stats
                usage_count INTEGER DEFAULT 0,
                last_used TIMESTAMP,
                effectiveness_score FLOAT DEFAULT 0.5
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_character_effectiveness 
            ON character_library(effectiveness_score DESC)
        ''')
        
        # Track character-situation matching outcomes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS character_usage_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- What happened
                character_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                situation_context TEXT NOT NULL,  -- JSON
                
                -- Matching
                match_score FLOAT,  -- How well character matched situation
                match_reasoning TEXT,
                
                -- Outcome
                user_satisfaction INTEGER,  -- 1-5 rating if collected
                conversation_length INTEGER,  -- Number of exchanges
                goal_progress BOOLEAN,  -- Did user make progress?
                
                -- Learning
                was_optimal_choice BOOLEAN,  -- Determined later
                
                FOREIGN KEY (character_id) REFERENCES character_library(id)
            )
        ''')
        
        self.db.commit()
        print("✓ Character trait system tables initialized")
    
    def _load_base_characters(self):
        """Load initial 8 characters into database"""
        
        base_characters = [
            {
                'character_name': 'motivational_coach',
                'display_name': 'Motivational Coach',
                'description': 'Energetic, supportive coach focused on action and goals',
                'historical_figure': 'Tony Robbins',
                'philosophical_school': 'Positive Psychology',
                'trait_vector': {
                    'stoicism': 0.3,
                    'optimism': 0.9,
                    'directness': 0.7,
                    'supportiveness': 0.9,
                    'structure': 0.6,
                    'depth': 0.3,
                    'formality': 0.2,
                    'verbosity': 0.6,
                    'action_oriented': 0.9,
                    'present_focus': 0.8,
                    'empathy': 0.7,
                    'intensity': 0.8
                }
            },
            {
                'character_name': 'wisdom_sage',
                'display_name': 'Wisdom Sage',
                'description': 'Contemplative Taoist philosopher focusing on harmony and flow',
                'historical_figure': 'Lao Tzu',
                'philosophical_school': 'Taoism',
                'trait_vector': {
                    'stoicism': 0.8,
                    'optimism': 0.6,
                    'directness': 0.3,
                    'supportiveness': 0.7,
                    'structure': 0.2,
                    'depth': 0.9,
                    'formality': 0.7,
                    'verbosity': 0.7,
                    'action_oriented': 0.3,
                    'present_focus': 0.9,
                    'empathy': 0.6,
                    'intensity': 0.2
                }
            },
            {
                'character_name': 'stoic_philosopher',
                'display_name': 'Marcus Aurelius',
                'description': 'Stoic emperor focusing on duty, virtue, and acceptance',
                'historical_figure': 'Marcus Aurelius',
                'philosophical_school': 'Stoicism',
                'trait_vector': {
                    'stoicism': 1.0,
                    'optimism': 0.5,
                    'directness': 0.8,
                    'supportiveness': 0.5,
                    'structure': 0.8,
                    'depth': 0.8,
                    'formality': 0.8,
                    'verbosity': 0.5,
                    'action_oriented': 0.7,
                    'present_focus': 0.9,
                    'empathy': 0.4,
                    'intensity': 0.5
                }
            },
            {
                'character_name': 'psychologist',
                'display_name': 'Clinical Psychologist',
                'description': 'Evidence-based therapist using CBT and compassion',
                'historical_figure': 'Carl Rogers',
                'philosophical_school': 'Cognitive Behavioral Therapy',
                'trait_vector': {
                    'stoicism': 0.6,
                    'optimism': 0.6,
                    'directness': 0.5,
                    'supportiveness': 0.8,
                    'structure': 0.7,
                    'depth': 0.7,
                    'formality': 0.6,
                    'verbosity': 0.6,
                    'action_oriented': 0.6,
                    'present_focus': 0.7,
                    'empathy': 0.9,
                    'intensity': 0.4
                }
            },
            # Add other 4 characters...
        ]
        
        cursor = self.db.cursor()
        
        for char in base_characters:
            try:
                cursor.execute('''
                    INSERT INTO character_library
                    (character_name, display_name, description, historical_figure,
                     philosophical_school, trait_vector, is_ai_generated)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                ''', (
                    char['character_name'],
                    char['display_name'],
                    char['description'],
                    char['historical_figure'],
                    char['philosophical_school'],
                    json.dumps(char['trait_vector'])
                ))
            except sqlite3.IntegrityError:
                # Character already exists
                pass
        
        self.db.commit()
    
    def find_best_character_for_situation(self, situation_context: Dict) -> Dict:
        """
        Find the best character for a given situation
        
        Args:
            situation_context: {
                'user_emotional_state': 'anxious',
                'user_personality': {...traits...},
                'goal_type': 'immediate_action' or 'long_term_growth',
                'challenge_type': 'emotional', 'practical', 'philosophical',
                'user_preference': {...past successful characters...}
            }
        
        Returns:
            {
                'character': character_data,
                'match_score': 0.85,
                'reasoning': "Stoic approach matches need for emotional regulation"
            }
        """
        
        # Determine ideal trait profile for situation
        ideal_traits = self._determine_ideal_traits(situation_context)
        
        # Get all characters
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT id, character_name, display_name, trait_vector, effectiveness_score
            FROM character_library
        ''')
        
        characters = cursor.fetchall()
        
        # Calculate match scores
        matches = []
        for char_id, name, display_name, trait_json, effectiveness in characters:
            traits = json.loads(trait_json)
            
            # Calculate trait distance
            distance = self._calculate_trait_distance(ideal_traits, traits)
            match_score = 1.0 - distance  # Convert distance to similarity
            
            # Weight by historical effectiveness
            weighted_score = match_score * 0.7 + effectiveness * 0.3
            
            matches.append({
                'character_id': char_id,
                'character_name': name,
                'display_name': display_name,
                'traits': traits,
                'match_score': weighted_score,
                'trait_distance': distance
            })
        
        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        best_match = matches[0]
        
        # Generate reasoning
        reasoning = self._generate_match_reasoning(
            situation_context, ideal_traits, best_match
        )
        
        return {
            'character': best_match,
            'match_score': best_match['match_score'],
            'reasoning': reasoning,
            'alternatives': matches[1:3]  # Top 2 alternatives
        }
    
    def _determine_ideal_traits(self, situation: Dict) -> Dict:
        """
        Determine ideal trait profile based on situation
        """
        ideal = {}
        
        # Emotional state mapping
        emotional_state = situation.get('user_emotional_state', 'neutral')
        
        if emotional_state in ['anxious', 'overwhelmed']:
            ideal['stoicism'] = 0.7  # Need calm, rational approach
            ideal['supportiveness'] = 0.8  # High support
            ideal['intensity'] = 0.3  # Low intensity
            ideal['empathy'] = 0.8  # High empathy
        
        elif emotional_state in ['motivated', 'excited']:
            ideal['action_oriented'] = 0.9  # Capitalize on motivation
            ideal['intensity'] = 0.7  # Match energy
            ideal['optimism'] = 0.8  # Reinforce positivity
        
        elif emotional_state in ['sad', 'discouraged']:
            ideal['empathy'] = 0.9  # High empathy
            ideal['optimism'] = 0.7  # Gentle optimism
            ideal['supportiveness'] = 0.9  # Strong support
        
        # Goal type mapping
        goal_type = situation.get('goal_type', 'general')
        
        if goal_type == 'immediate_action':
            ideal['action_oriented'] = 0.9
            ideal['structure'] = 0.8
            ideal['directness'] = 0.7
        
        elif goal_type == 'long_term_growth':
            ideal['depth'] = 0.8
            ideal['structure'] = 0.6
            ideal['present_focus'] = 0.5  # Balance past/future
        
        # Challenge type
        challenge = situation.get('challenge_type', 'general')
        
        if challenge == 'emotional':
            ideal['empathy'] = 0.9
            ideal['stoicism'] = 0.5  # Balanced
        
        elif challenge == 'practical':
            ideal['action_oriented'] = 0.9
            ideal['depth'] = 0.3  # Practical over philosophical
        
        elif challenge == 'philosophical':
            ideal['depth'] = 0.9
            ideal['verbosity'] = 0.7
        
        # Fill in defaults for unspecified traits
        for trait in self.TRAIT_DIMENSIONS:
            if trait not in ideal:
                ideal[trait] = 0.5  # Neutral default
        
        return ideal
    
    def _calculate_trait_distance(self, traits1: Dict, traits2: Dict) -> float:
        """
        Calculate Euclidean distance between trait vectors
        """
        distance_squared = 0
        for trait in self.TRAIT_DIMENSIONS:
            val1 = traits1.get(trait, 0.5)
            val2 = traits2.get(trait, 0.5)
            distance_squared += (val1 - val2) ** 2
        
        # Normalize by number of dimensions
        distance = (distance_squared / len(self.TRAIT_DIMENSIONS)) ** 0.5
        
        return distance
    
    def _generate_match_reasoning(self, situation: Dict,
                                  ideal_traits: Dict,
                                  best_match: Dict) -> str:
        """Generate human-readable reasoning for the match"""
        
        char_traits = best_match['traits']
        
        # Find strongest trait matches
        strong_matches = []
        for trait, ideal_value in ideal_traits.items():
            char_value = char_traits.get(trait, 0.5)
            if abs(ideal_value - char_value) < 0.2:  # Close match
                if ideal_value > 0.7:  # High need
                    strong_matches.append((trait, char_value))
        
        # Generate reasoning
        reasoning = f"{best_match['display_name']} is well-suited because "
        
        emotional_state = situation.get('user_emotional_state', 'neutral')
        reasoning += f"for someone feeling {emotional_state}, "
        
        if strong_matches:
            trait_names = [t[0].replace('_', ' ') for t in strong_matches[:2]]
            reasoning += f"their {' and '.join(trait_names)} align well with your needs."
        else:
            reasoning += "their balanced approach is appropriate."
        
        return reasoning
```

---

## **3. 📊 Character-Specific Context Layer**

### **The Concept**
> Same event, different interpretation per character

```python
class CharacterSpecificContext:
    """
    Each character interprets context through their philosophical lens
    """
    
    def interpret_event_as_character(self, event: Dict, character_traits: Dict) -> Dict:
        """
        Interpret an event through character's philosophical lens
        
        Example:
            Event: User says "I failed my exam"
            
            Coach (optimistic, action-oriented):
            → "Temporary setback, learn and plan next attempt"
            
            Stoic (stoic, rational):
            → "External outcome, focus on effort and virtue"
            
            Sage (contemplative, flow-focused):
            → "Natural cycle, resistance creates suffering"
            
            Psychologist (empathetic, structured):
            → "Emotional response is valid, let's explore it"
        """
        
        # Get character's dominant traits
        top_traits = self._get_dominant_traits(character_traits)
        
        interpretation = {
            'event': event,
            'character_lens': top_traits,
            'interpreted_meaning': None,
            'recommended_response_style': None,
            'philosophical_frame': None
        }
        
        # High stoicism → rational framing
        if character_traits.get('stoicism', 0) > 0.7:
            interpretation['philosophical_frame'] = 'stoic'
            interpretation['interpreted_meaning'] = self._stoic_interpretation(event)
            interpretation['recommended_response_style'] = 'rational_acceptance'
        
        # High optimism + action → motivational framing
        elif (character_traits.get('optimism', 0) > 0.7 and 
              character_traits.get('action_oriented', 0) > 0.7):
            interpretation['philosophical_frame'] = 'motivational'
            interpretation['interpreted_meaning'] = self._motivational_interpretation(event)
            interpretation['recommended_response_style'] = 'energetic_reframe'
        
        # High empathy + depth → therapeutic framing
        elif (character_traits.get('empathy', 0) > 0.7 and 
              character_traits.get('depth', 0) > 0.6):
            interpretation['philosophical_frame'] = 'therapeutic'
            interpretation['interpreted_meaning'] = self._therapeutic_interpretation(event)
            interpretation['recommended_response_style'] = 'explore_and_validate'
        
        # High depth + low action → philosophical framing
        elif (character_traits.get('depth', 0) > 0.7 and 
              character_traits.get('action_oriented', 0) < 0.4):
            interpretation['philosophical_frame'] = 'contemplative'
            interpretation['interpreted_meaning'] = self._contemplative_interpretation(event)
            interpretation['recommended_response_style'] = 'wisdom_and_perspective'
        
        else:
            # Balanced approach
            interpretation['philosophical_frame'] = 'balanced'
            interpretation['interpreted_meaning'] = self._balanced_interpretation(event)
            interpretation['recommended_response_style'] = 'adaptive'
        
        return interpretation
    
    def _get_dominant_traits(self, traits: Dict) -> List[str]:
        """Get character's top 3 traits"""
        sorted_traits = sorted(traits.items(), key=lambda x: x[1], reverse=True)
        return [t[0] for t in sorted_traits[:3]]
    
    def _stoic_interpretation(self, event: Dict) -> str:
        """Stoic lens: What can be controlled vs. what cannot"""
        # Implementation
        return "Event as test of virtue and focus on response, not outcome"
    
    def _motivational_interpretation(self, event: Dict) -> str:
        """Motivational lens: Opportunity for growth and action"""
        return "Challenge as stepping stone to success"
    
    def _therapeutic_interpretation(self, event: Dict) -> str:
        """Therapeutic lens: Emotional validity and cognitive patterns"""
        return "Experience as window into beliefs and coping patterns"
    
    def _contemplative_interpretation(self, event: Dict) -> str:
        """Contemplative lens: Natural flow and acceptance"""
        return "Moment in larger flow of life, neither good nor bad"
    
    def _balanced_interpretation(self, event: Dict) -> str:
        """Balanced lens: Multiple perspectives considered"""
        return "Situation with multiple valid interpretations and responses"
```

---

## **4. 🤖 AI-Powered Character Expansion (CONTROLLED)**

```python
class CharacterExpansionSystem:
    """
    Expand character library using AI - WITH STRICT CONTROLS
    """
    
    def __init__(self, db_connection, budget_manager: AIBudgetManager,
                 trait_system: CharacterTraitSystem):
        self.db = db_connection
        self.budget_manager = budget_manager
        self.trait_system = trait_system
    
    def expand_character_library(self, reason: str) -> Optional[Dict]:
        """
        Generate new character to fill gap in library
        
        This is a BACKGROUND TASK with strict cost controls
        
        Args:
            reason: Why expansion is needed (e.g., "No character for X situation")
        
        Returns:
            New character data or None if budget exceeded
        """
        
        # REQUEST PERMISSION
        allowed, deny_reason = self.budget_manager.request_ai_call(
            call_type='character_generation',
            purpose=f'Expand library: {reason}',
            is_background=True
        )
        
        if not allowed:
            print(f"❌ Character generation denied: {deny_reason}")
            return None
        
        # Identify gap in trait space
        gap_analysis = self._analyze_trait_space_gaps()
        
        # Generate character prompt
        prompt = self._create_character_generation_prompt(reason, gap_analysis)
        
        # CALL AI (with monitoring)
        try:
            start_time = time.time()
            response = ai_model.generate_character(prompt)  # Your AI call
            duration_ms = (time.time() - start_time) * 1000
            
            # Parse response
            new_character = self._parse_character_response(response)
            
            # Store in database
            self._store_generated_character(new_character, reason)
            
            # LOG SUCCESS
            self.budget_manager.log_ai_call(
                call_type='character_generation',
                purpose=f'Generated: {new_character["character_name"]}',
                estimated_cost=0.01,
                success=True,
                is_background=True,
                input_tokens=len(prompt.split()),
                output_tokens=len(response.split())
            )
            
            print(f"✅ New character generated: {new_character['display_name']}")
            return new_character
            
        except Exception as e:
            # LOG FAILURE
            self.budget_manager.log_ai_call(
                call_type='character_generation',
                purpose=f'Failed: {reason}',
                estimated_cost=0.01,
                success=False,
                is_background=True,
                error_message=str(e)
            )
            
            print(f"❌ Character generation failed: {e}")
            return None
    
    def _analyze_trait_space_gaps(self) -> Dict:
        """Find under-represented regions in trait space"""
        
        cursor = self.db.cursor()
        cursor.execute('SELECT trait_vector FROM character_library')
        
        all_vectors = [json.loads(row[0]) for row in cursor.fetchall()]
        
        # Analyze coverage (simplified - can use k-means clustering)
        # Return traits that are under-represented
        
        return {
            'underserved_traits': ['high_intensity_philosophical'],
            'missing_combinations': ['empathetic + stoic']
        }
    
    def _create_character_generation_prompt(self, reason: str, gap: Dict) -> str:
        """Create prompt for AI to generate new character"""
        
        prompt = f"""Create a new advisory character for a coaching system.

Reason for creation: {reason}

Gap analysis: {json.dumps(gap, indent=2)}

Generate a character with:
1. Name (historical figure or theoretical archetype)
2. Philosophical school/approach
3. Description (2-3 sentences)
4. Trait vector (JSON) with these dimensions:
   {json.dumps(list(self.trait_system.TRAIT_DIMENSIONS.keys()), indent=2)}
   Each trait: 0.0 to 1.0

Return as JSON:
{{
    "character_name": "unique_identifier",
    "display_name": "Display Name",
    "description": "...",
    "historical_figure": "...",
    "philosophical_school": "...",
    "trait_vector": {{...}}
}}
"""
        return prompt
    
    def _parse_character_response(self, response: str) -> Dict:
        """Parse AI response into character data"""
        # Parse JSON from AI response
        # Validate trait ranges
        # Return structured data
        return json.loads(response)
    
    def _store_generated_character(self, character: Dict, reason: str):
        """Store AI-generated character in database"""
        
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO character_library
            (character_name, display_name, description, historical_figure,
             philosophical_school, trait_vector, is_ai_generated, generation_context)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        ''', (
            character['character_name'],
            character['display_name'],
            character['description'],
            character.get('historical_figure'),
            character.get('philosophical_school'),
            json.dumps(character['trait_vector']),
            reason
        ))
        
        self.db.commit()
```

---

## **5. 📈 Learning from Outcomes**

```python
class CharacterEffectivenessLearner:
    """
    Learn which character-situation matches work best
    """
    
    def record_outcome(self, character_id: int, user_id: int,
                      situation: Dict, outcome: Dict):
        """
        Record outcome of character-situation match
        
        Args:
            situation: Context of the interaction
            outcome: {
                'conversation_length': 5,  # exchanges
                'user_satisfaction': 4,  # 1-5 if collected
                'goal_progress': True,
                'follow_up_interaction': True
            }
        """
        
        cursor = self.db.cursor()
        
        # Calculate match score (how well situation matched character)
        # This was determined earlier when character was selected
        
        cursor.execute('''
            INSERT INTO character_usage_outcomes
            (character_id, user_id, situation_context,
             match_score, conversation_length, goal_progress)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            character_id, user_id,
            json.dumps(situation),
            outcome.get('match_score', 0.5),
            outcome.get('conversation_length', 0),
            outcome.get('goal_progress', False)
        ))
        
        self.db.commit()
        
        # Update character effectiveness score
        self._update_effectiveness_score(character_id)
    
    def _update_effectiveness_score(self, character_id: int):
        """Update character's effectiveness based on outcomes"""
        
        cursor = self.db.cursor()
        
        # Calculate average outcome metrics
        cursor.execute('''
            SELECT 
                AVG(CASE WHEN goal_progress THEN 1.0 ELSE 0.0 END) as progress_rate,
                AVG(conversation_length) as avg_length,
                COUNT(*) as usage_count
            FROM character_usage_outcomes
            WHERE character_id = ?
            AND timestamp > datetime('now', '-30 days')
        ''', (character_id,))
        
        row = cursor.fetchone()
        
        if row and row[2] > 5:  # At least 5 uses
            progress_rate = row[0] or 0
            avg_length = row[1] or 0
            
            # Calculate effectiveness (weighted formula)
            effectiveness = (
                progress_rate * 0.6 +  # Goal progress most important
                min(avg_length / 10, 1.0) * 0.3 +  # Engagement
                0.5 * 0.1  # Base score
            )
            
            # Update character
            cursor.execute('''
                UPDATE character_library
                SET effectiveness_score = ?,
                    usage_count = usage_count + 1,
                    last_used = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (effectiveness, character_id))
            
            self.db.commit()
```

---

## **6. 🎯 Answers to Your Questions**

### **Q1: Is character-specific storage an issue?**
✅ **NO - It's a FEATURE**

- Each character SHOULD interpret differently
- Store: `history_secondary.character_interpretation` (JSON)
- Benefits: Multiple perspectives enrich understanding

### **Q2: Can we have more than 8 characters?**
✅ **YES - Expandable library**

- Start with 8 base characters
- AI generates more as needed (controlled)
- Library grows based on actual gaps

### **Q3: Better to have spectrum (0-1 traits)?**
✅ **YES - Implemented above**

- Characters = points in trait-space
- Find closest match via distance calculation
- Flexible and precise

### **Q4: Use established figures' philosophies?**
✅ **YES - Core strength**

- Base on historical/theoretical figures
- Leverage established wisdom
- Credible and proven approaches

### **Q5: Can we find characters dynamically?**
✅ **YES - Two approaches:**

1. **Preloaded** (8 characters) - Fast, no AI cost
2. **Dynamic** (AI generates) - Fills gaps, controlled cost

### **Q6: Expand via background AI?**
✅ **YES - With strict controls:**

- $1/day budget for background tasks
- Circuit breakers for runaway
- Log everything, detect patterns

### **Q7: Is this reasonable?**
✅ **YES - With safeguards in place**

All your concerns addressed with:
- Budget management
- Circuit breakers
- Logging and monitoring
- Pattern detection

### **Q8: Other issues?**
⚠️ **Consider:**

1. **Character coherence** - Generated characters should still be internally consistent
2. **User confusion** - Too many characters might overwhelm
3. **Maintenance** - Prune ineffective characters
4. **Bias** - AI-generated characters may have biases

### **Q9: How determine best trait combo?**
✅ **Multi-pronged approach:**

1. **Hypothesis-based** (situational matching)
2. **AI-assisted** (controlled calls)
3. **Data-driven** (learn from outcomes)
4. **Hybrid** (combine all three)

### **Q10: Can ask AI when necessary?**
✅ **YES - Always with:**

```python
allowed, reason = budget_manager.request_ai_call(...)
if allowed:
    # Make call
    # Log result
```

### **Q11: Monitor and control AI calls?**
✅ **YES - Complete system above:**

- Every call logged
- Budgets enforced
- Patterns detected
- Circuit breaker for emergencies

---

## **🎯 Summary: You're Right**

Your vision is:
- ✅ **Technically sound**
- ✅ **Strategically smart**
- ✅ **Properly controlled**
- ✅ **Ready to implement**

**Next steps:**
1. Implement `AIBudgetManager` (cost control)
2. Implement `CharacterTraitSystem` (spectrum)
3. Add character-specific interpretation layer
4. Set up background expansion (controlled)
5. Track outcomes and learn

**Want me to start implementing?** We can begin with the AI Budget Manager - the foundation for everything else. 🚀

# 🧠 Intelligent Context Architecture
## **A Proactive, Personality-Aware Coaching System**

---

## **Core Philosophy**

> **Context is not just data - it's interpretation through the lens of who the user is.**

The same event means different things to different people, or even to the same person at different times. This system doesn't just recall context - it **interprets** it intelligently to provide **long-term constructive guidance**.

---

## **1. 🎭 Personality-Based Context Interpretation**

### **Key Insight**
> "I failed my exam" means different things to different personalities:
> - **Achiever:** Devastating setback requiring action plan
> - **Learner:** Learning opportunity to improve
> - **Anxious:** Validation of fears, needs reassurance
> - **Optimist:** Temporary bump, focus on next attempt

### **Implementation: Context Interpreter**

```python
class PersonalityAwareContextInterpreter:
    """
    Interprets context through the lens of user personality
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.personality_profiler = PersonalityProfiler()
    
    def interpret_context(self, user_id: int, raw_context: Dict, 
                         event_data: Dict) -> Dict:
        """
        Interprets context based on user personality
        
        Args:
            raw_context: Objective facts (what happened)
            event_data: The event being interpreted
        
        Returns:
            Interpreted context with personality-aware insights
        """
        
        # Get user personality (with fallback handling)
        personality = self.get_user_personality(user_id)
        
        # Interpret the event through personality lens
        interpretation = {
            'raw_event': event_data,
            'personality_context': personality,
            'interpreted_meaning': None,
            'likely_emotional_impact': None,
            'recommended_approach': None,
            'confidence_level': 0.0
        }
        
        # Example: User mentions "I'm stressed about work"
        if 'stress' in event_data.get('message', '').lower():
            interpretation.update(
                self._interpret_stress_event(event_data, personality)
            )
        
        return interpretation
    
    def _interpret_stress_event(self, event: Dict, personality: Dict) -> Dict:
        """Interpret stress differently based on personality"""
        
        message = event.get('message', '').lower()
        
        # Get personality traits
        trait_scores = personality.get('traits', {})
        neuroticism = trait_scores.get('neuroticism', 0.5)
        conscientiousness = trait_scores.get('conscientiousness', 0.5)
        
        # High neuroticism + high conscientiousness
        if neuroticism > 0.7 and conscientiousness > 0.7:
            return {
                'interpreted_meaning': 'Perfectionist under pressure',
                'likely_emotional_impact': 'high_anxiety',
                'recommended_approach': 'validate_then_reframe',
                'confidence_level': 0.85,
                'notes': 'User tends to be hard on themselves. Need reassurance first.'
            }
        
        # Low neuroticism + high conscientiousness
        elif neuroticism < 0.4 and conscientiousness > 0.7:
            return {
                'interpreted_meaning': 'Competent person facing challenge',
                'likely_emotional_impact': 'manageable_concern',
                'recommended_approach': 'problem_solving_focus',
                'confidence_level': 0.8,
                'notes': 'User can handle stress. Focus on practical solutions.'
            }
        
        # High neuroticism + low conscientiousness
        elif neuroticism > 0.7 and conscientiousness < 0.4:
            return {
                'interpreted_meaning': 'Overwhelmed by situation',
                'likely_emotional_impact': 'high_distress',
                'recommended_approach': 'break_down_and_support',
                'confidence_level': 0.75,
                'notes': 'User may need help organizing and emotional support.'
            }
        
        # Default interpretation
        else:
            return {
                'interpreted_meaning': 'Person experiencing work stress',
                'likely_emotional_impact': 'moderate_concern',
                'recommended_approach': 'balanced_support',
                'confidence_level': 0.6,
                'notes': 'General stress response. Assess further.'
            }
    
    def get_user_personality(self, user_id: int) -> Dict:
        """
        Get user personality with graceful degradation
        Handles incomplete or unavailable personality data
        """
        
        # Try to get from personality profiler
        personality = self.personality_profiler.get_profile(user_id)
        
        if personality and self._is_personality_complete(personality):
            return {
                'traits': personality.get('traits', {}),
                'completeness': 1.0,
                'source': 'assessment',
                'last_updated': personality.get('last_updated'),
                'confidence': 0.9
            }
        
        # Fallback: Infer from conversation history
        inferred = self._infer_personality_from_history(user_id)
        if inferred:
            return {
                'traits': inferred.get('traits', {}),
                'completeness': inferred.get('completeness', 0.5),
                'source': 'inferred',
                'last_updated': datetime.now().isoformat(),
                'confidence': inferred.get('confidence', 0.5)
            }
        
        # Final fallback: Neutral defaults
        return self._get_neutral_personality()
    
    def _is_personality_complete(self, personality: Dict) -> bool:
        """Check if personality data is sufficiently complete"""
        if not personality:
            return False
        
        traits = personality.get('traits', {})
        required_traits = ['openness', 'conscientiousness', 'extraversion', 
                          'agreeableness', 'neuroticism']
        
        # Check if we have all Big 5 traits
        has_all_traits = all(trait in traits for trait in required_traits)
        
        # Check if data is recent (within 90 days)
        last_updated = personality.get('last_updated')
        if last_updated:
            updated_date = datetime.fromisoformat(last_updated)
            is_recent = (datetime.now() - updated_date).days < 90
        else:
            is_recent = False
        
        return has_all_traits and is_recent
    
    def _infer_personality_from_history(self, user_id: int) -> Optional[Dict]:
        """
        Infer personality from conversation patterns
        Used when formal assessment not available
        """
        
        cursor = self.db.cursor()
        
        # Get conversation history
        cursor.execute('''
            SELECT topic, mention_count, importance_score
            FROM conversation_topics
            WHERE user_id = ?
            ORDER BY mention_count DESC
            LIMIT 20
        ''', (user_id,))
        
        topics = cursor.fetchall()
        
        if not topics:
            return None
        
        # Analyze patterns
        inferred_traits = {}
        confidence_factors = []
        
        # Infer conscientiousness from goal-focused topics
        goal_topics = sum(1 for t in topics if t[0] in ['goals', 'progress', 'planning'])
        if goal_topics > 3:
            inferred_traits['conscientiousness'] = 0.7
            confidence_factors.append(0.6)
        
        # Infer neuroticism from emotional topics
        emotional_topics = sum(1 for t in topics if t[0] in ['emotions', 'anxiety', 'worry'])
        if emotional_topics > 2:
            inferred_traits['neuroticism'] = 0.7
            confidence_factors.append(0.5)
        
        # Infer openness from diverse topic range
        topic_diversity = len(set(t[0] for t in topics)) / max(len(topics), 1)
        if topic_diversity > 0.6:
            inferred_traits['openness'] = 0.7
            confidence_factors.append(0.5)
        
        # Calculate overall confidence
        avg_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.3
        completeness = len(inferred_traits) / 5.0  # Out of Big 5
        
        return {
            'traits': inferred_traits,
            'completeness': completeness,
            'confidence': avg_confidence,
            'method': 'conversation_analysis',
            'data_points': len(topics)
        }
    
    def _get_neutral_personality(self) -> Dict:
        """Return neutral personality profile when no data available"""
        return {
            'traits': {
                'openness': 0.5,
                'conscientiousness': 0.5,
                'extraversion': 0.5,
                'agreeableness': 0.5,
                'neuroticism': 0.5
            },
            'completeness': 0.0,
            'source': 'default',
            'confidence': 0.0,
            'note': 'No personality data available. Using neutral defaults.'
        }
```

---

## **2. ⚠️ Handling Incomplete/Changing Personality Data**

### **Challenge**
> Personality data may be unavailable, incomplete, or evolve over time

### **Solution: Graceful Degradation Strategy**

```python
class PersonalityDataHandler:
    """
    Handles incomplete, missing, or changing personality data gracefully
    """
    
    CONFIDENCE_THRESHOLDS = {
        'HIGH': 0.8,      # Use with confidence
        'MEDIUM': 0.5,    # Use with caution
        'LOW': 0.3,       # Minimal use, ask for clarification
        'NONE': 0.0       # Don't use for interpretation
    }
    
    def get_personality_with_confidence(self, user_id: int) -> Tuple[Dict, str]:
        """
        Returns personality data with confidence level
        
        Returns:
            (personality_data, confidence_level)
        """
        
        personality = self.interpreter.get_user_personality(user_id)
        confidence = personality.get('confidence', 0.0)
        
        if confidence >= self.CONFIDENCE_THRESHOLDS['HIGH']:
            return personality, 'HIGH'
        elif confidence >= self.CONFIDENCE_THRESHOLDS['MEDIUM']:
            return personality, 'MEDIUM'
        elif confidence >= self.CONFIDENCE_THRESHOLDS['LOW']:
            return personality, 'LOW'
        else:
            return personality, 'NONE'
    
    def should_use_personality_interpretation(self, confidence_level: str,
                                             context_importance: str) -> bool:
        """
        Decide if personality should be used for interpretation
        
        Args:
            confidence_level: HIGH, MEDIUM, LOW, NONE
            context_importance: CRITICAL, HIGH, NORMAL, LOW
        """
        
        # Critical context: Only use high-confidence personality data
        if context_importance == 'CRITICAL':
            return confidence_level == 'HIGH'
        
        # High importance: Use medium+ confidence
        elif context_importance == 'HIGH':
            return confidence_level in ['HIGH', 'MEDIUM']
        
        # Normal: Use low+ confidence
        elif context_importance == 'NORMAL':
            return confidence_level in ['HIGH', 'MEDIUM', 'LOW']
        
        # Low importance: Can experiment with any data
        else:
            return True
    
    def detect_personality_changes(self, user_id: int) -> Optional[Dict]:
        """
        Detect if user personality seems to be changing
        """
        
        cursor = self.db.cursor()
        
        # Get personality assessments over time
        cursor.execute('''
            SELECT assessment_data, timestamp
            FROM personality_assessments
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 3
        ''', (user_id,))
        
        assessments = cursor.fetchall()
        
        if len(assessments) < 2:
            return None
        
        # Compare recent assessments
        latest = json.loads(assessments[0][0])
        previous = json.loads(assessments[1][0])
        
        changes = {}
        for trait in ['openness', 'conscientiousness', 'extraversion', 
                     'agreeableness', 'neuroticism']:
            latest_score = latest.get('traits', {}).get(trait, 0.5)
            previous_score = previous.get('traits', {}).get(trait, 0.5)
            diff = abs(latest_score - previous_score)
            
            # Significant change threshold: 0.2
            if diff > 0.2:
                changes[trait] = {
                    'previous': previous_score,
                    'current': latest_score,
                    'change': diff,
                    'direction': 'increased' if latest_score > previous_score else 'decreased'
                }
        
        if changes:
            return {
                'has_changes': True,
                'changed_traits': changes,
                'assessment_dates': [a[1] for a in assessments[:2]],
                'action': 'REASSESS_RECOMMENDED'
            }
        
        return None
    
    def get_adaptive_personality_profile(self, user_id: int, 
                                        recent_behavior: Dict) -> Dict:
        """
        Create adaptive profile that adjusts based on recent behavior
        """
        
        # Get base personality
        base_personality, confidence = self.get_personality_with_confidence(user_id)
        
        # If low confidence, weight recent behavior more heavily
        if confidence == 'LOW' or confidence == 'NONE':
            behavior_weight = 0.7
        elif confidence == 'MEDIUM':
            behavior_weight = 0.3
        else:  # HIGH
            behavior_weight = 0.1
        
        # Adjust traits based on recent behavior
        adjusted_traits = base_personality.get('traits', {}).copy()
        
        # Example: Recent stress mentions → adjust neuroticism
        if recent_behavior.get('stress_mentions', 0) > 3:
            current_neuroticism = adjusted_traits.get('neuroticism', 0.5)
            adjusted_traits['neuroticism'] = (
                current_neuroticism * (1 - behavior_weight) + 
                0.7 * behavior_weight
            )
        
        # Example: Recent goal-setting → adjust conscientiousness
        if recent_behavior.get('goal_setting_count', 0) > 2:
            current_conscientiousness = adjusted_traits.get('conscientiousness', 0.5)
            adjusted_traits['conscientiousness'] = (
                current_conscientiousness * (1 - behavior_weight) + 
                0.8 * behavior_weight
            )
        
        return {
            'traits': adjusted_traits,
            'source': 'adaptive',
            'base_confidence': confidence,
            'behavior_weight': behavior_weight,
            'note': 'Adjusted based on recent behavior patterns'
        }
```

---

## **3. ✅ Explicit User Context - Trusted Priority**

### **Principle**
> User's explicit statements override all inference. Trust but verify.

```python
class ExplicitContextHandler:
    """
    Handles explicitly stated context from users
    """
    
    def extract_explicit_context(self, message: str) -> List[Dict]:
        """
        Extract explicit context statements from message
        
        Examples:
        - "I'm feeling stressed"
        - "I prefer morning workouts"
        - "My goal is to lose weight"
        """
        
        explicit_statements = []
        
        # Pattern 1: Feelings
        feeling_patterns = [
            r"I(?:'m| am) feeling (\w+)",
            r"I feel (\w+)",
            r"feeling (\w+)"
        ]
        
        for pattern in feeling_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                explicit_statements.append({
                    'type': 'emotional_state',
                    'value': match,
                    'confidence': 1.0,
                    'source': 'explicit_user_statement',
                    'priority': 'HIGH'
                })
        
        # Pattern 2: Preferences
        preference_patterns = [
            r"I prefer (?:to )?(.+?)(?:\.|$)",
            r"I like (?:to )?(.+?)(?:\.|$)",
            r"I want (?:to )?(.+?)(?:\.|$)"
        ]
        
        for pattern in preference_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                explicit_statements.append({
                    'type': 'preference',
                    'value': match,
                    'confidence': 1.0,
                    'source': 'explicit_user_statement',
                    'priority': 'HIGH'
                })
        
        # Pattern 3: Goals
        goal_patterns = [
            r"(?:my )?goal is (?:to )?(.+?)(?:\.|$)",
            r"I'm (?:trying|working) to (.+?)(?:\.|$)",
            r"I'm aiming (?:to |for )?(.+?)(?:\.|$)"
        ]
        
        for pattern in goal_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                explicit_statements.append({
                    'type': 'goal',
                    'value': match,
                    'confidence': 1.0,
                    'source': 'explicit_user_statement',
                    'priority': 'CRITICAL'
                })
        
        return explicit_statements
    
    def store_explicit_context(self, user_id: int, character: str,
                               explicit_statements: List[Dict]):
        """Store explicit context with highest priority"""
        
        for statement in explicit_statements:
            cursor = self.db.cursor()
            cursor.execute('''
                INSERT INTO conversation_context 
                (user_id, character, context_type, context_data, priority, source)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, character, context_type) 
                DO UPDATE SET 
                    context_data = ?,
                    priority = ?,
                    updated_at = CURRENT_TIMESTAMP
            ''', (
                user_id, character, 
                statement['type'], 
                json.dumps(statement),
                statement['priority'],
                'explicit_user',
                json.dumps(statement),
                statement['priority']
            ))
        
        self.db.commit()
    
    def get_context_with_priority(self, user_id: int, character: str) -> Dict:
        """
        Get context with explicit statements prioritized
        """
        
        cursor = self.db.cursor()
        
        # Get all context, ordered by priority
        cursor.execute('''
            SELECT context_type, context_data, priority, source
            FROM conversation_context
            WHERE user_id = ? AND character = ?
            ORDER BY 
                CASE priority
                    WHEN 'CRITICAL' THEN 1
                    WHEN 'HIGH' THEN 2
                    WHEN 'NORMAL' THEN 3
                    ELSE 4
                END,
                updated_at DESC
        ''', (user_id, character))
        
        contexts = cursor.fetchall()
        
        # Separate explicit from inferred
        explicit_context = []
        inferred_context = []
        
        for ctx in contexts:
            context_type, context_data, priority, source = ctx
            data = json.loads(context_data)
            
            if source == 'explicit_user':
                explicit_context.append(data)
            else:
                inferred_context.append(data)
        
        return {
            'explicit': explicit_context,  # Trusted, always used
            'inferred': inferred_context,  # Used with caution
            'priority': 'explicit_first'
        }
```

---

## **4. 🤔 Proactive Clarification System**

### **Principle**
> When uncertain, ASK. This is a proactive system, not passive.

```python
class ProactiveClarificationSystem:
    """
    Asks clarifying questions when context is uncertain
    """
    
    UNCERTAINTY_THRESHOLD = 0.6  # Ask if confidence < 60%
    
    def should_ask_clarification(self, context_interpretation: Dict,
                                 conversation_importance: str) -> Tuple[bool, Optional[str]]:
        """
        Decide if we should ask for clarification
        
        Returns:
            (should_ask, question_to_ask)
        """
        
        confidence = context_interpretation.get('confidence_level', 0.0)
        
        # High-importance conversations: ask if any uncertainty
        if conversation_importance in ['CRITICAL', 'HIGH']:
            if confidence < 0.8:
                question = self._generate_clarification_question(
                    context_interpretation, 
                    confidence
                )
                return True, question
        
        # Normal conversations: ask if significant uncertainty
        elif conversation_importance == 'NORMAL':
            if confidence < self.UNCERTAINTY_THRESHOLD:
                question = self._generate_clarification_question(
                    context_interpretation,
                    confidence
                )
                return True, question
        
        return False, None
    
    def _generate_clarification_question(self, interpretation: Dict,
                                        confidence: float) -> str:
        """
        Generate a natural clarifying question
        """
        
        meaning = interpretation.get('interpreted_meaning', '')
        
        # Template based on confidence level
        if confidence < 0.3:
            # Very uncertain - broad question
            return (
                "I want to make sure I understand correctly. "
                "Can you tell me a bit more about how you're feeling about this?"
            )
        
        elif confidence < 0.6:
            # Moderate uncertainty - specific question
            return (
                f"It sounds like you might be {meaning}. "
                "Is that how you're experiencing it, or is there more to it?"
            )
        
        else:
            # Slight uncertainty - validation question
            return (
                f"Just checking - this seems like {meaning}. "
                "Does that resonate with you?"
            )
    
    def detect_conversation_importance(self, message: str, 
                                      context: Dict) -> str:
        """
        Determine importance level of current conversation
        """
        
        # Critical indicators
        critical_keywords = [
            'crisis', 'emergency', 'urgent', 'desperate',
            'can\'t cope', 'giving up', 'suicide', 'harm'
        ]
        
        if any(kw in message.lower() for kw in critical_keywords):
            return 'CRITICAL'
        
        # High importance indicators
        high_keywords = [
            'important', 'major', 'significant', 'life-changing',
            'decision', 'stuck', 'lost', 'confused'
        ]
        
        if any(kw in message.lower() for kw in high_keywords):
            return 'HIGH'
        
        # Check context - repeated topic indicates importance
        topic_mentions = context.get('topic_mentions', 0)
        if topic_mentions > 5:
            return 'HIGH'
        
        return 'NORMAL'
    
    def generate_proactive_question(self, user_id: int, character: str,
                                   context: Dict) -> Optional[str]:
        """
        Generate proactive questions to deepen understanding
        
        Returns question when it would be valuable to ask
        """
        
        # Analyze context gaps
        gaps = self._identify_context_gaps(context)
        
        if not gaps:
            return None
        
        # Prioritize gaps
        priority_gap = gaps[0]  # Most important gap
        
        # Generate question for the gap
        questions = {
            'unclear_goal': "What would success look like for you in this area?",
            'missing_motivation': "What's driving your interest in this?",
            'unclear_timeline': "What timeframe are you thinking about for this?",
            'missing_obstacles': "What's been holding you back from this?",
            'unclear_emotional_state': "How are you feeling about this?",
            'missing_support_system': "Who's supporting you in this journey?",
            'unclear_values': "What makes this important to you?"
        }
        
        return questions.get(priority_gap)
    
    def _identify_context_gaps(self, context: Dict) -> List[str]:
        """Identify what's missing in our understanding"""
        
        gaps = []
        
        # Check for common gaps
        if not context.get('user_goals'):
            gaps.append('unclear_goal')
        
        if not context.get('emotional_state'):
            gaps.append('unclear_emotional_state')
        
        if context.get('challenge_mentioned') and not context.get('obstacles_identified'):
            gaps.append('missing_obstacles')
        
        if context.get('goal_mentioned') and not context.get('timeline'):
            gaps.append('unclear_timeline')
        
        return gaps
```

---

## **5. 📊 Dual-Layer History: Primary + Analytical**

### **Principle**
> Store raw data for truth, analytical data for insights

```python
class DualLayerHistorySystem:
    """
    Maintains two layers of history:
    1. Primary (Raw) - What actually happened
    2. Secondary (Analytical) - What it means
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._init_dual_layer_tables()
    
    def _init_dual_layer_tables(self):
        """Create tables for dual-layer history"""
        
        cursor = self.db.cursor()
        
        # PRIMARY LAYER - Raw conversation data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history_primary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Raw data
                user_message TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                response_type TEXT,  -- quick_reply, full_ai
                
                -- Metadata
                session_id TEXT,
                message_length INTEGER,
                response_time_ms INTEGER,
                
                -- Never modify - this is source of truth
                is_primary BOOLEAN DEFAULT 1,
                
                INDEX idx_user_time (user_id, timestamp),
                INDEX idx_session (session_id)
            )
        ''')
        
        # SECONDARY LAYER - Analytical interpretation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history_secondary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                primary_id INTEGER NOT NULL,  -- Links to primary
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Interpreted data
                detected_intent TEXT,
                emotional_tone TEXT,
                topics_extracted TEXT,  -- JSON array
                personality_interpretation TEXT,  -- JSON
                
                -- Context at time of message
                context_snapshot TEXT,  -- JSON
                
                -- Insights
                progress_indicators TEXT,  -- JSON
                concerns_identified TEXT,  -- JSON
                opportunities_spotted TEXT,  -- JSON
                
                -- Guidance data
                suggested_actions TEXT,  -- JSON
                follow_up_recommended TEXT,
                
                -- Meta
                analysis_confidence FLOAT,
                analysis_version TEXT,  -- For future re-analysis
                
                FOREIGN KEY (primary_id) REFERENCES history_primary(id),
                INDEX idx_user_analysis (user_id, analysis_timestamp)
            )
        ''')
        
        # PROGRESS TRACKING - Long-term patterns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                
                -- What we're tracking
                goal_category TEXT,  -- fitness, career, mental_health, etc.
                metric_name TEXT,
                
                -- Timeline
                tracking_start_date TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Data points (JSON array of {date, value, note})
                data_points TEXT NOT NULL,
                
                -- Trend analysis
                trend_direction TEXT,  -- improving, declining, stable, unclear
                trend_confidence FLOAT,
                
                -- Context
                related_primary_ids TEXT,  -- JSON array of primary history IDs
                
                INDEX idx_user_goal (user_id, goal_category)
            )
        ''')
        
        self.db.commit()
    
    def store_interaction(self, user_id: int, character: str,
                         user_message: str, assistant_response: str,
                         response_type: str, metadata: Dict) -> int:
        """
        Store interaction in PRIMARY layer (raw data)
        
        Returns: primary_id for linking secondary analysis
        """
        
        cursor = self.db.cursor()
        
        cursor.execute('''
            INSERT INTO history_primary 
            (user_id, character, user_message, assistant_response, 
             response_type, session_id, message_length, response_time_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, character, user_message, assistant_response,
            response_type,
            metadata.get('session_id'),
            len(user_message),
            metadata.get('response_time_ms', 0)
        ))
        
        primary_id = cursor.lastrowid
        self.db.commit()
        
        return primary_id
    
    def analyze_and_store_secondary(self, primary_id: int,
                                   interpretation: Dict,
                                   context: Dict) -> int:
        """
        Analyze and store in SECONDARY layer (interpretations)
        """
        
        cursor = self.db.cursor()
        
        # Get primary record to analyze
        cursor.execute('''
            SELECT user_id, character, user_message, assistant_response
            FROM history_primary WHERE id = ?
        ''', (primary_id,))
        
        row = cursor.fetchone()
        if not row:
            return -1
        
        user_id, character, user_message, assistant_response = row
        
        # Extract insights
        topics = self._extract_topics(user_message + " " + assistant_response)
        emotional_tone = self._detect_emotional_tone(user_message)
        progress_indicators = self._detect_progress_indicators(user_message)
        concerns = self._identify_concerns(user_message, context)
        opportunities = self._spot_opportunities(user_message, context)
        
        # Store analysis
        cursor.execute('''
            INSERT INTO history_secondary 
            (primary_id, user_id, character, detected_intent, emotional_tone,
             topics_extracted, personality_interpretation, context_snapshot,
             progress_indicators, concerns_identified, opportunities_spotted,
             analysis_confidence, analysis_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            primary_id, user_id, character,
            interpretation.get('detected_intent'),
            emotional_tone,
            json.dumps(topics),
            json.dumps(interpretation.get('personality_context', {})),
            json.dumps(context),
            json.dumps(progress_indicators),
            json.dumps(concerns),
            json.dumps(opportunities),
            interpretation.get('confidence_level', 0.0),
            'v1.0'
        ))
        
        secondary_id = cursor.lastrowid
        self.db.commit()
        
        return secondary_id
    
    def get_conversation_history(self, user_id: int, character: str,
                                layer: str = 'both',
                                limit: int = 20) -> List[Dict]:
        """
        Retrieve history from specified layer(s)
        
        Args:
            layer: 'primary', 'secondary', or 'both'
        """
        
        cursor = self.db.cursor()
        
        if layer == 'primary' or layer == 'both':
            cursor.execute('''
                SELECT id, timestamp, user_message, assistant_response, response_type
                FROM history_primary
                WHERE user_id = ? AND character = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, character, limit))
            
            primary_records = [
                {
                    'id': row[0],
                    'timestamp': row[1],
                    'user_message': row[2],
                    'assistant_response': row[3],
                    'response_type': row[4],
                    'layer': 'primary'
                }
                for row in cursor.fetchall()
            ]
        else:
            primary_records = []
        
        if layer == 'secondary' or layer == 'both':
            cursor.execute('''
                SELECT s.id, s.primary_id, s.analysis_timestamp,
                       s.detected_intent, s.emotional_tone, s.topics_extracted,
                       s.progress_indicators, s.concerns_identified,
                       s.opportunities_spotted, s.analysis_confidence
                FROM history_secondary s
                WHERE s.user_id = ? AND s.character = ?
                ORDER BY s.analysis_timestamp DESC
                LIMIT ?
            ''', (user_id, character, limit))
            
            secondary_records = [
                {
                    'id': row[0],
                    'primary_id': row[1],
                    'timestamp': row[2],
                    'intent': row[3],
                    'emotional_tone': row[4],
                    'topics': json.loads(row[5]) if row[5] else [],
                    'progress': json.loads(row[6]) if row[6] else {},
                    'concerns': json.loads(row[7]) if row[7] else [],
                    'opportunities': json.loads(row[8]) if row[8] else [],
                    'confidence': row[9],
                    'layer': 'secondary'
                }
                for row in cursor.fetchall()
            ]
        else:
            secondary_records = []
        
        if layer == 'both':
            # Merge by linking primary_id
            merged = []
            for primary in primary_records:
                # Find matching secondary
                secondary = next(
                    (s for s in secondary_records if s['primary_id'] == primary['id']),
                    None
                )
                merged.append({
                    'primary': primary,
                    'secondary': secondary
                })
            return merged
        elif layer == 'primary':
            return primary_records
        else:
            return secondary_records
    
    def update_progress_tracking(self, user_id: int, character: str,
                                goal_category: str, metric_name: str,
                                value: Any, note: str = ''):
        """
        Update long-term progress tracking
        """
        
        cursor = self.db.cursor()
        
        # Get or create progress tracker
        cursor.execute('''
            SELECT id, data_points FROM history_progress
            WHERE user_id = ? AND character = ? 
            AND goal_category = ? AND metric_name = ?
        ''', (user_id, character, goal_category, metric_name))
        
        row = cursor.fetchone()
        
        # New data point
        new_point = {
            'date': datetime.now().isoformat(),
            'value': value,
            'note': note
        }
        
        if row:
            # Update existing
            tracker_id, data_points_json = row
            data_points = json.loads(data_points_json)
            data_points.append(new_point)
            
            # Analyze trend
            trend = self._analyze_trend(data_points)
            
            cursor.execute('''
                UPDATE history_progress
                SET data_points = ?,
                    last_updated = CURRENT_TIMESTAMP,
                    trend_direction = ?,
                    trend_confidence = ?
                WHERE id = ?
            ''', (
                json.dumps(data_points),
                trend['direction'],
                trend['confidence'],
                tracker_id
            ))
        else:
            # Create new
            cursor.execute('''
                INSERT INTO history_progress
                (user_id, character, goal_category, metric_name,
                 tracking_start_date, data_points, trend_direction, trend_confidence)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?)
            ''', (
                user_id, character, goal_category, metric_name,
                json.dumps([new_point]),
                'unclear',  # Not enough data yet
                0.0
            ))
        
        self.db.commit()
    
    def _analyze_trend(self, data_points: List[Dict]) -> Dict:
        """Analyze trend from data points"""
        
        if len(data_points) < 3:
            return {'direction': 'unclear', 'confidence': 0.0}
        
        # Simple linear trend analysis
        recent_points = data_points[-5:]  # Last 5 points
        values = [p['value'] for p in recent_points if isinstance(p['value'], (int, float))]
        
        if len(values) < 3:
            return {'direction': 'unclear', 'confidence': 0.0}
        
        # Calculate trend
        avg_first_half = sum(values[:len(values)//2]) / (len(values)//2)
        avg_second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        difference = avg_second_half - avg_first_half
        percent_change = abs(difference / avg_first_half) if avg_first_half != 0 else 0
        
        # Determine direction
        if percent_change < 0.05:
            direction = 'stable'
            confidence = 0.7
        elif difference > 0:
            direction = 'improving'
            confidence = min(0.9, 0.5 + percent_change)
        else:
            direction = 'declining'
            confidence = min(0.9, 0.5 + percent_change)
        
        return {'direction': direction, 'confidence': confidence}
    
    # Helper methods for analysis
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text"""
        # Reuse from context analyzer
        return []  # Implementation in context_analyzer
    
    def _detect_emotional_tone(self, text: str) -> str:
        """Detect emotional tone"""
        emotional_words = {
            'positive': ['happy', 'excited', 'great', 'awesome', 'love'],
            'negative': ['sad', 'angry', 'frustrated', 'upset', 'hate'],
            'anxious': ['worried', 'anxious', 'nervous', 'scared', 'afraid'],
            'neutral': []
        }
        
        text_lower = text.lower()
        for tone, words in emotional_words.items():
            if any(word in text_lower for word in words):
                return tone
        
        return 'neutral'
    
    def _detect_progress_indicators(self, text: str) -> Dict:
        """Detect indicators of progress"""
        progress_keywords = {
            'achievement': ['completed', 'achieved', 'succeeded', 'won', 'finished'],
            'improvement': ['better', 'improved', 'progress', 'growing'],
            'setback': ['failed', 'couldn't', 'didn\'t work', 'setback'],
            'milestone': ['milestone', 'breakthrough', 'first time']
        }
        
        detected = {}
        text_lower = text.lower()
        
        for category, keywords in progress_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected[category] = True
                    break
        
        return detected
    
    def _identify_concerns(self, text: str, context: Dict) -> List[str]:
        """Identify concerns or challenges"""
        concerns = []
        
        concern_patterns = [
            r"I'm (?:worried|concerned|anxious) about (.+?)(?:\.|$)",
            r"struggling with (.+?)(?:\.|$)",
            r"having trouble (.+?)(?:\.|$)"
        ]
        
        for pattern in concern_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            concerns.extend(matches)
        
        return concerns
    
    def _spot_opportunities(self, text: str, context: Dict) -> List[str]:
        """Spot opportunities for growth or intervention"""
        opportunities = []
        
        # Opportunity: User mentions wanting to improve
        if 'want to' in text.lower() or 'would like to' in text.lower():
            opportunities.append('expressed_desire_for_change')
        
        # Opportunity: User asks for advice
        if '?' in text and any(word in text.lower() for word in ['how', 'what', 'should']):
            opportunities.append('seeking_guidance')
        
        # Opportunity: User shows readiness
        if any(word in text.lower() for word in ['ready', 'prepared', 'let\'s do']):
            opportunities.append('high_motivation_moment')
        
        return opportunities
```

---

## **6. 📋 System Design Principles (Core Documentation)**

```markdown
# INTELLIGENT CONTEXT SYSTEM - CORE PRINCIPLES

## These principles guide ALL system design decisions

### 1. PERSONALITY-AWARE INTERPRETATION
- Context meaning depends on WHO the user is
- Same event → different implications for different personalities
- ALWAYS consider personality in interpretation
- Gracefully handle incomplete/missing personality data

### 2. EXPLICIT OVER INFERRED
- User's explicit statements = highest priority
- Trust user honesty (assume good faith)
- Explicit context overrides all inference
- Store with CRITICAL priority level

### 3. PROACTIVE, NOT PASSIVE
- System can and should ask clarifying questions
- Don't guess when uncertain - ASK
- Generate proactive questions to deepen understanding
- This is a coaching system, not just a chatbot

### 4. DUAL-LAYER HISTORY
- PRIMARY layer = raw data (never modify)
- SECONDARY layer = analytical interpretation (can evolve)
- Enables future re-analysis with better methods
- Progress tracking = long-term view

### 5. LONG-TERM CONSTRUCTIVE GUIDANCE
- Prime goal: Inspire constructive action over time
- Not just conversation - transformation
- Track progress, spot trends, identify opportunities
- Guide users toward growth, not just chat

### 6. GRACEFUL DEGRADATION
- Handle missing data elegantly
- Use confidence levels appropriately
- Adapt to incomplete information
- Never fail hard - always provide value

### 7. EVOLVING UNDERSTANDING
- Personality can change over time
- Context interpretation can improve
- Re-analyze history with new methods
- Adaptive profiles based on recent behavior

## Application
These principles apply to:
- All context-related features
- All user interaction patterns
- All data storage decisions
- All AI prompting strategies
- All system architecture choices

Consult these when making ANY design decision.
```

---

## **Summary: What Makes This Intelligent**

| Traditional System | Intelligent System |
|-------------------|-------------------|
| Recalls what was said | Interprets what it means |
| Generic responses | Personality-aware responses |
| Passive recorder | Proactive questioner |
| Single data layer | Dual-layer (raw + analytical) |
| Short-term memory | Long-term progress tracking |
| Conversation tool | Transformation tool |

**This system doesn't just remember - it understands, interprets, and guides.** 🧠🎯

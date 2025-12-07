# Personality Data Decision Logic for Real-Time Use

## **The Core Question**

When the system needs to make a decision RIGHT NOW:
- **Which character should respond?**
- **What tone/style to use?**
- **What action plan to recommend?**
- **How to interpret the user's message?**

**Which personality data do we trust?**

---

## **The Answer: Priority-Based Decision with Context**

### **Decision Tree:**

```
┌─ Need personality data to make decision
│
├─ 1. Check ASSESSMENT (highest trust)
│   ├─ Exists AND < 3 months old?
│   │   └─ ✅ USE IT (confidence: 0.95)
│   │
│   ├─ Exists but 3-12 months old?
│   │   ├─ Has inferred data?
│   │   │   └─ ✅ BLEND: 60% assessment + 40% inferred
│   │   └─ No inferred?
│   │       └─ ✅ USE assessment (confidence: 0.75)
│   │
│   └─ Exists but > 12 months old?
│       ├─ Has inferred data?
│       │   └─ ✅ USE inferred (assessment too stale)
│       └─ No inferred?
│           └─ ✅ USE assessment (confidence: 0.50, note staleness)
│
├─ 2. No assessment? Check INFERRED
│   ├─ Exists with confidence > 0.6?
│   │   └─ ✅ USE IT (confidence from inference engine)
│   │
│   ├─ Exists but confidence < 0.6?
│   │   └─ ✅ USE IT but FLAG LOW CONFIDENCE
│   │
│   └─ No inferred data?
│       └─ ⬇️ Fall to defaults
│
└─ 3. No data at all?
    └─ ✅ USE NEUTRAL DEFAULTS (confidence: 0.0)
        └─ Flag: "Should offer personality assessment"
```

---

## **Implementation: Smart Personality Resolver**

```python
class PersonalityResolver:
    """
    Resolves the BEST personality data to use for real-time decisions
    Handles priority, blending, and confidence scoring
    """
    
    def __init__(self, db: IntegratedDatabase):
        self.db = db
        self.cache = {}  # Cache results for session
        
    def get_decision_ready_profile(
        self, 
        user_id: int,
        context: str = None  # 'character_selection', 'response_tone', 'action_plan'
    ) -> Dict[str, Any]:
        """
        Get personality profile optimized for making decisions
        
        Returns:
        {
            'traits': {
                'openness': 0.80,
                'conscientiousness': 0.70,
                ...
            },
            'confidence': 0.85,  # Overall confidence 0-1
            'source': 'assessment',  # or 'inferred', 'blended', 'default'
            'metadata': {
                'assessment_age_days': 45,
                'assessment_exists': True,
                'inferred_exists': True,
                'inferred_confidence': 0.72,
                'blend_ratio': None  # or {'assessment': 0.6, 'inferred': 0.4}
            },
            'recommendations': {
                'reliability': 'high',  # 'high', 'medium', 'low'
                'should_reassess': False,
                'reasoning': 'Recent assessment data available'
            }
        }
        """
        
        # Check cache first (valid for 5 minutes)
        cache_key = f"{user_id}_{context}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['timestamp'] < 300:  # 5 min
                return cached['data']
        
        # Get assessment data
        assessment = self._get_assessment_data(user_id)
        
        # Get inferred data
        inferred = self._get_inferred_data(user_id)
        
        # Apply decision logic
        result = self._resolve_personality(assessment, inferred, context)
        
        # Cache result
        self.cache[cache_key] = {
            'data': result,
            'timestamp': time.time()
        }
        
        return result
    
    def _get_assessment_data(self, user_id: int) -> Dict:
        """Get latest assessment with age calculation"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                openness, conscientiousness, extraversion, 
                agreeableness, neuroticism,
                completed_at,
                julianday('now') - julianday(completed_at) as age_days
            FROM assessment_history
            WHERE user_id = ?
            ORDER BY completed_at DESC
            LIMIT 1
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        return {
            'traits': {
                'openness': row[0],
                'conscientiousness': row[1],
                'extraversion': row[2],
                'agreeableness': row[3],
                'neuroticism': row[4]
            },
            'completed_at': row[5],
            'age_days': row[6]
        }
    
    def _get_inferred_data(self, user_id: int) -> Dict:
        """Get inferred traits with metadata"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                openness, conscientiousness, extraversion,
                agreeableness, neuroticism,
                confidence, message_count, last_updated
            FROM inferred_traits
            WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        return {
            'traits': {
                'openness': row[0],
                'conscientiousness': row[1],
                'extraversion': row[2],
                'agreeableness': row[3],
                'neuroticism': row[4]
            },
            'confidence': row[5],
            'message_count': row[6],
            'last_updated': row[7]
        }
    
    def _resolve_personality(
        self, 
        assessment: Dict, 
        inferred: Dict,
        context: str
    ) -> Dict:
        """Apply decision logic to choose best personality data"""
        
        # CASE 1: Fresh assessment (< 3 months)
        if assessment and assessment['age_days'] < 90:
            return {
                'traits': assessment['traits'],
                'confidence': 0.95,
                'source': 'assessment',
                'metadata': {
                    'assessment_age_days': assessment['age_days'],
                    'assessment_exists': True,
                    'inferred_exists': inferred is not None,
                    'inferred_confidence': inferred['confidence'] if inferred else None,
                    'blend_ratio': None
                },
                'recommendations': {
                    'reliability': 'high',
                    'should_reassess': False,
                    'reasoning': f'Recent assessment ({int(assessment["age_days"])} days old)'
                }
            }
        
        # CASE 2: Moderately old assessment (3-12 months) + inferred data
        if assessment and 90 <= assessment['age_days'] < 365 and inferred:
            # BLEND: Assessment is getting old, but still valuable
            # Use 60% assessment, 40% inferred
            blended_traits = {}
            for trait in ['openness', 'conscientiousness', 'extraversion', 
                         'agreeableness', 'neuroticism']:
                blended_traits[trait] = (
                    0.6 * assessment['traits'][trait] + 
                    0.4 * inferred['traits'][trait]
                )
            
            return {
                'traits': blended_traits,
                'confidence': 0.75,
                'source': 'blended',
                'metadata': {
                    'assessment_age_days': assessment['age_days'],
                    'assessment_exists': True,
                    'inferred_exists': True,
                    'inferred_confidence': inferred['confidence'],
                    'blend_ratio': {'assessment': 0.6, 'inferred': 0.4}
                },
                'recommendations': {
                    'reliability': 'medium',
                    'should_reassess': True,
                    'reasoning': f'Assessment is {int(assessment["age_days"])} days old, blended with recent conversation patterns'
                }
            }
        
        # CASE 3: Old assessment (3-12 months) but no inferred data
        if assessment and 90 <= assessment['age_days'] < 365 and not inferred:
            return {
                'traits': assessment['traits'],
                'confidence': 0.65,
                'source': 'assessment',
                'metadata': {
                    'assessment_age_days': assessment['age_days'],
                    'assessment_exists': True,
                    'inferred_exists': False,
                    'inferred_confidence': None,
                    'blend_ratio': None
                },
                'recommendations': {
                    'reliability': 'medium',
                    'should_reassess': True,
                    'reasoning': f'Assessment is {int(assessment["age_days"])} days old, no recent conversation data'
                }
            }
        
        # CASE 4: Very old assessment (> 12 months) but has inferred
        if assessment and assessment['age_days'] >= 365 and inferred:
            # Inferred data more reliable than 1+ year old assessment
            return {
                'traits': inferred['traits'],
                'confidence': inferred['confidence'],
                'source': 'inferred',
                'metadata': {
                    'assessment_age_days': assessment['age_days'],
                    'assessment_exists': True,
                    'inferred_exists': True,
                    'inferred_confidence': inferred['confidence'],
                    'blend_ratio': None
                },
                'recommendations': {
                    'reliability': 'medium' if inferred['confidence'] > 0.6 else 'low',
                    'should_reassess': True,
                    'reasoning': f'Assessment is very old ({int(assessment["age_days"])} days), using recent conversation patterns'
                }
            }
        
        # CASE 5: Very old assessment, no inferred
        if assessment and assessment['age_days'] >= 365 and not inferred:
            return {
                'traits': assessment['traits'],
                'confidence': 0.50,
                'source': 'assessment',
                'metadata': {
                    'assessment_age_days': assessment['age_days'],
                    'assessment_exists': True,
                    'inferred_exists': False,
                    'inferred_confidence': None,
                    'blend_ratio': None
                },
                'recommendations': {
                    'reliability': 'low',
                    'should_reassess': True,
                    'reasoning': f'Assessment is very old ({int(assessment["age_days"])} days), urgently needs reassessment'
                }
            }
        
        # CASE 6: No assessment, has inferred
        if not assessment and inferred:
            reliability = 'medium' if inferred['confidence'] > 0.6 else 'low'
            return {
                'traits': inferred['traits'],
                'confidence': inferred['confidence'],
                'source': 'inferred',
                'metadata': {
                    'assessment_age_days': None,
                    'assessment_exists': False,
                    'inferred_exists': True,
                    'inferred_confidence': inferred['confidence'],
                    'blend_ratio': None
                },
                'recommendations': {
                    'reliability': reliability,
                    'should_reassess': True,
                    'reasoning': f'No formal assessment, using inferred data from {inferred["message_count"]} messages'
                }
            }
        
        # CASE 7: No data at all - defaults
        return {
            'traits': {
                'openness': 0.5,
                'conscientiousness': 0.5,
                'extraversion': 0.5,
                'agreeableness': 0.5,
                'neuroticism': 0.5
            },
            'confidence': 0.0,
            'source': 'default',
            'metadata': {
                'assessment_age_days': None,
                'assessment_exists': False,
                'inferred_exists': False,
                'inferred_confidence': None,
                'blend_ratio': None
            },
            'recommendations': {
                'reliability': 'none',
                'should_reassess': True,
                'reasoning': 'No personality data available, using neutral defaults'
            }
        }
```

---

## **Usage in Real-Time Decisions**

### **1. Character Selection**

```python
def select_best_character(user_id: int, situation: str) -> str:
    """Choose which character to use for helping the user"""
    
    # Get best available personality data
    resolver = PersonalityResolver(db)
    profile = resolver.get_decision_ready_profile(
        user_id, 
        context='character_selection'
    )
    
    # Use confidence to adjust approach
    if profile['confidence'] < 0.5:
        # Low confidence - use versatile character
        print(f"⚠️ Low personality confidence ({profile['confidence']}), using Coach (versatile)")
        return 'coach'
    
    # Analyze situation + personality
    if situation == 'struggling_with_decision':
        # High Openness + Low Conscientiousness → Use Sage (philosophical)
        if profile['traits']['openness'] > 0.7 and profile['traits']['conscientiousness'] < 0.5:
            return 'sage'
        # Low Openness + High Conscientiousness → Use Coach (structured)
        elif profile['traits']['openness'] < 0.5 and profile['traits']['conscientiousness'] > 0.7:
            return 'coach'
    
    elif situation == 'emotional_distress':
        # High Neuroticism → Use Psychologist (supportive)
        if profile['traits']['neuroticism'] > 0.6:
            return 'psychologist'
        # Low Neuroticism + High Openness → Use Sage (reflective)
        else:
            return 'sage'
    
    # Default based on confidence
    if profile['source'] == 'assessment':
        print(f"✅ Using assessment data (confidence: {profile['confidence']})")
    elif profile['source'] == 'blended':
        print(f"📊 Using blended data (confidence: {profile['confidence']})")
    elif profile['source'] == 'inferred':
        print(f"🔍 Using inferred data (confidence: {profile['confidence']})")
    
    return 'coach'  # Default safe choice
```

### **2. Response Tone**

```python
def determine_response_tone(user_id: int, message: str) -> Dict:
    """Decide how to respond based on personality"""
    
    resolver = PersonalityResolver(db)
    profile = resolver.get_decision_ready_profile(
        user_id,
        context='response_tone'
    )
    
    # Build response parameters
    tone = {
        'formality': 'casual',
        'verbosity': 'moderate',
        'directness': 'balanced',
        'empathy_level': 'medium'
    }
    
    # Adjust based on traits (if confidence is reasonable)
    if profile['confidence'] > 0.6:
        # High Openness → More exploratory, less structured
        if profile['traits']['openness'] > 0.7:
            tone['verbosity'] = 'detailed'
            tone['formality'] = 'casual'
        
        # High Conscientiousness → More structured, organized
        if profile['traits']['conscientiousness'] > 0.7:
            tone['directness'] = 'direct'
            tone['verbosity'] = 'concise'
        
        # High Extraversion → More enthusiastic, social
        if profile['traits']['extraversion'] > 0.7:
            tone['formality'] = 'friendly'
        
        # High Neuroticism → More empathetic, careful
        if profile['traits']['neuroticism'] > 0.6:
            tone['empathy_level'] = 'high'
            tone['directness'] = 'gentle'
    
    # Add metadata for logging
    tone['_personality_source'] = profile['source']
    tone['_confidence'] = profile['confidence']
    
    return tone
```

### **3. Action Plan Recommendation**

```python
def recommend_action_plan(user_id: int, goal: str) -> Dict:
    """Recommend action plan based on personality"""
    
    resolver = PersonalityResolver(db)
    profile = resolver.get_decision_ready_profile(
        user_id,
        context='action_plan'
    )
    
    plan = {
        'approach': 'balanced',
        'structure_level': 'medium',
        'check_in_frequency': 'weekly',
        'detail_level': 'medium'
    }
    
    # Only personalize if confidence is good
    if profile['confidence'] > 0.7:
        # High Conscientiousness → Detailed, structured plan
        if profile['traits']['conscientiousness'] > 0.7:
            plan['approach'] = 'structured'
            plan['structure_level'] = 'high'
            plan['detail_level'] = 'detailed'
            plan['check_in_frequency'] = 'daily'
        
        # Low Conscientiousness + High Openness → Flexible, exploratory
        elif (profile['traits']['conscientiousness'] < 0.5 and 
              profile['traits']['openness'] > 0.7):
            plan['approach'] = 'exploratory'
            plan['structure_level'] = 'low'
            plan['detail_level'] = 'overview'
            plan['check_in_frequency'] = 'biweekly'
    
    # Warn if using low-confidence data
    elif profile['confidence'] < 0.5:
        plan['_warning'] = f"Using {profile['source']} data with low confidence"
        plan['_should_assess'] = True
    
    plan['_personality_source'] = profile['source']
    plan['_confidence'] = profile['confidence']
    
    return plan
```

---

## **Key Principles**

### **1. Confidence Thresholds**

```python
if confidence >= 0.9:  # Excellent
    # Full personalization, trust all decisions
    
elif confidence >= 0.7:  # Good
    # Standard personalization
    
elif confidence >= 0.5:  # Moderate
    # Conservative personalization, prefer safe choices
    
elif confidence >= 0.3:  # Low
    # Minimal personalization, use versatile defaults
    
else:  # < 0.3: Very low
    # No personalization, suggest assessment
```

### **2. Context-Specific Decisions**

Different decisions need different confidence levels:

```python
CONFIDENCE_REQUIREMENTS = {
    'character_selection': 0.6,     # Medium confidence OK
    'response_tone': 0.7,            # Higher confidence needed
    'action_plan': 0.8,              # High confidence needed
    'crisis_intervention': 0.9       # Very high confidence needed
}
```

### **3. Graceful Degradation**

```python
if profile['confidence'] < required_confidence:
    # Fall back to safer, more general approach
    # But LOG the decision for later analysis
    logger.info(
        f"Personality confidence too low ({profile['confidence']} < {required}), "
        f"using default approach"
    )
```

---

## **Summary** 🎯

**Your Question:** How do we decide which personality data to use for real-time decisions?

**Answer:**
1. ✅ **Use `PersonalityResolver`** - Smart decision logic
2. ✅ **Priority system** - Assessment → Inferred → Default
3. ✅ **Age-based blending** - Mix old assessment with fresh inference
4. ✅ **Confidence-based adaptation** - Reduce personalization if low confidence
5. ✅ **Context-aware** - Different decisions need different confidence
6. ✅ **Graceful degradation** - Always have a safe fallback

**Result:**
- Fast, cached lookups
- Clear decision logic
- No data loss
- Handles all edge cases
- Production-ready

Should I implement this `PersonalityResolver` class?

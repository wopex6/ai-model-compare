"""
Simulated User Agent System

Creates AI-powered agents that act like real users, pumping conversations
through the system's API endpoints. This exercises the FULL pipeline:
- Authentication
- Conversation creation
- Message sending → AI response
- Character matching & effectiveness learning
- Proactive clarification
- Character collaboration
- Greeting system interaction

Each agent has a unique persona with:
- Personality traits & communication style
- Life situations & concerns
- Conversation patterns (topic starters, follow-ups, emotional arcs)
- Realistic timing between messages
"""

import requests
import json
import time
import random
import uuid
import sys
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

# ================================================================
# USER PERSONAS
# ================================================================

@dataclass
class UserPersona:
    """Defines a simulated user's personality and conversation patterns"""
    name: str
    password: str
    email: str
    communication_style: str  # brief, verbose, emotional, analytical
    personality_summary: str
    
    # Topics this user naturally gravitates toward
    situation_topics: Dict[str, List[str]] = field(default_factory=dict)
    
    # How they respond to AI (follow-up patterns)
    follow_up_styles: List[str] = field(default_factory=list)
    
    # Emotional range (affects message tone)
    emotional_range: Tuple[float, float] = (0.3, 0.7)  # min, max positivity
    
    # Messages per conversation (min, max)
    messages_per_convo: Tuple[int, int] = (3, 8)
    
    # Seconds between messages (min, max)  
    delay_between_msgs: Tuple[float, float] = (2.0, 5.0)


# Pre-defined personas that cover diverse situations
PERSONAS = [
    UserPersona(
        name="SimUser_Alex",
        password="SimTest123!",
        email="sim_alex@test.com",
        communication_style="analytical",
        personality_summary="Software engineer in mid-career transition. Logical, structured thinker. Struggles with work-life balance.",
        situation_topics={
            'career_guidance': [
                "I'm thinking about switching from backend engineering to product management. Is this a good move?",
                "My company just announced layoffs. I wasn't affected but I'm worried about my future there.",
                "I got a job offer with 30% more pay but the company culture seems toxic. What should I consider?",
                "I've been in the same role for 4 years. How do I know when it's time to move on?",
            ],
            'skill_development': [
                "I want to learn machine learning but I'm overwhelmed by where to start. Can you help me make a plan?",
                "How do I get better at public speaking? I freeze up in meetings.",
                "I need to improve my leadership skills. I just got promoted to team lead.",
            ],
            'financial': [
                "I have 50k in savings and 20k in student loans. Should I pay off the loans or invest?",
                "I'm 35 and haven't started saving for retirement seriously. Am I too late?",
                "My partner and I disagree about how to budget. How do we find middle ground?",
            ],
            'emotional': [
                "I feel burnt out. I used to love coding but now I dread opening my laptop.",
                "I'm jealous of my friends who seem more successful than me. How do I deal with this?",
            ],
        },
        follow_up_styles=[
            "That makes sense. But what about {topic}?",
            "Can you be more specific about the steps?",
            "I've tried that before and it didn't work. What else can I try?",
            "How long would this typically take?",
            "What's the biggest risk I should watch out for?",
        ],
        emotional_range=(0.4, 0.7),
        messages_per_convo=(4, 8),
        delay_between_msgs=(2.0, 4.0),
    ),
    
    UserPersona(
        name="SimUser_Maya",
        password="SimTest123!",
        email="sim_maya@test.com",
        communication_style="emotional",
        personality_summary="Single mother of two, dealing with anxiety. Very empathetic, sometimes overwhelmed. Values emotional validation.",
        situation_topics={
            'emotional': [
                "I had a panic attack at the grocery store today. I feel so embarrassed.",
                "I can't stop worrying about my kids' future. The anxiety keeps me up at night.",
                "I feel like I'm failing as a mother. Other moms seem to have it all together.",
                "I got angry at my 5-year-old today and now I feel terrible guilt.",
                "Some days I just want to cry but I can't because I have to be strong for my kids.",
            ],
            'relationship': [
                "My ex keeps trying to control how I parent. How do I set boundaries?",
                "I started dating again but I feel guilty about taking time away from my kids.",
                "My sister said something really hurtful about my parenting. I don't know how to respond.",
                "I feel so lonely as a single parent. All my friends are couples.",
            ],
            'grief': [
                "My mother passed away last month and I haven't really processed it yet.",
                "I lost my best friend to cancer. Some days the grief hits me out of nowhere.",
                "My kids keep asking about their grandmother who died. I don't know what to tell them.",
            ],
            'health': [
                "I haven't been taking care of myself. I eat whatever's fast and never exercise.",
                "My doctor said my stress levels are affecting my physical health. I don't know where to start.",
                "I've been having trouble sleeping for weeks. I'm exhausted but my mind won't stop.",
            ],
        },
        follow_up_styles=[
            "That really resonates with me. Can you tell me more?",
            "I never thought about it that way. But I'm scared to try.",
            "Does it get easier? I feel like I've been stuck forever.",
            "Thank you for understanding. Most people just tell me to 'stay positive'.",
            "What if I can't do this? What if I'm not strong enough?",
        ],
        emotional_range=(0.2, 0.6),
        messages_per_convo=(5, 10),
        delay_between_msgs=(3.0, 6.0),
    ),
    
    UserPersona(
        name="SimUser_Jordan",
        password="SimTest123!",
        email="sim_jordan@test.com",
        communication_style="brief",
        personality_summary="College student, 20. Struggles with direction and meaning. Skeptical but curious. Uses short messages.",
        situation_topics={
            'existential': [
                "what's the point of college if AI is going to take all the jobs anyway",
                "i don't know what i want to do with my life and everyone expects me to have it figured out",
                "sometimes i wonder if anything really matters",
                "my parents want me to be a doctor but i hate science. how do i tell them?",
            ],
            'skill_development': [
                "how do i actually study effectively? i just stare at my textbook",
                "i want to start a youtube channel but i'm afraid nobody will watch",
                "i procrastinate everything until the last minute. how do i fix this?",
            ],
            'creative': [
                "i write poetry but i'm too scared to show anyone. is it even good enough?",
                "i have this business idea but everyone says i should finish school first",
                "how do you find your creative voice? everything i make feels like a copy of someone else",
            ],
            'relationship': [
                "my best friend and i are drifting apart since we went to different colleges",
                "i think my roommate is depressed but i don't know how to help",
                "i got rejected and it hurts way more than i thought it would",
            ],
        },
        follow_up_styles=[
            "yeah but how tho",
            "idk that sounds hard",
            "ok but what if that doesn't work",
            "hmm never thought of it like that",
            "that's actually helpful, thanks",
            "what do you mean by that exactly",
        ],
        emotional_range=(0.3, 0.65),
        messages_per_convo=(3, 6),
        delay_between_msgs=(1.5, 3.0),
    ),
    
    UserPersona(
        name="SimUser_Priya",
        password="SimTest123!",
        email="sim_priya@test.com",
        communication_style="verbose",
        personality_summary="45-year-old project manager. Going through mid-life reflection. Thoughtful, detailed communicator. Interested in philosophy and growth.",
        situation_topics={
            'existential': [
                "I've been successful by society's standards - good career, nice house, stable marriage. But I wake up feeling empty. Is this a mid-life crisis or something deeper?",
                "I read that Kierkegaard said anxiety is the dizziness of freedom. I think I finally understand what he meant. I have so many options but I'm paralyzed.",
                "Do you think it's possible to fundamentally change who you are at 45? Or is personality mostly fixed by now?",
            ],
            'career_guidance': [
                "I've been managing projects for 20 years. I'm good at it, but it feels mechanical now. I used to dream about being a teacher. Is it too late to switch careers at 45?",
                "My company wants me to take on a VP role. More money, more prestige, but also more politics. Part of me wants to downsize instead.",
            ],
            'health': [
                "I've been having chest pains that my doctor says are stress-related. I need to make lifestyle changes but my entire identity is built around being the person who handles everything.",
                "I started meditating but my mind won't quiet down. Am I doing it wrong?",
            ],
            'relationship': [
                "My teenage daughter thinks I don't understand her. She's probably right. I'm trying to connect but everything I say seems wrong.",
                "My husband and I have become roommates. We're not fighting, we're just... coexisting. How do we reconnect?",
            ],
            'creative': [
                "I used to paint in college. I haven't picked up a brush in 20 years. I'm afraid I've lost whatever talent I had.",
                "I want to write a book about my experiences with burnout in corporate life. Where do I even start?",
            ],
        },
        follow_up_styles=[
            "That's a really interesting perspective. I think what I'm really struggling with is the gap between knowing what I should do and actually doing it.",
            "I appreciate that framework. Could you help me think through the practical implications?",
            "You know, I think part of the issue is that I've been optimizing for the wrong things my whole life.",
            "That reminds me of something I read. The idea that we're all writing stories about ourselves. Maybe I need to write a new chapter.",
            "I want to dig deeper into that. What would that look like in practice for someone in my situation?",
        ],
        emotional_range=(0.4, 0.75),
        messages_per_convo=(4, 7),
        delay_between_msgs=(3.0, 6.0),
    ),
    
    UserPersona(
        name="SimUser_Marcus",
        password="SimTest123!",
        email="sim_marcus@test.com",
        communication_style="analytical",
        personality_summary="Recently retired military, 50. Adjusting to civilian life. Disciplined but emotionally guarded. Looking for purpose.",
        situation_topics={
            'career_guidance': [
                "After 25 years in the military, I retired. Nobody tells you how hard the transition is. I don't know who I am without the uniform.",
                "I'm looking at consulting jobs but they all feel meaningless compared to what I used to do.",
                "People keep telling me to 'enjoy retirement' but I'm 50 and I need purpose. What should I pursue?",
            ],
            'emotional': [
                "I was always told to push through emotions. Now my wife says I'm emotionally unavailable. I don't even know what that means.",
                "I saw something on the news that triggered some memories I'd rather forget. I don't want to talk about specifics but how do I manage this?",
                "My adult children say they don't really know me. I was deployed for most of their childhood. The guilt is crushing.",
            ],
            'relationship': [
                "My wife and I are basically strangers after 25 years of deployments. How do we build something real?",
                "I have trouble making civilian friends. Everything feels superficial compared to military bonds.",
            ],
            'health': [
                "My body is falling apart from years of service. Two bad knees, a bad back. How do I stay active without making things worse?",
                "Someone suggested therapy for stress but I've always handled things on my own. Is therapy actually useful?",
            ],
            'grief': [
                "I lost a close friend in service. I never properly grieved because there was always the next mission. Now it's catching up with me.",
            ],
        },
        follow_up_styles=[
            "Roger that. Give me the action plan.",
            "I understand the theory. What's step one?",
            "That's softer than what I'm used to, but I'll consider it.",
            "How do I measure progress on something like that?",
            "I need concrete steps. Abstract advice doesn't help me.",
        ],
        emotional_range=(0.35, 0.6),
        messages_per_convo=(3, 6),
        delay_between_msgs=(2.0, 4.0),
    ),
]


# ================================================================
# SIMULATED USER AGENT
# ================================================================

class SimulatedUserAgent:
    """An agent that simulates a real user interacting with the system"""
    
    def __init__(self, base_url: str, persona: UserPersona, verbose: bool = True):
        self.base_url = base_url.rstrip('/')
        self.persona = persona
        self.verbose = verbose
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.conversations = []
        self.total_messages_sent = 0
        self.total_responses_received = 0
        self.errors = []
        self.satisfaction_scores = []
        self.rate_limited = False
        self.messages_remaining = None
    
    def log(self, msg: str):
        if self.verbose:
            print(f"  [{self.persona.name}] {msg}")
    
    # --- Authentication ---
    
    def register(self) -> bool:
        """Register this persona as a new user"""
        try:
            r = self.session.post(f"{self.base_url}/api/auth/signup", json={
                'username': self.persona.name,
                'password': self.persona.password,
                'email': self.persona.email,
                'first_name': self.persona.name.replace('SimUser_', ''),
                'last_name': 'Simulated'
            })
            if r.status_code == 200 or r.status_code == 201:
                data = r.json()
                self.token = data.get('token')
                if self.token:
                    self.session.headers['Authorization'] = f'Bearer {self.token}'
                    self.user_id = data.get('user_id')
                    self.log(f"✅ Registered (user_id={self.user_id})")
                    return True
            # Maybe already registered
            return self.login()
        except Exception as e:
            self.errors.append(f"Register: {e}")
            return self.login()
    
    def login(self) -> bool:
        """Login with this persona's credentials"""
        try:
            r = self.session.post(f"{self.base_url}/api/auth/login", json={
                'username': self.persona.name,
                'password': self.persona.password,
            })
            if r.status_code == 200:
                data = r.json()
                self.token = data.get('token')
                if self.token:
                    self.session.headers['Authorization'] = f'Bearer {self.token}'
                    self.user_id = data.get('user_id')
                    self.log(f"✅ Logged in (user_id={self.user_id})")
                    return True
            self.log(f"❌ Login failed: {r.status_code} {r.text[:100]}")
            return False
        except Exception as e:
            self.errors.append(f"Login: {e}")
            self.log(f"❌ Login error: {e}")
            return False
    
    # --- Conversation Management ---
    
    def create_conversation(self, title: str) -> Optional[str]:
        """Create a new conversation and return session_id"""
        try:
            r = self.session.post(f"{self.base_url}/api/user/conversations", json={
                'title': title
            })
            if r.status_code == 200:
                data = r.json()
                session_id = data.get('session_id')
                self.conversations.append(session_id)
                self.log(f"📝 Created conversation: {title}")
                return session_id
            self.log(f"❌ Create conversation failed: {r.status_code}")
            return None
        except Exception as e:
            self.errors.append(f"Create convo: {e}")
            return None
    
    def send_message(self, session_id: str, content: str) -> Optional[Dict]:
        """Send a message and get AI response"""
        try:
            r = self.session.post(
                f"{self.base_url}/api/user/conversations/{session_id}/messages",
                json={'senderType': 'user', 'content': content},
                timeout=60  # AI responses can take time
            )
            if r.status_code == 200:
                data = r.json()
                self.total_messages_sent += 1
                if data.get('ai_response'):
                    self.total_responses_received += 1
                # Track remaining messages from usage info
                usage = data.get('usage', {})
                if usage.get('remaining') is not None:
                    self.messages_remaining = usage['remaining']
                return data
            elif r.status_code == 403:
                self.rate_limited = True
                self.log(f"⚠️ Rate limited: {r.json().get('error', 'unknown')}")
                return None
            else:
                self.log(f"❌ Send message failed: {r.status_code} {r.text[:100]}")
                return None
        except requests.Timeout:
            self.log(f"⏱️ Message timed out (60s)")
            self.errors.append("Message timeout")
            return None
        except Exception as e:
            self.errors.append(f"Send msg: {e}")
            return None
    
    def send_feedback(self, session_id: str, feedback_type: str = 'thumbs_up'):
        """Send feedback on the AI response"""
        try:
            self.session.post(f"{self.base_url}/api/user/personalization/signal", json={
                'signal_type': 'feedback',
                'signal_data': {
                    'session_id': session_id,
                    'type': feedback_type,
                    'value': 1.0 if feedback_type == 'thumbs_up' else 0.0
                }
            })
        except Exception:
            pass  # Non-critical
    
    # --- Conversation Simulation ---
    
    def pick_topic(self) -> Tuple[str, str]:
        """Pick a random situation type and opening message"""
        situation = random.choice(list(self.persona.situation_topics.keys()))
        messages = self.persona.situation_topics[situation]
        opening = random.choice(messages)
        return situation, opening
    
    def generate_follow_up(self, ai_response: str) -> str:
        """Generate a follow-up message based on the AI's response"""
        style = random.choice(self.persona.follow_up_styles)
        
        # Extract a keyword from the AI response to make it feel natural
        words = ai_response.split()
        # Find meaningful words (not stop words, > 5 chars)
        meaningful = [w.strip('.,!?;:') for w in words if len(w) > 5 and w.isalpha()]
        topic_word = random.choice(meaningful) if meaningful else "that"
        
        follow_up = style.replace('{topic}', topic_word)
        return follow_up
    
    def simulate_conversation(self) -> Dict:
        """Run a complete multi-turn conversation"""
        if self.rate_limited:
            self.log(f"⏭️ Skipping — rate limited for today")
            return {'success': False, 'error': 'rate_limited'}
        
        situation, opening = self.pick_topic()
        title = f"{situation.replace('_', ' ').title()} - {datetime.now().strftime('%m/%d %H:%M')}"
        
        session_id = self.create_conversation(title)
        if not session_id:
            return {'success': False, 'error': 'Failed to create conversation'}
        
        num_messages = random.randint(*self.persona.messages_per_convo)
        messages_log = []
        
        self.log(f"💬 Starting {situation} conversation ({num_messages} msgs)")
        
        # Send opening message
        result = self.send_message(session_id, opening)
        messages_log.append({'role': 'user', 'content': opening, 'situation': situation})
        
        if result and result.get('ai_response'):
            ai_text = result['ai_response']
            messages_log.append({'role': 'assistant', 'content': ai_text[:100] + '...'})
            self.log(f"  → AI: {ai_text[:80]}...")
            
            # Simulate reading time
            delay = random.uniform(*self.persona.delay_between_msgs)
            time.sleep(delay)
        else:
            self.log(f"  ⚠️ No AI response to opening")
            return {'success': False, 'session_id': session_id, 'messages': 1}
        
        # Follow-up messages
        for i in range(num_messages - 1):
            ai_text = result.get('ai_response', '') if result else ''
            
            if ai_text and random.random() < 0.7:
                # 70%: Follow up on what the AI said
                follow_up = self.generate_follow_up(ai_text)
            else:
                # 30%: Bring up a related topic
                related_msgs = self.persona.situation_topics.get(situation, [])
                if related_msgs:
                    follow_up = random.choice(related_msgs)
                else:
                    follow_up = self.generate_follow_up(ai_text or "that")
            
            result = self.send_message(session_id, follow_up)
            messages_log.append({'role': 'user', 'content': follow_up})
            
            if result and result.get('ai_response'):
                ai_text = result['ai_response']
                messages_log.append({'role': 'assistant', 'content': ai_text[:100] + '...'})
                self.log(f"  → AI: {ai_text[:80]}...")
                
                # Random feedback (30% chance)
                if random.random() < 0.3:
                    positivity = random.uniform(*self.persona.emotional_range)
                    fb = 'thumbs_up' if positivity > 0.5 else 'thumbs_down'
                    self.send_feedback(session_id, fb)
                    self.satisfaction_scores.append(positivity)
            
            delay = random.uniform(*self.persona.delay_between_msgs)
            time.sleep(delay)
            
            # Check rate limit
            if result is None:
                self.log(f"  ⚠️ Stopping conversation (rate limited or error)")
                break
        
        return {
            'success': True,
            'session_id': session_id,
            'situation': situation,
            'messages': len([m for m in messages_log if m['role'] == 'user']),
            'ai_responses': len([m for m in messages_log if m['role'] == 'assistant']),
        }
    
    def get_stats(self) -> Dict:
        """Get agent statistics"""
        return {
            'persona': self.persona.name,
            'messages_sent': self.total_messages_sent,
            'responses_received': self.total_responses_received,
            'conversations': len(self.conversations),
            'errors': len(self.errors),
            'rate_limited': self.rate_limited,
            'messages_remaining': self.messages_remaining,
            'avg_satisfaction': round(
                sum(self.satisfaction_scores) / max(1, len(self.satisfaction_scores)), 3
            ) if self.satisfaction_scores else None,
        }


# ================================================================
# AGENT RUNNER
# ================================================================

class AgentRunner:
    """Orchestrates multiple simulated user agents"""
    
    def __init__(self, base_url: str, personas: List[UserPersona] = None,
                 verbose: bool = True):
        self.base_url = base_url
        self.personas = personas or PERSONAS
        self.agents: List[SimulatedUserAgent] = []
        self.verbose = verbose
        self.start_time = None
        self.end_time = None
    
    def warm_up_server(self, max_attempts: int = 5, timeout: int = 60) -> bool:
        """Warm up the server by hitting the homepage until it responds"""
        print(f"🔥 Warming up server at {self.base_url}...")
        for attempt in range(1, max_attempts + 1):
            try:
                r = requests.get(self.base_url, timeout=timeout)
                if r.status_code == 200:
                    print(f"  ✅ Server ready (attempt {attempt})")
                    return True
                print(f"  ⚠️ Attempt {attempt}: status {r.status_code}")
            except requests.Timeout:
                print(f"  ⏱️ Attempt {attempt}: timeout ({timeout}s)")
            except requests.ConnectionError:
                print(f"  🔄 Attempt {attempt}: connection refused")
            except Exception as e:
                print(f"  ❌ Attempt {attempt}: {e}")
            
            if attempt < max_attempts:
                wait = min(30, 10 * attempt)
                print(f"  Waiting {wait}s before retry...")
                time.sleep(wait)
        
        print(f"  ❌ Server not responding after {max_attempts} attempts")
        return False
    
    def initialize_agents(self) -> int:
        """Register/login all agents, return count of successful agents"""
        print(f"\n🤖 Initializing {len(self.personas)} simulated user agents...")
        
        for persona in self.personas:
            agent = SimulatedUserAgent(self.base_url, persona, self.verbose)
            if agent.register():
                self.agents.append(agent)
            else:
                print(f"  ❌ Failed to initialize {persona.name}")
        
        print(f"  ✅ {len(self.agents)}/{len(self.personas)} agents ready\n")
        return len(self.agents)
    
    def run_round(self) -> List[Dict]:
        """Run one round: each agent has one conversation"""
        results = []
        for agent in self.agents:
            try:
                result = agent.simulate_conversation()
                results.append(result)
                
                # Small delay between agents to avoid hammering the server
                time.sleep(random.uniform(1.0, 3.0))
            except Exception as e:
                print(f"  ❌ {agent.persona.name} error: {e}")
                results.append({'success': False, 'error': str(e)})
        
        return results
    
    def run_continuous(self, duration_minutes: int = 10, 
                       conversations_per_agent: int = None,
                       delay_between_rounds: float = 30.0):
        """
        Run agents continuously for a specified duration.
        
        Args:
            duration_minutes: How long to run (0 = use conversations_per_agent instead)
            conversations_per_agent: Fixed number of conversations per agent
            delay_between_rounds: Seconds to wait between rounds
        """
        self.start_time = datetime.now()
        end_time = self.start_time + timedelta(minutes=duration_minutes) if duration_minutes > 0 else None
        
        round_num = 0
        total_convos = 0
        total_messages = 0
        
        print(f"{'='*60}")
        print(f"SIMULATED USER AGENTS - CONTINUOUS RUN")
        print(f"{'='*60}")
        print(f"  Target: {self.base_url}")
        print(f"  Agents: {len(self.agents)}")
        if end_time:
            print(f"  Duration: {duration_minutes} minutes")
        else:
            print(f"  Conversations per agent: {conversations_per_agent}")
        print(f"  Started: {self.start_time.strftime('%H:%M:%S')}")
        print()
        
        try:
            while True:
                # Check termination conditions
                if end_time and datetime.now() >= end_time:
                    print(f"\n⏱️ Duration reached ({duration_minutes} min)")
                    break
                
                if conversations_per_agent and round_num >= conversations_per_agent:
                    print(f"\n✅ Completed {conversations_per_agent} rounds")
                    break
                
                round_num += 1
                print(f"\n--- Round {round_num} ---")
                
                results = self.run_round()
                
                round_convos = sum(1 for r in results if r.get('success'))
                round_msgs = sum(r.get('messages', 0) for r in results)
                total_convos += round_convos
                total_messages += round_msgs
                
                print(f"  Round {round_num}: {round_convos} conversations, {round_msgs} messages")
                
                # Wait between rounds
                if (end_time and datetime.now() < end_time) or (conversations_per_agent and round_num < conversations_per_agent):
                    wait = min(delay_between_rounds, 
                              (end_time - datetime.now()).total_seconds() if end_time else delay_between_rounds)
                    if wait > 0:
                        print(f"  ⏳ Waiting {wait:.0f}s before next round...")
                        time.sleep(wait)
        
        except KeyboardInterrupt:
            print(f"\n\n⚠️ Interrupted by user")
        
        self.end_time = datetime.now()
        self._print_summary(round_num, total_convos, total_messages)
    
    def run_single_round(self):
        """Quick mode: each agent runs exactly one conversation"""
        self.start_time = datetime.now()
        
        print(f"\n{'='*60}")
        print(f"SIMULATED USER AGENTS - SINGLE ROUND")
        print(f"{'='*60}")
        print(f"  Target: {self.base_url}")
        print(f"  Agents: {len(self.agents)}\n")
        
        results = self.run_round()
        
        self.end_time = datetime.now()
        total_convos = sum(1 for r in results if r.get('success'))
        total_msgs = sum(r.get('messages', 0) for r in results)
        
        self._print_summary(1, total_convos, total_msgs)
        return results
    
    def _print_summary(self, rounds: int, total_convos: int, total_msgs: int):
        """Print run summary"""
        elapsed = (self.end_time - self.start_time).total_seconds()
        
        print(f"\n{'='*60}")
        print(f"RUN SUMMARY")
        print(f"{'='*60}")
        print(f"  Duration: {elapsed:.0f}s")
        print(f"  Rounds: {rounds}")
        print(f"  Total conversations: {total_convos}")
        print(f"  Total user messages: {total_msgs}")
        print(f"  Total AI responses: {sum(a.total_responses_received for a in self.agents)}")
        
        print(f"\n  Per-Agent Stats:")
        for agent in self.agents:
            stats = agent.get_stats()
            sat = f", sat={stats['avg_satisfaction']}" if stats['avg_satisfaction'] else ""
            errs = f", errors={stats['errors']}" if stats['errors'] > 0 else ""
            rl = " [RATE LIMITED]" if stats.get('rate_limited') else ""
            print(f"    {stats['persona']:20s}: {stats['messages_sent']} msgs, "
                  f"{stats['conversations']} convos{sat}{errs}{rl}")
        
        total_errors = sum(len(a.errors) for a in self.agents)
        if total_errors:
            print(f"\n  ⚠️ Total errors: {total_errors}")
            for agent in self.agents:
                for err in agent.errors[:3]:  # Show first 3 errors per agent
                    print(f"    [{agent.persona.name}] {err}")


# ================================================================
# CLI
# ================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Run simulated user agents')
    parser.add_argument('--url', default='http://localhost:5000',
                        help='Base URL of the server')
    parser.add_argument('--production', action='store_true',
                        help='Use production URL (trabcd.pythonanywhere.com)')
    parser.add_argument('--rounds', type=int, default=1,
                        help='Number of conversation rounds per agent')
    parser.add_argument('--duration', type=int, default=0,
                        help='Run for N minutes (overrides --rounds)')
    parser.add_argument('--delay', type=float, default=30.0,
                        help='Delay between rounds in seconds')
    parser.add_argument('--agents', type=int, default=0,
                        help='Number of agents to use (0 = all)')
    parser.add_argument('--quiet', action='store_true',
                        help='Suppress per-message output')
    
    args = parser.parse_args()
    
    url = 'https://trabcd.pythonanywhere.com' if args.production else args.url
    
    personas = PERSONAS
    if args.agents > 0:
        personas = personas[:args.agents]
    
    runner = AgentRunner(url, personas, verbose=not args.quiet)
    
    # Warm up the server before starting
    if not runner.warm_up_server():
        print("❌ Server not responding. Exiting.")
        sys.exit(1)
    
    ready = runner.initialize_agents()
    if ready == 0:
        print("❌ No agents initialized. Exiting.")
        sys.exit(1)
    
    if args.duration > 0:
        runner.run_continuous(duration_minutes=args.duration, delay_between_rounds=args.delay)
    elif args.rounds == 1:
        runner.run_single_round()
    else:
        runner.run_continuous(duration_minutes=0, conversations_per_agent=args.rounds,
                            delay_between_rounds=args.delay)


if __name__ == '__main__':
    main()

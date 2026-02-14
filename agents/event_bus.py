"""
Lightweight Event Bus for Agent Communication

Decouples system components by allowing publish/subscribe messaging.
This enables agents and modules to communicate without direct dependencies.

Events flow through the bus and subscribers react autonomously:
  - conversation.completed → EffectivenessLearner, HealthAgent
  - character.gap_detected → CharacterExpansion
  - user.inactive → GreetingSystem, EngagementAgent
  - health.critical → Orchestrator, Admin alerts
  - agent.rate_limited → Orchestrator (switch to next agent)

Usage:
    bus = EventBus()
    bus.subscribe('conversation.completed', my_handler)
    bus.publish('conversation.completed', {'session_id': '...', 'satisfaction': 0.8})
"""

import threading
import time
import json
import os
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any, Optional


@dataclass
class Event:
    """An event that flows through the bus"""
    topic: str
    data: Dict[str, Any]
    source: str = 'unknown'
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    event_id: str = field(default_factory=lambda: f"evt_{int(time.time()*1000)}")


@dataclass
class Subscriber:
    """A registered event handler"""
    name: str
    callback: Callable[[Event], None]
    filter_fn: Optional[Callable[[Event], bool]] = None


class EventBus:
    """Central event bus for agent/module communication"""
    
    def __init__(self, persist_events: bool = False, log_path: str = None):
        self._subscribers: Dict[str, List[Subscriber]] = defaultdict(list)
        self._lock = threading.Lock()
        self._event_history: List[Event] = []
        self._max_history = 1000
        self.persist_events = persist_events
        self.log_path = log_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'event_log.jsonl'
        )
        self.stats = {
            'events_published': 0,
            'events_delivered': 0,
            'errors': 0,
        }
    
    def subscribe(self, topic: str, callback: Callable[[Event], None], 
                  name: str = None, filter_fn: Callable[[Event], bool] = None):
        """Subscribe to events on a topic.
        
        Args:
            topic: Event topic (supports wildcards: 'conversation.*')
            callback: Function to call when event is published
            name: Subscriber name for debugging
            filter_fn: Optional filter to only receive matching events
        """
        sub = Subscriber(
            name=name or f"sub_{len(self._subscribers[topic])}",
            callback=callback,
            filter_fn=filter_fn
        )
        with self._lock:
            self._subscribers[topic].append(sub)
    
    def unsubscribe(self, topic: str, name: str):
        """Remove a subscriber by name"""
        with self._lock:
            self._subscribers[topic] = [
                s for s in self._subscribers[topic] if s.name != name
            ]
    
    def publish(self, topic: str, data: Dict[str, Any] = None, source: str = 'unknown'):
        """Publish an event to all subscribers.
        
        Args:
            topic: Event topic (e.g. 'conversation.completed')
            data: Event payload
            source: Who published the event
        """
        event = Event(topic=topic, data=data or {}, source=source)
        
        self.stats['events_published'] += 1
        
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        # Persist if enabled
        if self.persist_events:
            self._persist_event(event)
        
        # Find matching subscribers (exact match + wildcard)
        matched_subs = []
        with self._lock:
            # Exact topic match
            matched_subs.extend(self._subscribers.get(topic, []))
            
            # Wildcard match (e.g. 'conversation.*' matches 'conversation.completed')
            parts = topic.split('.')
            for i in range(len(parts)):
                wildcard = '.'.join(parts[:i+1]) + '.*'
                matched_subs.extend(self._subscribers.get(wildcard, []))
            
            # Global wildcard
            matched_subs.extend(self._subscribers.get('*', []))
        
        # Deliver to subscribers
        for sub in matched_subs:
            try:
                # Apply filter if set
                if sub.filter_fn and not sub.filter_fn(event):
                    continue
                
                sub.callback(event)
                self.stats['events_delivered'] += 1
            except Exception as e:
                self.stats['errors'] += 1
                print(f"⚠️ EventBus: Error delivering {topic} to {sub.name}: {e}")
    
    def publish_async(self, topic: str, data: Dict[str, Any] = None, source: str = 'unknown'):
        """Publish an event asynchronously (non-blocking)"""
        thread = threading.Thread(target=self.publish, args=(topic, data, source), daemon=True)
        thread.start()
    
    def get_history(self, topic: str = None, limit: int = 50) -> List[Dict]:
        """Get recent event history, optionally filtered by topic"""
        events = self._event_history
        if topic:
            events = [e for e in events if e.topic == topic or e.topic.startswith(topic.rstrip('*'))]
        
        return [
            {
                'event_id': e.event_id,
                'topic': e.topic,
                'source': e.source,
                'data': e.data,
                'timestamp': e.timestamp,
            }
            for e in events[-limit:]
        ]
    
    def get_stats(self) -> Dict:
        """Get bus statistics"""
        subscriber_count = sum(len(subs) for subs in self._subscribers.values())
        return {
            **self.stats,
            'subscribers': subscriber_count,
            'topics': list(self._subscribers.keys()),
            'history_size': len(self._event_history),
        }
    
    def _persist_event(self, event: Event):
        """Append event to JSONL log file"""
        try:
            with open(self.log_path, 'a') as f:
                f.write(json.dumps({
                    'event_id': event.event_id,
                    'topic': event.topic,
                    'source': event.source,
                    'data': event.data,
                    'timestamp': event.timestamp,
                }) + '\n')
        except Exception:
            pass


# ================================================================
# STANDARD EVENT TOPICS
# ================================================================

class Topics:
    """Standard event topic constants"""
    
    # Conversation lifecycle
    CONVERSATION_STARTED = 'conversation.started'
    CONVERSATION_COMPLETED = 'conversation.completed'
    CONVERSATION_RATED = 'conversation.rated'
    MESSAGE_SENT = 'message.sent'
    
    # Character system
    CHARACTER_GAP_DETECTED = 'character.gap_detected'
    CHARACTER_CREATED = 'character.created'
    CHARACTER_EFFECTIVENESS_UPDATE = 'character.effectiveness_update'
    
    # User events
    USER_REGISTERED = 'user.registered'
    USER_INACTIVE = 'user.inactive'
    USER_RETURNING = 'user.returning'
    USER_MILESTONE = 'user.milestone'
    
    # System health
    HEALTH_CHECK_COMPLETED = 'health.check_completed'
    HEALTH_CRITICAL = 'health.critical'
    HEALTH_WARNING = 'health.warning'
    
    # Agent events
    AGENT_RATE_LIMITED = 'agent.rate_limited'
    AGENT_CYCLE_COMPLETED = 'agent.cycle_completed'
    AGENT_ERROR = 'agent.error'
    
    # Expansion system
    EXPANSION_TRIGGERED = 'expansion.triggered'
    EXPANSION_COMPLETED = 'expansion.completed'


# ================================================================
# DEMO / TEST
# ================================================================

def demo():
    """Demonstrate the event bus"""
    bus = EventBus(persist_events=False)
    
    # Sample subscribers
    events_received = []
    
    def on_conversation_complete(event: Event):
        sat = event.data.get('satisfaction', 0)
        print(f"  📊 Effectiveness Learner: recorded satisfaction={sat:.2f}")
        events_received.append(event)
    
    def on_gap_detected(event: Event):
        gap = event.data.get('situation_type', '?')
        print(f"  🔧 Character Expansion: detected gap in '{gap}'")
        events_received.append(event)
    
    def on_health_critical(event: Event):
        msg = event.data.get('message', '?')
        print(f"  🚨 Alert: {msg}")
        events_received.append(event)
    
    def on_any_event(event: Event):
        events_received.append(event)
    
    # Subscribe
    bus.subscribe(Topics.CONVERSATION_COMPLETED, on_conversation_complete, 'effectiveness_learner')
    bus.subscribe(Topics.CHARACTER_GAP_DETECTED, on_gap_detected, 'expansion_system')
    bus.subscribe(Topics.HEALTH_CRITICAL, on_health_critical, 'alert_system')
    bus.subscribe('*', on_any_event, 'audit_log')
    
    print("Event Bus Demo")
    print("=" * 40)
    
    # Simulate events
    print("\n1. Publishing conversation.completed:")
    bus.publish(Topics.CONVERSATION_COMPLETED, {
        'session_id': 'abc123',
        'user_id': 9,
        'character_id': 'therapist',
        'satisfaction': 0.82,
        'situation_type': 'emotional',
    }, source='chat_endpoint')
    
    print("\n2. Publishing character.gap_detected:")
    bus.publish(Topics.CHARACTER_GAP_DETECTED, {
        'situation_type': 'grief',
        'gap_score': 0.43,
        'best_existing_character': 'therapist',
        'best_distance': 1.8,
    }, source='expansion_system')
    
    print("\n3. Publishing health.critical:")
    bus.publish(Topics.HEALTH_CRITICAL, {
        'message': 'API response time > 30s',
        'check': 'api_response',
        'value': 35.2,
    }, source='health_agent')
    
    print(f"\n{'='*40}")
    print(f"Stats: {bus.get_stats()}")
    print(f"Total events received by audit_log: {len(events_received)}")
    
    return bus


# ================================================================
# Global singleton for cross-module access
# ================================================================
_global_bus: Optional[EventBus] = None


def set_global_bus(bus: EventBus):
    """Set the global event bus instance (called from app.py at startup)"""
    global _global_bus
    _global_bus = bus


def get_global_bus() -> Optional[EventBus]:
    """Get the global event bus instance (safe to call from any module)"""
    return _global_bus


if __name__ == '__main__':
    demo()

"""
Habit Tracker & Daily Check-in System
======================================
Provides structured habit tracking and daily check-ins that integrate
naturally into conversations:

  - Habit creation, tracking, streaks, and completion rates
  - Daily check-ins (mood, energy, top priority, gratitude)
  - Gentle nudges when habits are missed
  - Weekly/monthly summaries
  - Integration with AI prompt for proactive coaching

All data persisted in SQLite. No AI calls required.
"""

import json
import sqlite3
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import Counter


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Habit:
    id: int = 0
    user_id: int = 0
    name: str = ''
    description: str = ''
    frequency: str = 'daily'            # daily, weekday, weekly, custom
    category: str = 'general'           # health, productivity, mindfulness, social, learning, creativity
    target_count: int = 1               # times per period
    current_streak: int = 0
    best_streak: int = 0
    total_completions: int = 0
    created_at: str = ''
    last_completed: Optional[str] = None
    is_active: bool = True

@dataclass
class HabitCompletion:
    habit_id: int
    completed_at: str
    notes: str = ''
    mood_after: Optional[str] = None    # how they felt after completing

@dataclass
class DailyCheckIn:
    user_id: int
    date: str                           # YYYY-MM-DD
    mood: str = 'neutral'               # great, good, okay, low, bad
    energy: str = 'medium'              # high, medium, low
    top_priority: str = ''
    gratitude: str = ''
    reflection: str = ''
    mood_score: int = 3                 # 1-5
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class HabitSummary:
    user_id: int
    active_habits: List[Habit] = field(default_factory=list)
    due_today: List[Habit] = field(default_factory=list)
    completed_today: List[int] = field(default_factory=list)  # habit IDs
    current_streaks: Dict[str, int] = field(default_factory=dict)  # name → streak
    weekly_completion_rate: float = 0.0
    recent_checkins: List[DailyCheckIn] = field(default_factory=list)
    mood_trend: str = 'stable'          # improving, stable, declining


class HabitTracker:
    """
    Manages habits and daily check-ins for a user.

    Usage::

        tracker = HabitTracker(db_conn)
        tracker.create_habit(user_id=42, name="Morning meditation", category="mindfulness")
        tracker.complete_habit(user_id=42, habit_id=1)
        tracker.daily_checkin(user_id=42, mood="good", energy="high",
                              top_priority="Finish project", gratitude="Sunny day")
        summary = tracker.get_summary(user_id=42)
        prompt_block = tracker.build_prompt_block(summary)
    """

    def __init__(self, db_connection=None):
        self.db = db_connection
        self._ensure_tables()

    def _ensure_tables(self):
        if not self.db:
            return
        try:
            cur = self.db.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS habits (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id         INTEGER NOT NULL,
                    name            TEXT NOT NULL,
                    description     TEXT DEFAULT '',
                    frequency       TEXT DEFAULT 'daily',
                    category        TEXT DEFAULT 'general',
                    target_count    INTEGER DEFAULT 1,
                    current_streak  INTEGER DEFAULT 0,
                    best_streak     INTEGER DEFAULT 0,
                    total_completions INTEGER DEFAULT 0,
                    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_completed  DATETIME,
                    is_active       BOOLEAN DEFAULT 1,
                    UNIQUE(user_id, name)
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS habit_completions (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_id        INTEGER NOT NULL,
                    user_id         INTEGER NOT NULL,
                    completed_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
                    notes           TEXT DEFAULT '',
                    mood_after      TEXT,
                    FOREIGN KEY (habit_id) REFERENCES habits(id)
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS daily_checkins (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id         INTEGER NOT NULL,
                    check_date      DATE NOT NULL,
                    mood            TEXT DEFAULT 'neutral',
                    energy          TEXT DEFAULT 'medium',
                    mood_score      INTEGER DEFAULT 3,
                    top_priority    TEXT DEFAULT '',
                    gratitude       TEXT DEFAULT '',
                    reflection      TEXT DEFAULT '',
                    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, check_date)
                )
            ''')
            self.db.commit()
        except Exception as e:
            print(f"[HabitTracker] table init error: {e}")

    # ==================================================================
    # HABIT MANAGEMENT
    # ==================================================================

    def create_habit(self, user_id: int, name: str, description: str = '',
                     frequency: str = 'daily', category: str = 'general',
                     target_count: int = 1) -> Optional[Habit]:
        if not self.db:
            return None
        try:
            cur = self.db.cursor()
            cur.execute('''
                INSERT INTO habits (user_id, name, description, frequency, category, target_count)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, name.strip(), description, frequency, category, target_count))
            self.db.commit()
            return Habit(
                id=cur.lastrowid, user_id=user_id, name=name,
                description=description, frequency=frequency,
                category=category, target_count=target_count,
                created_at=datetime.now().isoformat(),
            )
        except sqlite3.IntegrityError:
            return None  # duplicate
        except Exception as e:
            print(f"[HabitTracker] create error: {e}")
            return None

    def complete_habit(self, user_id: int, habit_id: int,
                       notes: str = '', mood_after: str = None) -> bool:
        if not self.db:
            return False
        try:
            cur = self.db.cursor()
            now = datetime.now()
            today = now.date().isoformat()

            # Check if already completed today
            cur.execute('''
                SELECT COUNT(*) FROM habit_completions
                WHERE habit_id = ? AND user_id = ? AND DATE(completed_at) = ?
            ''', (habit_id, user_id, today))
            if cur.fetchone()[0] > 0:
                return True  # already done

            # Record completion
            cur.execute('''
                INSERT INTO habit_completions (habit_id, user_id, notes, mood_after)
                VALUES (?, ?, ?, ?)
            ''', (habit_id, user_id, notes, mood_after))

            # Update habit stats
            cur.execute('SELECT last_completed, current_streak, best_streak FROM habits WHERE id = ?', (habit_id,))
            row = cur.fetchone()
            if row:
                last = row[0]
                streak = row[1] or 0
                best = row[2] or 0

                # Check if streak continues (completed yesterday or today)
                if last:
                    try:
                        last_date = datetime.fromisoformat(last).date()
                        if (now.date() - last_date).days <= 1:
                            streak += 1
                        else:
                            streak = 1  # streak broken, start new
                    except (ValueError, TypeError):
                        streak = 1
                else:
                    streak = 1

                best = max(best, streak)

                cur.execute('''
                    UPDATE habits SET
                        total_completions = total_completions + 1,
                        current_streak = ?,
                        best_streak = ?,
                        last_completed = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (streak, best, habit_id))

            self.db.commit()
            return True
        except Exception as e:
            print(f"[HabitTracker] complete error: {e}")
            return False

    def get_habits(self, user_id: int, active_only: bool = True) -> List[Habit]:
        if not self.db:
            return []
        try:
            cur = self.db.cursor()
            query = 'SELECT * FROM habits WHERE user_id = ?'
            if active_only:
                query += ' AND is_active = 1'
            query += ' ORDER BY created_at'
            cur.execute(query, (user_id,))
            cols = [desc[0] for desc in cur.description]
            return [Habit(**dict(zip(cols, row))) for row in cur.fetchall()]
        except Exception:
            return []

    def deactivate_habit(self, user_id: int, habit_id: int) -> bool:
        if not self.db:
            return False
        try:
            cur = self.db.cursor()
            cur.execute('UPDATE habits SET is_active = 0 WHERE id = ? AND user_id = ?',
                        (habit_id, user_id))
            self.db.commit()
            return cur.rowcount > 0
        except Exception:
            return False

    # ==================================================================
    # DAILY CHECK-INS
    # ==================================================================

    def daily_checkin(self, user_id: int, mood: str = 'okay',
                      energy: str = 'medium', top_priority: str = '',
                      gratitude: str = '', reflection: str = '') -> Optional[DailyCheckIn]:
        if not self.db:
            return None

        mood_scores = {'great': 5, 'good': 4, 'okay': 3, 'low': 2, 'bad': 1}
        score = mood_scores.get(mood, 3)
        today = date.today().isoformat()

        try:
            cur = self.db.cursor()
            cur.execute('''
                INSERT INTO daily_checkins
                (user_id, check_date, mood, energy, mood_score, top_priority, gratitude, reflection)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, check_date) DO UPDATE SET
                    mood = excluded.mood, energy = excluded.energy,
                    mood_score = excluded.mood_score,
                    top_priority = excluded.top_priority,
                    gratitude = excluded.gratitude,
                    reflection = excluded.reflection
            ''', (user_id, today, mood, energy, score, top_priority, gratitude, reflection))
            self.db.commit()

            return DailyCheckIn(
                user_id=user_id, date=today, mood=mood, energy=energy,
                top_priority=top_priority, gratitude=gratitude,
                reflection=reflection, mood_score=score,
            )
        except Exception as e:
            print(f"[HabitTracker] checkin error: {e}")
            return None

    def get_today_checkin(self, user_id: int) -> Optional[DailyCheckIn]:
        if not self.db:
            return None
        try:
            cur = self.db.cursor()
            cur.execute('''
                SELECT user_id, check_date, mood, energy, mood_score,
                       top_priority, gratitude, reflection, created_at
                FROM daily_checkins
                WHERE user_id = ? AND check_date = DATE('now')
            ''', (user_id,))
            row = cur.fetchone()
            if row:
                return DailyCheckIn(
                    user_id=row[0], date=row[1], mood=row[2], energy=row[3],
                    mood_score=row[4], top_priority=row[5], gratitude=row[6],
                    reflection=row[7], created_at=row[8],
                )
        except Exception:
            pass
        return None

    def get_recent_checkins(self, user_id: int, days: int = 7) -> List[DailyCheckIn]:
        if not self.db:
            return []
        try:
            cur = self.db.cursor()
            cur.execute('''
                SELECT user_id, check_date, mood, energy, mood_score,
                       top_priority, gratitude, reflection, created_at
                FROM daily_checkins
                WHERE user_id = ? AND check_date > DATE('now', ?)
                ORDER BY check_date DESC
            ''', (user_id, f'-{days} days'))
            results = []
            for row in cur.fetchall():
                results.append(DailyCheckIn(
                    user_id=row[0], date=row[1], mood=row[2], energy=row[3],
                    mood_score=row[4], top_priority=row[5], gratitude=row[6],
                    reflection=row[7], created_at=row[8],
                ))
            return results
        except Exception:
            return []

    # ==================================================================
    # SUMMARY & INSIGHTS
    # ==================================================================

    def get_summary(self, user_id: int) -> HabitSummary:
        summary = HabitSummary(user_id=user_id)

        habits = self.get_habits(user_id)
        summary.active_habits = habits

        today = date.today()
        today_str = today.isoformat()

        # Due today (based on frequency)
        weekday = today.weekday()  # 0=Mon, 6=Sun
        for h in habits:
            if h.frequency == 'daily':
                summary.due_today.append(h)
            elif h.frequency == 'weekday' and weekday < 5:
                summary.due_today.append(h)
            elif h.frequency == 'weekly':
                # Consider due if not completed this week
                if not h.last_completed or (
                    today - datetime.fromisoformat(h.last_completed).date()
                ).days >= 7:
                    summary.due_today.append(h)

        # Completed today
        if self.db:
            try:
                cur = self.db.cursor()
                cur.execute('''
                    SELECT DISTINCT habit_id FROM habit_completions
                    WHERE user_id = ? AND DATE(completed_at) = ?
                ''', (user_id, today_str))
                summary.completed_today = [row[0] for row in cur.fetchall()]
            except Exception:
                pass

        # Streaks
        for h in habits:
            if h.current_streak > 0:
                summary.current_streaks[h.name] = h.current_streak

        # Weekly completion rate
        summary.weekly_completion_rate = self._weekly_rate(user_id, habits)

        # Recent check-ins
        summary.recent_checkins = self.get_recent_checkins(user_id, days=7)

        # Mood trend
        summary.mood_trend = self._mood_trend(summary.recent_checkins)

        return summary

    def _weekly_rate(self, user_id: int, habits: List[Habit]) -> float:
        if not self.db or not habits:
            return 0.0
        try:
            cur = self.db.cursor()
            cur.execute('''
                SELECT COUNT(DISTINCT habit_id || DATE(completed_at))
                FROM habit_completions
                WHERE user_id = ? AND completed_at > datetime('now', '-7 days')
            ''', (user_id,))
            completions = cur.fetchone()[0] or 0
            # Expected = daily habits × 7 + weekday habits × 5 + weekly × 1
            expected = 0
            for h in habits:
                if h.frequency == 'daily':
                    expected += 7
                elif h.frequency == 'weekday':
                    expected += 5
                elif h.frequency == 'weekly':
                    expected += 1
            return round(completions / max(expected, 1), 2)
        except Exception:
            return 0.0

    @staticmethod
    def _mood_trend(checkins: List[DailyCheckIn]) -> str:
        if len(checkins) < 3:
            return 'stable'
        scores = [c.mood_score for c in checkins]
        recent_avg = sum(scores[:3]) / 3
        older_avg = sum(scores[3:]) / max(len(scores[3:]), 1)
        diff = recent_avg - older_avg
        if diff > 0.5:
            return 'improving'
        if diff < -0.5:
            return 'declining'
        return 'stable'

    # ==================================================================
    # NUDGE GENERATION
    # ==================================================================

    def get_nudges(self, user_id: int) -> List[str]:
        summary = self.get_summary(user_id)
        nudges = []

        # Incomplete habits
        incomplete = [h for h in summary.due_today
                      if h.id not in summary.completed_today]
        if incomplete:
            names = ', '.join(h.name for h in incomplete[:3])
            nudges.append(f"You still have habits to complete today: {names}")

        # Streak celebration
        for name, streak in summary.current_streaks.items():
            if streak in (7, 14, 21, 30, 50, 100):
                nudges.append(f"🎉 Amazing! {streak}-day streak on '{name}'!")
            elif streak >= 3:
                nudges.append(f"You're on a {streak}-day streak with '{name}' — keep it going!")

        # No check-in today
        if not self.get_today_checkin(user_id):
            nudges.append("You haven't done your daily check-in yet. How are you feeling today?")

        # Mood trend
        if summary.mood_trend == 'declining':
            nudges.append("Your mood has been trending down this week. Would you like to talk about what's going on?")
        elif summary.mood_trend == 'improving':
            nudges.append("Your mood has been improving — that's great progress! What's been going well?")

        return nudges

    # ==================================================================
    # PROMPT BLOCK
    # ==================================================================

    def build_prompt_block(self, summary: HabitSummary) -> str:
        if not summary.active_habits and not summary.recent_checkins:
            return ''

        lines = ["[HABIT & CHECK-IN CONTEXT]"]

        # Today's status
        due = len(summary.due_today)
        done = len(summary.completed_today)
        if due > 0:
            lines.append(f"Habits today: {done}/{due} completed "
                         f"(weekly rate: {summary.weekly_completion_rate:.0%})")

        # Streaks
        if summary.current_streaks:
            top = sorted(summary.current_streaks.items(), key=lambda x: -x[1])[:3]
            streaks_str = ', '.join(f"{n} ({s}d)" for n, s in top)
            lines.append(f"Active streaks: {streaks_str}")

        # Today's check-in
        if summary.recent_checkins:
            latest = summary.recent_checkins[0]
            lines.append(f"Today's mood: {latest.mood} | Energy: {latest.energy}")
            if latest.top_priority:
                lines.append(f"Today's priority: {latest.top_priority}")
            if latest.gratitude:
                lines.append(f"Grateful for: {latest.gratitude}")

        # Mood trend
        if summary.mood_trend != 'stable':
            lines.append(f"Mood trend (7d): {summary.mood_trend}")

        return '\n'.join(lines)

    # ==================================================================
    # CONVERSATION DETECTION (extract habits from natural language)
    # ==================================================================

    def detect_habit_intent(self, message: str) -> Optional[Dict[str, str]]:
        """Detect if user is expressing a habit intention in conversation."""
        msg_lower = message.lower()

        habit_signals = [
            (r"i want to (?:start|begin) (.+?)(?:\.|$|,)", 'create'),
            (r"i(?:'m| am) going to (.+?) (?:every|daily|each)", 'create'),
            (r"i (?:did|completed|finished) (?:my |the )?(.+?)(?:\.|$|!)", 'complete'),
            (r"i (?:worked out|meditated|exercised|ran|walked|read|studied|journaled)", 'complete'),
            (r"how (?:am i|are my) (?:habits|streaks|progress)", 'status'),
            (r"(?:show|check|what are) my habits", 'status'),
        ]

        import re
        for pattern, intent in habit_signals:
            match = re.search(pattern, msg_lower)
            if match:
                return {
                    'intent': intent,
                    'subject': match.group(1).strip() if match.lastindex else '',
                    'raw': message,
                }
        return None


    # ==================================================================
    # GOAL-HABIT LINKING (Enhancement 7)
    # ==================================================================

    def link_habit_to_goal(self, user_id: int, habit_id: int, goal: str) -> bool:
        if not self.db:
            return False
        try:
            cur = self.db.cursor()
            try:
                cur.execute('ALTER TABLE habits ADD COLUMN linked_goal TEXT DEFAULT ""')
                self.db.commit()
            except Exception:
                pass  # column already exists
            cur.execute('UPDATE habits SET linked_goal = ? WHERE id = ? AND user_id = ?',
                        (goal.strip(), habit_id, user_id))
            self.db.commit()
            return cur.rowcount > 0
        except Exception:
            return False

    def get_goal_progress(self, user_id: int) -> List[Dict]:
        """Get habits grouped by linked goal with completion stats."""
        if not self.db:
            return []
        try:
            cur = self.db.cursor()
            cur.execute('''
                SELECT linked_goal, name, current_streak, total_completions, best_streak
                FROM habits WHERE user_id = ? AND is_active = 1 AND linked_goal != ''
                ORDER BY linked_goal, name
            ''', (user_id,))
            from collections import defaultdict
            goals = defaultdict(list)
            for row in cur.fetchall():
                goals[row[0]].append({
                    'habit': row[1], 'streak': row[2],
                    'total': row[3], 'best_streak': row[4],
                })
            return [{'goal': g, 'habits': h, 'avg_streak': sum(x['streak'] for x in h) / len(h)}
                    for g, h in goals.items()]
        except Exception:
            return []

    # ==================================================================
    # WEEKLY SUMMARY (Enhancement 6)
    # ==================================================================

    def generate_weekly_summary(self, user_id: int) -> Dict:
        """Generate a comprehensive weekly summary for the user."""
        summary = {
            'period': 'last_7_days',
            'habits': {},
            'checkins': {},
            'highlights': [],
        }

        # Habit stats
        habits = self.get_habits(user_id)
        if habits:
            rate = self._weekly_rate(user_id, habits)
            streaks = {h.name: h.current_streak for h in habits if h.current_streak > 0}
            best_streak_habit = max(streaks.items(), key=lambda x: x[1]) if streaks else None
            summary['habits'] = {
                'total_active': len(habits),
                'weekly_completion_rate': rate,
                'active_streaks': streaks,
                'best_streak': {'name': best_streak_habit[0], 'days': best_streak_habit[1]} if best_streak_habit else None,
            }
            if rate >= 0.8:
                summary['highlights'].append(f"Excellent habit consistency ({rate:.0%} completion rate)!")
            elif rate < 0.3 and len(habits) > 0:
                summary['highlights'].append("Habit completion was low this week — consider simplifying your routine.")

        # Check-in stats
        checkins = self.get_recent_checkins(user_id, days=7)
        if checkins:
            scores = [c.mood_score for c in checkins]
            avg_mood = sum(scores) / len(scores)
            trend = self._mood_trend(checkins)
            summary['checkins'] = {
                'days_checked_in': len(checkins),
                'avg_mood_score': round(avg_mood, 1),
                'mood_trend': trend,
                'best_day': max(checkins, key=lambda c: c.mood_score).date if checkins else None,
            }
            if trend == 'improving':
                summary['highlights'].append("Your mood has been trending upward — great progress!")
            elif trend == 'declining':
                summary['highlights'].append("Your mood dipped this week. Be gentle with yourself.")

        # Goal progress
        goal_progress = self.get_goal_progress(user_id)
        if goal_progress:
            summary['goal_progress'] = goal_progress

        return summary


# ---------------------------------------------------------------------------
# Module-level factory
# ---------------------------------------------------------------------------
_instance = None

def get_habit_tracker(db_connection=None) -> HabitTracker:
    global _instance
    if _instance is None or db_connection is not None:
        _instance = HabitTracker(db_connection)
    return _instance

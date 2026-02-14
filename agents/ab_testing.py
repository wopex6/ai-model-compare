"""
A/B Testing Agent
=================
Runs controlled experiments on character configurations using simulated users.
Compares prompt variations, response lengths, collaboration modes, and trait
adjustments to empirically determine what works best.

Experiment flow:
  1. Define variants (A = control, B = experimental change)
  2. Run sim users through both variants
  3. Collect quality scores for each variant
  4. Statistical comparison → declare winner or inconclusive
  5. Optionally auto-apply winning variant

Experiment types:
  - prompt_variation: Test different system prompt wordings
  - trait_adjustment: Test different trait vector values
  - response_length: Test short vs medium vs long
  - collaboration_mode: Test visible vs silent collaboration
  - threshold_tuning: Test different activation thresholds

Usage:
    python agents/ab_testing.py --list              # List all experiments
    python agents/ab_testing.py --run <exp_id>      # Run an experiment
    python agents/ab_testing.py --results <exp_id>  # View results
    python agents/ab_testing.py --create             # Interactive experiment creation
"""

import os
import sys
import json
import sqlite3
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ExperimentStatus(Enum):
    DRAFT = 'draft'
    RUNNING = 'running'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class VariantResult(Enum):
    WINNER = 'winner'
    LOSER = 'loser'
    INCONCLUSIVE = 'inconclusive'


@dataclass
class Variant:
    """A single variant in an A/B test."""
    name: str                       # e.g. 'A_control', 'B_empathy_boost'
    description: str
    config_overrides: Dict[str, Any]  # What to change for this variant
    conversations: List[str] = field(default_factory=list)  # session_ids
    quality_scores: List[float] = field(default_factory=list)
    
    @property
    def avg_score(self) -> float:
        return sum(self.quality_scores) / len(self.quality_scores) if self.quality_scores else 0
    
    @property
    def sample_size(self) -> int:
        return len(self.quality_scores)


@dataclass
class Experiment:
    """An A/B test experiment."""
    experiment_id: str
    name: str
    description: str
    experiment_type: str            # prompt_variation, trait_adjustment, etc.
    character_id: str               # Which character to test
    variants: List[Variant]
    status: ExperimentStatus = ExperimentStatus.DRAFT
    min_samples_per_variant: int = 5
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    winner: Optional[str] = None
    significance: float = 0.0       # How significant the difference is
    
    def to_dict(self) -> Dict:
        return {
            'experiment_id': self.experiment_id,
            'name': self.name,
            'description': self.description,
            'experiment_type': self.experiment_type,
            'character_id': self.character_id,
            'status': self.status.value,
            'variants': [
                {
                    'name': v.name,
                    'description': v.description,
                    'config_overrides': v.config_overrides,
                    'sample_size': v.sample_size,
                    'avg_score': round(v.avg_score, 3),
                }
                for v in self.variants
            ],
            'min_samples': self.min_samples_per_variant,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
            'winner': self.winner,
            'significance': round(self.significance, 3),
        }


class ABTestingAgent:
    """Manages and runs A/B testing experiments."""
    
    # Minimum score difference to declare a winner
    MIN_EFFECT_SIZE = 0.05
    
    def __init__(self, db_path: str = None, event_bus=None):
        self.db_path = db_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'smart_response.db'
        )
        self.event_bus = event_bus
        self.experiments: Dict[str, Experiment] = {}
        
        self._ensure_tables()
        self._load_experiments()
    
    def _ensure_tables(self):
        """Create experiment tracking tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ab_experiments (
                    experiment_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    experiment_type TEXT NOT NULL,
                    character_id TEXT NOT NULL,
                    variants_json TEXT NOT NULL,
                    status TEXT DEFAULT 'draft',
                    min_samples INTEGER DEFAULT 5,
                    created_at TEXT DEFAULT (datetime('now')),
                    completed_at TEXT,
                    winner TEXT,
                    significance REAL DEFAULT 0
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ab_experiment_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT NOT NULL,
                    variant_name TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    quality_score REAL,
                    details_json TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (experiment_id) REFERENCES ab_experiments(experiment_id)
                )
            """)
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"  ⚠️ AB table creation error: {e}")
    
    def _load_experiments(self):
        """Load experiments from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM ab_experiments ORDER BY created_at DESC")
            for row in cursor.fetchall():
                variants_data = json.loads(row[5])
                variants = [
                    Variant(
                        name=v['name'],
                        description=v.get('description', ''),
                        config_overrides=v.get('config_overrides', {}),
                    )
                    for v in variants_data
                ]
                
                exp = Experiment(
                    experiment_id=row[0],
                    name=row[1],
                    description=row[2] or '',
                    experiment_type=row[3],
                    character_id=row[4],
                    variants=variants,
                    status=ExperimentStatus(row[6]),
                    min_samples_per_variant=row[7],
                    created_at=row[8],
                    completed_at=row[9],
                    winner=row[10],
                    significance=row[11] or 0,
                )
                
                # Load session scores
                cursor.execute("""
                    SELECT variant_name, quality_score FROM ab_experiment_sessions
                    WHERE experiment_id = ? AND quality_score IS NOT NULL
                """, (row[0],))
                
                for srow in cursor.fetchall():
                    for v in exp.variants:
                        if v.name == srow[0]:
                            v.quality_scores.append(srow[1])
                
                self.experiments[exp.experiment_id] = exp
            
            conn.close()
        except Exception as e:
            print(f"  ⚠️ AB load error: {e}")
    
    # ================================================================
    # EXPERIMENT CREATION
    # ================================================================
    
    def create_experiment(self, name: str, description: str, experiment_type: str,
                          character_id: str, variants: List[Dict],
                          min_samples: int = 5) -> Experiment:
        """Create a new A/B experiment."""
        exp_id = f"exp_{int(time.time())}_{random.randint(100,999)}"
        
        variant_objects = [
            Variant(
                name=v['name'],
                description=v.get('description', ''),
                config_overrides=v.get('config_overrides', {}),
            )
            for v in variants
        ]
        
        exp = Experiment(
            experiment_id=exp_id,
            name=name,
            description=description,
            experiment_type=experiment_type,
            character_id=character_id,
            variants=variant_objects,
            min_samples_per_variant=min_samples,
        )
        
        # Save to DB
        self._save_experiment(exp)
        self.experiments[exp_id] = exp
        
        print(f"  ✅ Created experiment: {exp_id} — {name}")
        return exp
    
    def _save_experiment(self, exp: Experiment):
        """Save experiment to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            cursor = conn.cursor()
            
            variants_json = json.dumps([
                {
                    'name': v.name,
                    'description': v.description,
                    'config_overrides': v.config_overrides,
                }
                for v in exp.variants
            ])
            
            cursor.execute("""
                INSERT OR REPLACE INTO ab_experiments
                (experiment_id, name, description, experiment_type, character_id,
                 variants_json, status, min_samples, created_at, completed_at, winner, significance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                exp.experiment_id, exp.name, exp.description, exp.experiment_type,
                exp.character_id, variants_json, exp.status.value, exp.min_samples_per_variant,
                exp.created_at, exp.completed_at, exp.winner, exp.significance,
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"  ❌ Save experiment error: {e}")
    
    # ================================================================
    # EXPERIMENT EXECUTION
    # ================================================================
    
    def get_variant_for_session(self, experiment_id: str) -> Optional[Variant]:
        """Get the next variant to use for a new conversation session.
        
        Uses round-robin assignment to ensure balanced sampling.
        """
        exp = self.experiments.get(experiment_id)
        if not exp or exp.status != ExperimentStatus.RUNNING:
            return None
        
        # Find variant with fewest samples
        min_samples = min(v.sample_size for v in exp.variants)
        candidates = [v for v in exp.variants if v.sample_size == min_samples]
        return random.choice(candidates)
    
    def record_session(self, experiment_id: str, variant_name: str,
                       session_id: str, quality_score: float = None,
                       details: Dict = None):
        """Record a conversation session result for an experiment."""
        exp = self.experiments.get(experiment_id)
        if not exp:
            return
        
        # Record in DB
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ab_experiment_sessions
                (experiment_id, variant_name, session_id, quality_score, details_json)
                VALUES (?, ?, ?, ?, ?)
            """, (experiment_id, variant_name, session_id, quality_score,
                  json.dumps(details) if details else None))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"  ⚠️ Record session error: {e}")
        
        # Update in-memory
        for v in exp.variants:
            if v.name == variant_name:
                v.conversations.append(session_id)
                if quality_score is not None:
                    v.quality_scores.append(quality_score)
                break
        
        # Check if experiment is complete
        all_sufficient = all(
            v.sample_size >= exp.min_samples_per_variant
            for v in exp.variants
        )
        if all_sufficient and exp.status == ExperimentStatus.RUNNING:
            self._evaluate_experiment(exp)
    
    def start_experiment(self, experiment_id: str) -> bool:
        """Start running an experiment."""
        exp = self.experiments.get(experiment_id)
        if not exp:
            print(f"  ❌ Experiment {experiment_id} not found")
            return False
        
        exp.status = ExperimentStatus.RUNNING
        self._save_experiment(exp)
        print(f"  ▶️ Started experiment: {exp.name}")
        return True
    
    def _evaluate_experiment(self, exp: Experiment):
        """Evaluate experiment results and declare winner."""
        if len(exp.variants) < 2:
            return
        
        # Sort by average score
        sorted_variants = sorted(exp.variants, key=lambda v: v.avg_score, reverse=True)
        best = sorted_variants[0]
        second = sorted_variants[1]
        
        diff = best.avg_score - second.avg_score
        
        # Simple significance test (effect size)
        # For proper stats, we'd use a t-test, but this works for small samples
        pooled_n = best.sample_size + second.sample_size
        significance = min(1.0, diff * (pooled_n ** 0.5) / 0.5) if diff > 0 else 0
        
        exp.significance = significance
        
        if diff >= self.MIN_EFFECT_SIZE and significance >= 0.6:
            exp.winner = best.name
            print(f"  🏆 Winner: {best.name} (avg={best.avg_score:.3f} vs {second.avg_score:.3f})")
        else:
            exp.winner = None
            print(f"  🤷 Inconclusive: {best.name}={best.avg_score:.3f} vs {second.name}={second.avg_score:.3f}")
        
        exp.status = ExperimentStatus.COMPLETED
        exp.completed_at = datetime.now().isoformat()
        self._save_experiment(exp)
        
        # Publish result
        if self.event_bus:
            self.event_bus.publish_async('experiment.completed', {
                'experiment_id': exp.experiment_id,
                'name': exp.name,
                'winner': exp.winner,
                'significance': exp.significance,
            }, source='ab_testing_agent')
    
    # ================================================================
    # PREDEFINED EXPERIMENTS
    # ================================================================
    
    def create_standard_experiments(self) -> List[Experiment]:
        """Create a set of standard experiments to run."""
        experiments = []
        
        # 1. Empathy boost test
        exp1 = self.create_experiment(
            name="Empathy Boost",
            description="Test whether increasing empathy trait improves quality scores",
            experiment_type="trait_adjustment",
            character_id="coordinator",
            variants=[
                {
                    'name': 'A_control',
                    'description': 'Current empathy level',
                    'config_overrides': {},
                },
                {
                    'name': 'B_high_empathy',
                    'description': 'Empathy +0.1',
                    'config_overrides': {'trait_adjustments': {'empathy': 0.1}},
                },
            ],
        )
        experiments.append(exp1)
        
        # 2. Response length test
        exp2 = self.create_experiment(
            name="Response Length",
            description="Test concise vs detailed responses",
            experiment_type="response_length",
            character_id="coordinator",
            variants=[
                {
                    'name': 'A_medium',
                    'description': 'Current medium-length responses',
                    'config_overrides': {},
                },
                {
                    'name': 'B_concise',
                    'description': 'Shorter, more focused responses',
                    'config_overrides': {
                        'prompt_addon': 'Keep responses concise and focused — 2-3 short paragraphs max.',
                        'trait_adjustments': {'verbosity': -0.15},
                    },
                },
            ],
        )
        experiments.append(exp2)
        
        # 3. Prompt variation test
        exp3 = self.create_experiment(
            name="Actionable Advice",
            description="Test whether adding 'always give one actionable step' improves helpfulness",
            experiment_type="prompt_variation",
            character_id="coordinator",
            variants=[
                {
                    'name': 'A_control',
                    'description': 'Current prompt',
                    'config_overrides': {},
                },
                {
                    'name': 'B_actionable',
                    'description': 'With actionable advice instruction',
                    'config_overrides': {
                        'prompt_addon': 'Always end your response with one specific, actionable next step '
                                        'the user can take right now.',
                    },
                },
            ],
        )
        experiments.append(exp3)
        
        # 4. Question-asking test
        exp4 = self.create_experiment(
            name="Clarifying Questions",
            description="Test whether asking more clarifying questions improves engagement",
            experiment_type="prompt_variation",
            character_id="coordinator",
            variants=[
                {
                    'name': 'A_control',
                    'description': 'Current approach',
                    'config_overrides': {},
                },
                {
                    'name': 'B_questions',
                    'description': 'Ask clarifying questions',
                    'config_overrides': {
                        'prompt_addon': 'After addressing the user\'s concern, ask one thoughtful '
                                        'follow-up question to deepen the conversation.',
                    },
                },
            ],
        )
        experiments.append(exp4)
        
        # ---- Philosophy Character Experiments ----
        
        # 5. Stoic vs Motivational approach comparison
        exp5 = self.create_experiment(
            name="Stoic vs Motivational",
            description="Compare stoic_philosopher and super_motivational_coach on same topics",
            experiment_type="character_comparison",
            character_id="stoic_philosopher",
            variants=[
                {
                    'name': 'A_stoic',
                    'description': 'Stoic philosopher approach',
                    'config_overrides': {'character_id': 'stoic_philosopher'},
                },
                {
                    'name': 'B_motivational',
                    'description': 'Motivational coach approach',
                    'config_overrides': {'character_id': 'super_motivational_coach'},
                },
            ],
        )
        experiments.append(exp5)
        
        # 6. Philosophy character depth test
        exp6 = self.create_experiment(
            name="Wisdom Depth",
            description="Test whether deeper philosophical responses improve satisfaction for wisdom_sage",
            experiment_type="trait_adjustment",
            character_id="wisdom_sage",
            variants=[
                {
                    'name': 'A_control',
                    'description': 'Current depth level',
                    'config_overrides': {},
                },
                {
                    'name': 'B_deeper',
                    'description': 'Increased depth and reduced verbosity',
                    'config_overrides': {
                        'trait_adjustments': {'depth': 0.15, 'verbosity': -0.1},
                        'prompt_addon': 'Share one profound insight rather than many surface-level ones.',
                    },
                },
            ],
        )
        experiments.append(exp6)
        
        # 7. Domain character: Work Advisor directness test
        exp7 = self.create_experiment(
            name="Work Advisor Directness",
            description="Test whether more direct advice improves helpfulness for domain_work",
            experiment_type="trait_adjustment",
            character_id="domain_work",
            variants=[
                {
                    'name': 'A_control',
                    'description': 'Current directness level',
                    'config_overrides': {},
                },
                {
                    'name': 'B_more_direct',
                    'description': 'Higher directness + action orientation',
                    'config_overrides': {
                        'trait_adjustments': {'directness': 0.1, 'action_oriented': 0.1},
                    },
                },
            ],
        )
        experiments.append(exp7)
        
        return experiments
    
    # ================================================================
    # REPORTING
    # ================================================================
    
    def print_experiments(self):
        """Print all experiments and their status."""
        print(f"\n{'='*60}")
        print(f"A/B EXPERIMENTS")
        print(f"{'='*60}")
        
        if not self.experiments:
            print("  No experiments found. Run --create to set up standard tests.")
            return
        
        for exp in self.experiments.values():
            status_icon = {
                ExperimentStatus.DRAFT: '📝',
                ExperimentStatus.RUNNING: '▶️',
                ExperimentStatus.COMPLETED: '✅',
                ExperimentStatus.CANCELLED: '❌',
            }.get(exp.status, '❓')
            
            print(f"\n  {status_icon} {exp.experiment_id}")
            print(f"     Name: {exp.name}")
            print(f"     Type: {exp.experiment_type} | Character: {exp.character_id}")
            print(f"     Status: {exp.status.value}")
            
            for v in exp.variants:
                score_str = f"avg={v.avg_score:.3f}" if v.quality_scores else "no data"
                winner_tag = " 🏆" if exp.winner == v.name else ""
                print(f"     • {v.name}: {v.sample_size} samples, {score_str}{winner_tag}")
            
            if exp.winner:
                print(f"     Winner: {exp.winner} (significance: {exp.significance:.2f})")
            elif exp.status == ExperimentStatus.COMPLETED:
                print(f"     Result: Inconclusive")
        
        print(f"\n{'='*60}")
    
    def get_results_summary(self) -> Dict:
        """Get experiment results as a dict (for API/dashboard)."""
        return {
            'total_experiments': len(self.experiments),
            'running': sum(1 for e in self.experiments.values() if e.status == ExperimentStatus.RUNNING),
            'completed': sum(1 for e in self.experiments.values() if e.status == ExperimentStatus.COMPLETED),
            'experiments': {
                eid: exp.to_dict() for eid, exp in self.experiments.items()
            }
        }


# ================================================================
# CLI
# ================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='A/B Testing Agent')
    parser.add_argument('--db', type=str, help='Path to smart_response.db')
    parser.add_argument('--list', action='store_true', help='List all experiments')
    parser.add_argument('--create', action='store_true', help='Create standard experiments')
    parser.add_argument('--run', type=str, help='Start experiment by ID')
    parser.add_argument('--results', type=str, help='View results for experiment')
    args = parser.parse_args()
    
    agent = ABTestingAgent(db_path=args.db)
    
    if args.create:
        print("🧪 Creating standard A/B experiments...")
        experiments = agent.create_standard_experiments()
        print(f"\n  Created {len(experiments)} experiments")
        agent.print_experiments()
    elif args.run:
        agent.start_experiment(args.run)
    elif args.list or args.results:
        agent.print_experiments()
    else:
        print("A/B Testing Agent")
        print("  --list     List experiments")
        print("  --create   Create standard experiments")
        print("  --run ID   Start an experiment")
        agent.print_experiments()

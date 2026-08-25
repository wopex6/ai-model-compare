"""
Agent Orchestrator

Central coordinator that runs all agents on a configurable schedule:
- Simulated User Agents: pump conversations at configurable intervals
- System Health Agent: periodic health checks with alerting
- Character Expansion: trigger gap analysis after enough new data
- Data Quality Agent: validate conversation quality and flag anomalies

Usage:
    python agents/orchestrator.py --production --plan default
    python agents/orchestrator.py --production --plan intensive --duration 60
    python agents/orchestrator.py --production --plan health-only
"""

import time
import json
import threading
import sys
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.simulated_users import AgentRunner, PERSONAS, UserPersona
from agents.system_health import SystemHealthAgent
from agents.quota_monitor import QuotaMonitor
from agents.quality_scorer import ConversationQualityScorer
from agents.admin_utils import upgrade_roles_via_api, SIM_USER_NAMES
from agents.self_improvement import SelfImprovementAgent
from agents.ab_testing import ABTestingAgent
from agents.wisdom_agent import WisdomAgent


@dataclass
class TaskResult:
    """Result of an orchestrated task"""
    task_name: str
    success: bool
    message: str
    data: Optional[Dict] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RunPlan:
    """Defines what the orchestrator should do"""
    name: str
    description: str
    # How many simulated user conversations per cycle
    sim_conversations_per_cycle: int = 1
    # How many agents to use
    sim_agent_count: int = 3
    # Run health check every N cycles
    health_check_interval: int = 1
    # Include chat test in health check (costs 1 AI call)
    health_include_chat: bool = False
    # Run quality scoring every N cycles (0 = disabled)
    quality_score_interval: int = 0
    # Run quota check every N cycles (0 = disabled)
    quota_check_interval: int = 1
    # Run self-improvement analysis every N cycles (0 = disabled)
    self_improve_interval: int = 0
    # Seconds between cycles
    cycle_delay: float = 60.0
    # Total duration in minutes (0 = run until stopped)
    max_duration_minutes: int = 30


# Pre-defined run plans
PLANS = {
    'default': RunPlan(
        name='default',
        description='Balanced: 3 agents, 1 convo each per cycle, health + quota every cycle, 60s delay',
        sim_conversations_per_cycle=1,
        sim_agent_count=3,
        health_check_interval=1,
        quota_check_interval=1,
        quality_score_interval=3,
        cycle_delay=60.0,
        max_duration_minutes=30,
    ),
    'intensive': RunPlan(
        name='intensive',
        description='Heavy testing: 5 agents, 1 convo each per cycle, health every 3 cycles, 30s delay',
        sim_conversations_per_cycle=1,
        sim_agent_count=5,
        health_check_interval=3,
        cycle_delay=30.0,
        max_duration_minutes=60,
    ),
    'light': RunPlan(
        name='light',
        description='Light: 2 agents, 1 convo per cycle, health every 5 cycles, 120s delay',
        sim_conversations_per_cycle=1,
        sim_agent_count=2,
        health_check_interval=5,
        cycle_delay=120.0,
        max_duration_minutes=30,
    ),
    'health-only': RunPlan(
        name='health-only',
        description='Health monitoring only, no simulated users',
        sim_conversations_per_cycle=0,
        sim_agent_count=0,
        health_check_interval=1,
        health_include_chat=True,
        cycle_delay=300.0,
        max_duration_minutes=60,
    ),
    'quick-test': RunPlan(
        name='quick-test',
        description='Quick: 2 agents, 1 convo each, health + quota + quality, then exit',
        sim_conversations_per_cycle=1,
        sim_agent_count=2,
        health_check_interval=1,
        quota_check_interval=1,
        quality_score_interval=1,
        cycle_delay=0,
        max_duration_minutes=0,  # Single cycle
    ),
}


class AgentOrchestrator:
    """Coordinates all agents in the system"""
    
    def __init__(self, base_url: str, db_path: str = None, verbose: bool = True):
        self.base_url = base_url.rstrip('/')
        self.db_path = db_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'integrated_users.db'
        )
        self.verbose = verbose
        
        # Agent instances
        self.sim_runner: Optional[AgentRunner] = None
        self.health_agent: Optional[SystemHealthAgent] = None
        self.quota_monitor: Optional[QuotaMonitor] = None
        self.quality_scorer: Optional[ConversationQualityScorer] = None
        self.self_improver: Optional[SelfImprovementAgent] = None
        self.ab_tester: Optional[ABTestingAgent] = None
        
        # Tracking
        self.results: List[TaskResult] = []
        self.cycle_count = 0
        self.start_time = None
        self.running = False
    
    def log(self, msg: str):
        if self.verbose:
            ts = datetime.now().strftime('%H:%M:%S')
            print(f"[{ts}] {msg}")
    
    def initialize(self, plan: RunPlan) -> bool:
        """Initialize all agents based on the plan"""
        self.log(f"🚀 Initializing Agent Orchestrator")
        self.log(f"   Plan: {plan.name} — {plan.description}")
        self.log(f"   Target: {self.base_url}")
        
        # 1. Initialize Health Agent (always)
        self.health_agent = SystemHealthAgent(self.base_url, db_path=self.db_path)
        # Try to auth with a simulated user
        self.health_agent.authenticate('SimUser_Alex', 'SimTest123!')
        self.log(f"   ✅ Health Agent ready")
        
        # 2. Initialize Quota Monitor
        self.quota_monitor = QuotaMonitor(db_path=self.db_path, base_url=self.base_url)
        self.log(f"   ✅ Quota Monitor ready")
        
        # 3. Initialize Quality Scorer
        self.quality_scorer = ConversationQualityScorer(self.db_path)
        self.log(f"   ✅ Quality Scorer ready")
        
        # 3b. Initialize Self-Improvement Agent
        sr_db = os.path.join(os.path.dirname(self.db_path), 'smart_response.db')
        self.self_improver = SelfImprovementAgent(db_path=sr_db)
        self.log(f"   ✅ Self-Improvement Agent ready")
        
        # 3c. Initialize A/B Testing Agent
        self.ab_tester = ABTestingAgent(db_path=sr_db)
        self.log(f"   ✅ A/B Testing Agent ready ({len(self.ab_tester.experiments)} experiments)")
        
        # 4. Initialize Simulated User Agents
        if plan.sim_agent_count > 0:
            personas = PERSONAS[:plan.sim_agent_count]
            self.sim_runner = AgentRunner(self.base_url, personas, verbose=self.verbose)
            
            if not self.sim_runner.warm_up_server():
                self.log("   ❌ Server not responding — cannot initialize")
                return False
            
            ready = self.sim_runner.initialize_agents()
            if ready == 0:
                self.log("   ❌ No simulated agents could register/login")
                return False
            self.log(f"   ✅ {ready} Simulated User Agents ready")
            
            # 5. Auto-upgrade sim users to 'paid' for unlimited messaging
            self._upgrade_sim_users_to_paid()
        else:
            self.log(f"   ⏭️  Simulated Users: disabled in this plan")
        
        return True
    
    def _upgrade_sim_users_to_paid(self):
        """Auto-upgrade simulated users from guest to paid for unlimited messaging.
        
        Uses the first authenticated sim user (who must be admin) or tries
        direct API call with each agent's session to upgrade others.
        """
        import requests
        
        self.log("   🔑 Checking sim user roles...")
        
        # Use any authenticated agent's session to check roles
        if not self.sim_runner or not self.sim_runner.agents:
            return
        
        # Find an agent with a valid session
        auth_agent = None
        for agent in self.sim_runner.agents:
            if agent.session and agent.user_id:
                auth_agent = agent
                break
        
        if not auth_agent:
            self.log("   ⚠️ No authenticated agent found for role check")
            return
        
        # Check current roles and upgrade if needed
        upgraded = 0
        already_paid = 0
        
        for agent in self.sim_runner.agents:
            if not agent.user_id:
                continue
            
            try:
                # Try to upgrade via admin endpoint
                r = auth_agent.session.post(
                    f"{self.base_url}/api/admin/users/{agent.user_id}/role",
                    json={'role': 'paid'},
                    timeout=15
                )
                
                if r.status_code == 200:
                    upgraded += 1
                    agent.rate_limited = False  # Reset rate limit flag
                    self.log(f"   ✅ {agent.persona.name} → paid (unlimited messaging)")
                elif r.status_code == 403:
                    # Not admin — check if already paid via message limit check
                    already_paid += 1
                else:
                    self.log(f"   ⚠️ {agent.persona.name}: role change returned {r.status_code}")
            except Exception as e:
                self.log(f"   ⚠️ {agent.persona.name}: role upgrade error: {e}")
        
        if upgraded > 0:
            self.log(f"   🔑 Upgraded {upgraded} agents to paid")
        elif already_paid > 0:
            self.log(f"   ℹ️ Could not upgrade roles (need admin access). "
                     f"Run: python agents/admin_utils.py upgrade --production --admin-user <USER> --admin-pass <PASS>")
    
    def run_health_check(self, include_chat: bool = False) -> TaskResult:
        """Run a system health check"""
        self.log("🏥 Running health check...")
        
        try:
            report = self.health_agent.run_full_check(include_chat_test=include_chat)
            self.health_agent.print_report(report)
            
            result = TaskResult(
                task_name='health_check',
                success=True,
                message=f"Health: {report.overall_status} ({len(report.checks)} checks)",
                data=report.to_dict()
            )
            self.results.append(result)
            return result
        except Exception as e:
            result = TaskResult('health_check', False, f'Error: {e}')
            self.results.append(result)
            return result
    
    def run_simulated_conversations(self) -> TaskResult:
        """Run one round of simulated user conversations"""
        if not self.sim_runner or not self.sim_runner.agents:
            return TaskResult('sim_conversations', False, 'No agents available')
        
        self.log(f"💬 Running simulated conversations ({len(self.sim_runner.agents)} agents)...")
        
        try:
            results = self.sim_runner.run_round()
            
            successes = sum(1 for r in results if r.get('success'))
            total_msgs = sum(r.get('messages', 0) for r in results)
            situations = [r.get('situation', '?') for r in results if r.get('success')]
            
            msg = f"{successes}/{len(results)} conversations, {total_msgs} messages, topics: {', '.join(situations)}"
            self.log(f"   ✅ {msg}")
            
            result = TaskResult(
                task_name='sim_conversations',
                success=successes > 0,
                message=msg,
                data={'results': results}
            )
            self.results.append(result)
            return result
        except Exception as e:
            result = TaskResult('sim_conversations', False, f'Error: {e}')
            self.results.append(result)
            return result
    
    def run_quota_check(self) -> TaskResult:
        """Run AI model quota check"""
        if not self.quota_monitor:
            return TaskResult('quota_check', False, 'No quota monitor')
        
        self.log("💰 Checking AI model quotas...")
        
        try:
            report = self.quota_monitor.run_check()
            self.quota_monitor.print_report(report)
            
            if report.has_critical_alerts():
                self.log("🚨 CRITICAL: AI model quota issue detected — please top up credits!")
            
            result = TaskResult(
                task_name='quota_check',
                success=True,
                message=f"{len(report.alerts)} alerts" if report.alerts else "All providers OK",
                data=report.to_dict()
            )
            self.results.append(result)
            return result
        except Exception as e:
            result = TaskResult('quota_check', False, f'Error: {e}')
            self.results.append(result)
            return result
    
    def run_quality_scoring(self, days: int = 7, limit: int = 20) -> TaskResult:
        """Score recent conversation quality"""
        if not self.quality_scorer:
            return TaskResult('quality_score', False, 'No quality scorer')
        
        self.log("📊 Scoring conversation quality...")
        
        try:
            report = self.quality_scorer.score_recent(days=days, limit=limit)
            self.quality_scorer.print_report(report)
            
            result = TaskResult(
                task_name='quality_score',
                success=True,
                message=f"Scored {len(report.scores)} convos, avg={report.avg_overall:.3f}, flagged={report.flagged_count}",
                data=report.to_dict()
            )
            self.results.append(result)
            return result
        except Exception as e:
            result = TaskResult('quality_score', False, f'Error: {e}')
            self.results.append(result)
            return result
    
    def run_self_improvement(self, dry_run: bool = True) -> TaskResult:
        """Run self-improvement analysis on character performance."""
        if not self.self_improver:
            return TaskResult('self_improvement', False, 'No self-improvement agent')
        
        self.log("🧠 Running self-improvement analysis...")
        
        try:
            report = self.self_improver.analyze(days=14)
            report = self.self_improver.apply_suggestions(report, dry_run=dry_run)
            self.self_improver.print_report(report)
            
            n_suggestions = len(report.suggestions)
            n_applied = len(report.applied)
            mode = "dry-run" if dry_run else "applied"
            
            result = TaskResult(
                task_name='self_improvement',
                success=True,
                message=f"{n_suggestions} suggestions, {n_applied} {mode}",
                data={'suggestions': n_suggestions, 'applied': n_applied, 'dry_run': dry_run}
            )
            self.results.append(result)
            return result
        except Exception as e:
            result = TaskResult('self_improvement', False, f'Error: {e}')
            self.results.append(result)
            return result
    
    def run_cycle(self, plan: RunPlan) -> Dict:
        """Run one complete orchestration cycle"""
        self.cycle_count += 1
        cycle_results = {}
        
        self.log(f"\n{'='*50}")
        self.log(f"CYCLE {self.cycle_count}")
        self.log(f"{'='*50}")
        
        # 1. Run simulated conversations
        if plan.sim_conversations_per_cycle > 0 and self.sim_runner:
            for i in range(plan.sim_conversations_per_cycle):
                result = self.run_simulated_conversations()
                cycle_results['sim_conversations'] = result.success
        
        # 2. Run health check (at interval)
        if plan.health_check_interval > 0 and self.cycle_count % plan.health_check_interval == 0:
            result = self.run_health_check(include_chat=plan.health_include_chat)
            cycle_results['health_check'] = result.success
        
        # 3. Run quota check (at interval)
        if plan.quota_check_interval > 0 and self.cycle_count % plan.quota_check_interval == 0:
            result = self.run_quota_check()
            cycle_results['quota_check'] = result.success
        
        # 4. Run quality scoring (at interval)
        if plan.quality_score_interval > 0 and self.cycle_count % plan.quality_score_interval == 0:
            result = self.run_quality_scoring()
            cycle_results['quality_score'] = result.success
        
        # 5. Run self-improvement analysis (at interval, dry-run by default)
        if getattr(plan, 'self_improve_interval', 0) > 0 and self.cycle_count % plan.self_improve_interval == 0:
            result = self.run_self_improvement(dry_run=True)
            cycle_results['self_improvement'] = result.success
        
        return cycle_results
    
    def run(self, plan: RunPlan):
        """Main run loop"""
        self.start_time = datetime.now()
        self.running = True
        
        end_time = (self.start_time + timedelta(minutes=plan.max_duration_minutes)
                   if plan.max_duration_minutes > 0 else None)
        
        print(f"\n{'='*60}")
        print(f"AGENT ORCHESTRATOR — {plan.name.upper()}")
        print(f"{'='*60}")
        print(f"  Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if end_time:
            print(f"  Ends: {end_time.strftime('%H:%M:%S')} ({plan.max_duration_minutes} min)")
        print()
        
        try:
            # Single cycle mode (quick-test)
            if plan.max_duration_minutes == 0 and plan.cycle_delay == 0:
                self.run_cycle(plan)
                self._print_final_summary()
                return
            
            # Continuous mode
            while self.running:
                if end_time and datetime.now() >= end_time:
                    self.log(f"⏱️ Duration limit reached")
                    break
                
                self.run_cycle(plan)
                
                if plan.cycle_delay > 0 and self.running:
                    remaining = ((end_time - datetime.now()).total_seconds() 
                                if end_time else plan.cycle_delay)
                    wait = min(plan.cycle_delay, remaining) if end_time else plan.cycle_delay
                    if wait > 0:
                        self.log(f"⏳ Next cycle in {wait:.0f}s...")
                        time.sleep(wait)
        
        except KeyboardInterrupt:
            self.log("⚠️ Interrupted by user")
        
        self.running = False
        self._print_final_summary()
    
    def _print_final_summary(self):
        """Print final orchestration summary"""
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        print(f"\n{'='*60}")
        print(f"ORCHESTRATION SUMMARY")
        print(f"{'='*60}")
        print(f"  Duration: {elapsed:.0f}s ({elapsed/60:.1f} min)")
        print(f"  Cycles: {self.cycle_count}")
        print(f"  Tasks run: {len(self.results)}")
        
        # Aggregate by task type
        task_types = {}
        for r in self.results:
            if r.task_name not in task_types:
                task_types[r.task_name] = {'success': 0, 'fail': 0}
            if r.success:
                task_types[r.task_name]['success'] += 1
            else:
                task_types[r.task_name]['fail'] += 1
        
        for task, counts in task_types.items():
            total = counts['success'] + counts['fail']
            print(f"  {task:25s}: {counts['success']}/{total} succeeded")
        
        # Simulated user stats
        if self.sim_runner:
            total_msgs = sum(a.total_messages_sent for a in self.sim_runner.agents)
            total_resps = sum(a.total_responses_received for a in self.sim_runner.agents)
            total_convos = sum(len(a.conversations) for a in self.sim_runner.agents)
            print(f"\n  Simulated Users Total:")
            print(f"    Messages sent: {total_msgs}")
            print(f"    AI responses: {total_resps}")
            print(f"    Conversations: {total_convos}")
        
        # Last health status
        health_results = [r for r in self.results if r.task_name == 'health_check' and r.data]
        if health_results:
            last = health_results[-1]
            summary = last.data.get('summary', {})
            print(f"\n  Last Health Check:")
            print(f"    Status: {last.data.get('overall_status', '?').upper()}")
            print(f"    Healthy: {summary.get('healthy', 0)}, Warnings: {summary.get('warning', 0)}, Critical: {summary.get('critical', 0)}")
            
            recs = last.data.get('recommendations', [])
            if recs:
                print(f"\n  📋 Recommendations:")
                for rec in recs:
                    print(f"    • {rec}")


# ================================================================
# CLI
# ================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Agent Orchestrator')
    parser.add_argument('--url', default='http://localhost:5000')
    parser.add_argument('--production', action='store_true')
    parser.add_argument('--plan', default='quick-test', choices=list(PLANS.keys()),
                        help='Run plan to use')
    parser.add_argument('--duration', type=int, default=None,
                        help='Override plan duration (minutes)')
    parser.add_argument('--db', default=None, help='Database path')
    parser.add_argument('--quiet', action='store_true')
    parser.add_argument('--list-plans', action='store_true', help='List available plans')
    
    args = parser.parse_args()
    
    if args.list_plans:
        print("Available plans:")
        for name, plan in PLANS.items():
            print(f"  {name:15s} — {plan.description}")
        return
    
    url = 'https://trabcd.pythonanywhere.com' if args.production else args.url
    plan = PLANS[args.plan]
    
    if args.duration is not None:
        plan.max_duration_minutes = args.duration
    
    orchestrator = AgentOrchestrator(url, db_path=args.db, verbose=not args.quiet)
    
    if not orchestrator.initialize(plan):
        print("❌ Initialization failed. Exiting.")
        sys.exit(1)
    
    orchestrator.run(plan)


if __name__ == '__main__':
    main()

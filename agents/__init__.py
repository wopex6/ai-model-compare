"""
AI Agent Team for autonomous project management.

Agents:
- SimulatedUserAgent: Acts like real users, pumps conversations through the system
- SystemHealthAgent: Monitors system health, detects anomalies, generates reports
- AgentOrchestrator: Coordinates all agents on a schedule
- ConversationQualityScorer: Grades conversations on coherence, helpfulness, consistency
- QuotaMonitor: Monitors AI provider quotas, alerts when credits run low
- EventBus: Lightweight pub/sub for decoupled agent communication
- AdminUtils: Manage simulated user roles and status
- AlertNotifier: Email/console alerts on critical Event Bus events with cooldown
- SelfImprovementAgent: Analyzes quality data to auto-tune character traits and prompts
- ABTestingAgent: Runs controlled A/B experiments on prompt/config variations
"""

"""
Admin logging system for model changes with cost tracking
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Setup admin logger
LOG_DIR = Path(__file__).parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

ADMIN_LOG_FILE = LOG_DIR / 'model_changes.log'

class AdminLogger:
    """Logs all model changes with timestamps and cost comparisons"""
    
    def __init__(self):
        self.logger = logging.getLogger('admin_model_changes')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # File handler
        file_handler = logging.FileHandler(ADMIN_LOG_FILE)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S %Z'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def log_model_discovery(self, provider: str, old_models: List[str], new_models: List[str], costs: Dict[str, dict]):
        """Log when new models are discovered"""
        self.logger.info("=" * 80)
        self.logger.info(f"MODEL DISCOVERY EVENT - Provider: {provider.upper()}")
        self.logger.info("=" * 80)
        
        # Find new models
        new_additions = [m for m in new_models if m not in old_models]
        removed = [m for m in old_models if m not in new_models]
        
        if new_additions:
            self.logger.info(f"NEW MODELS DISCOVERED: {len(new_additions)}")
            for model in new_additions:
                cost_info = costs.get(model, {})
                total_cost = cost_info.get('total', 'Unknown')
                self.logger.info(f"  + {model}")
                self.logger.info(f"    Cost: ${total_cost}/1M tokens (input+output)")
                
                # Compare with existing models
                if old_models:
                    avg_old_cost = self._get_average_cost(old_models, costs)
                    if avg_old_cost and isinstance(total_cost, (int, float)):
                        diff = ((total_cost - avg_old_cost) / avg_old_cost) * 100
                        if diff > 0:
                            self.logger.warning(f"    ⚠️  {diff:.1f}% MORE EXPENSIVE than average existing models")
                        elif diff < 0:
                            self.logger.info(f"    ✅ {abs(diff):.1f}% CHEAPER than average existing models")
                        else:
                            self.logger.info(f"    Similar cost to existing models")
        
        if removed:
            self.logger.info(f"MODELS REMOVED/DEPRECATED: {len(removed)}")
            for model in removed:
                self.logger.info(f"  - {model}")
        
        if not new_additions and not removed:
            self.logger.info("No changes - all models remain the same")
        
        self.logger.info("=" * 80)
        self.logger.info("")
    
    def log_config_update(self, provider: str, models: List[str]):
        """Log when config file is updated"""
        self.logger.info(f"CONFIG FILE UPDATED - Provider: {provider}")
        self.logger.info(f"  New model list: {models}")
        self.logger.info(f"  Total models: {len(models)}")
        self.logger.info("")
    
    def log_fallback_failure(self, provider: str, failed_models: List[str], reason: str):
        """Log when all fallback models fail"""
        self.logger.error("=" * 80)
        self.logger.error(f"ALL FALLBACK MODELS FAILED - Provider: {provider.upper()}")
        self.logger.error("=" * 80)
        self.logger.error(f"Reason: {reason}")
        self.logger.error(f"Failed models ({len(failed_models)}):")
        for model in failed_models:
            self.logger.error(f"  ❌ {model}")
        self.logger.error("Action: Triggering auto-discovery...")
        self.logger.error("=" * 80)
        self.logger.error("")
    
    def log_discovery_success(self, provider: str, model: str, attempt: int):
        """Log when a discovered model works"""
        self.logger.info("=" * 80)
        self.logger.info(f"✅ DISCOVERY SUCCESS - Provider: {provider.upper()}")
        self.logger.info("=" * 80)
        self.logger.info(f"Working model found: {model}")
        self.logger.info(f"Attempts before success: {attempt}")
        self.logger.info(f"Action: Adding to config and using immediately")
        self.logger.info("=" * 80)
        self.logger.info("")
    
    def log_system_startup(self):
        """Log when system starts"""
        self.logger.info("=" * 80)
        self.logger.info("AI MODEL DISCOVERY SYSTEM STARTED")
        self.logger.info("=" * 80)
        self.logger.info(f"Log file: {ADMIN_LOG_FILE}")
        self.logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("Monitoring: OpenAI, Anthropic, Google, Meta")
        self.logger.info("=" * 80)
        self.logger.info("")
    
    def _get_average_cost(self, models: List[str], costs: Dict[str, dict]) -> Optional[float]:
        """Calculate average cost of models"""
        total = 0
        count = 0
        for model in models:
            cost_info = costs.get(model, {})
            total_cost = cost_info.get('total')
            if isinstance(total_cost, (int, float)):
                total += total_cost
                count += 1
        
        return total / count if count > 0 else None
    
    @staticmethod
    def get_log_file_path() -> Path:
        """Get the path to the admin log file"""
        return ADMIN_LOG_FILE


# Singleton instance
_admin_logger = None

def get_admin_logger() -> AdminLogger:
    """Get the singleton admin logger instance"""
    global _admin_logger
    if _admin_logger is None:
        _admin_logger = AdminLogger()
    return _admin_logger

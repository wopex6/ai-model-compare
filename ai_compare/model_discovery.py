import asyncio
import aiohttp
from typing import List, Dict, Optional, Tuple
import json
import os
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import logging
import httpx

load_dotenv(override=True)

# Configure logging
LOG_DIR = Path(__file__).parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

# Admin log file
ADMIN_LOG_FILE = LOG_DIR / 'model_changes.log'

# Setup logger
logger = logging.getLogger('model_discovery')
logger.setLevel(logging.INFO)

# File handler for admin logs
file_handler = logging.FileHandler(ADMIN_LOG_FILE)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Console handler (optional)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

class ModelDiscovery:
    """Auto-discover models and update config with admin logging"""
    _instance = None
    _initialized = False
    
    # Model cost estimates (per 1M tokens)
    MODEL_COSTS = {
        'gpt-4o-mini': {'input': 0.15, 'output': 0.60, 'total': 0.75},
        'gpt-4o': {'input': 2.50, 'output': 10.00, 'total': 12.50},
        'gpt-4-turbo': {'input': 10.00, 'output': 30.00, 'total': 40.00},
        'gpt-4': {'input': 30.00, 'output': 60.00, 'total': 90.00},
        'gpt-3.5-turbo': {'input': 0.50, 'output': 1.50, 'total': 2.00},
        'claude-3-5-sonnet-20241022': {'input': 3.00, 'output': 15.00, 'total': 18.00},
        'claude-3-5-haiku-20241022': {'input': 1.00, 'output': 5.00, 'total': 6.00},
        'claude-3-haiku-20240307': {'input': 0.25, 'output': 1.25, 'total': 1.50},
        'claude-3-sonnet-20240229': {'input': 3.00, 'output': 15.00, 'total': 18.00},
        'claude-3-opus-20240229': {'input': 15.00, 'output': 75.00, 'total': 90.00},
        'gemini-2.5-flash': {'input': 0.075, 'output': 0.30, 'total': 0.375},
        'gemini-2.5-pro': {'input': 1.25, 'output': 5.00, 'total': 6.25},
        'gemini-2.0-flash': {'input': 0.10, 'output': 0.40, 'total': 0.50},
        'gemini-flash-latest': {'input': 0.075, 'output': 0.30, 'total': 0.375},
        'gemini-pro-latest': {'input': 1.25, 'output': 5.00, 'total': 6.25},
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelDiscovery, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not ModelDiscovery._initialized:
            self.cache = {}
            self.cache_duration = 3600  # 1 hour cache
            self._discovery_complete = {}
            self._lock = asyncio.Lock()
            self.config_file = Path(__file__).parent / 'model_config.py'
            ModelDiscovery._initialized = True
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid based on timestamp."""
        if cache_key not in self.cache:
            return False
        
        cached_entry = self.cache[cache_key]
        if not isinstance(cached_entry, dict) or 'timestamp' not in cached_entry:
            return False
        
        age = time.time() - cached_entry['timestamp']
        return age < self.cache_duration
    
    def _get_cached_data(self, cache_key: str):
        """Get cached data if valid, None otherwise."""
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        return None
    
    def _set_cache_data(self, cache_key: str, data):
        """Store data in cache with timestamp."""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    async def _retry_with_fallback(self, operation, fallback_data, max_retries=2, timeout=10):
        """Execute operation with retry logic and fallback."""
        for attempt in range(max_retries + 1):
            try:
                return await asyncio.wait_for(operation(), timeout=timeout)
            except asyncio.TimeoutError:
                if attempt == max_retries:
                    return fallback_data
                await asyncio.sleep(1)  # Brief delay before retry
            except Exception as e:
                if attempt == max_retries:
                    return fallback_data
                await asyncio.sleep(1)
    
    async def get_openai_models(self, api_key: str) -> List[str]:
        """Get available OpenAI models with caching, timeout, and fallback."""
        # Check cache first
        cached_data = self._get_cached_data('openai')
        if cached_data is not None:
            return cached_data
        
        # Fallback models in case of failure
        fallback_models = ['gpt-4o-mini', 'gpt-4', 'gpt-3.5-turbo']
        
        async def discover_models():
            from openai import AsyncOpenAI
            # Add timeout to prevent hangs on PythonAnywhere
            client = AsyncOpenAI(
                api_key=api_key,
                timeout=10.0,  # 10 second timeout for discovery
                http_client=httpx.AsyncClient(
                    timeout=10.0,
                    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
                )
            )
            models = await client.models.list()
            
            # Get all GPT models and sort by capability
            chat_models = []
            for model in models.data:
                if model.id.startswith('gpt-') and 'instruct' not in model.id.lower():
                    chat_models.append(model.id)
            
            # Sort by preference (newer/better models first)
            def model_priority(model_name):
                if 'gpt-4' in model_name:
                    if 'turbo' in model_name: return 1
                    return 2
                elif 'gpt-3.5' in model_name:
                    if '16k' in model_name: return 4
                    return 3
                return 5
            
            chat_models.sort(key=model_priority)
            return chat_models if chat_models else fallback_models
        
        # Use retry with fallback
        result = await self._retry_with_fallback(discover_models, fallback_models, timeout=8)
        self._set_cache_data('openai', result)
        return result
    
    async def get_anthropic_models(self, api_key: str) -> List[str]:
        """Get available Anthropic models with caching."""
        # Check cache first
        cached_data = self._get_cached_data('anthropic')
        if cached_data is not None:
            return cached_data
        
        # Fast fallback to known working models (cheapest first)
        known_models = [
            "claude-3-haiku-20240307",
            "claude-3-5-haiku-20241022",
            "claude-3-5-sonnet-20241022",
        ]
        
        self._set_cache_data('anthropic', known_models)
        return known_models
    
    async def get_google_models(self, api_key: str) -> List[str]:
        """Get available Google models with caching and actual API discovery."""
        # Check cache first
        cached_data = self._get_cached_data('google')
        if cached_data is not None:
            return cached_data
        
        # Try to discover actual models
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            models = genai.list_models()
            available = []
            
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    model_name = model.name.replace('models/', '')
                    available.append(model_name)
            
            if available:
                # Prioritize newer models
                def priority(name):
                    if '2.5' in name: return 0
                    if '2.0' in name: return 1
                    if 'flash' in name: return 2
                    if 'pro' in name: return 3
                    return 4
                
                available.sort(key=priority)
                self._set_cache_data('google', available[:10])  # Top 10
                return available[:10]
        except Exception as e:
            logger.warning(f"Failed to discover Google models: {e}")
        
        # Fallback to known working models
        known_models = [
            'gemini-2.5-flash',
            'gemini-2.0-flash', 
            'gemini-2.5-pro',
            'gemini-flash-latest',
            'gemini-pro-latest'
        ]
        
        self._set_cache_data('google', known_models)
        return known_models
    
    async def discover_endpoints(self, base_urls: List[str], api_key: str) -> List[str]:
        """Test which endpoints are accessible."""
        working_endpoints = []
        
        for url in base_urls:
            try:
                headers = {"Authorization": f"Bearer {api_key}"}
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{url}/models", headers=headers, timeout=5) as response:
                        if response.status < 500:  # Accept 4xx (auth issues) but not 5xx (server down)
                            working_endpoints.append(url)
            except Exception:
                continue
        
        if not working_endpoints:
            raise Exception(f"No accessible endpoints found from: {base_urls}")
        
        return working_endpoints
    
    async def get_grok_config(self, api_key: str) -> Dict[str, List[str]]:
        """Get Grok endpoints and models with caching."""
        cache_key = f"grok_{hash(api_key)}"
        
        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Fast fallback configuration
        config = {
            "endpoints": ["https://api.x.ai/v1"],
            "models": ["grok-beta", "grok-2", "grok-1"]
        }
        
        self._set_cache_data(cache_key, config)
        return config
    
    async def get_meta_config(self, api_key: str) -> Dict[str, List[str]]:
        """Get Meta/Llama endpoints and models with caching."""
        cache_key = 'meta'
        
        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Fast fallback configuration
        config = {
            "endpoints": ["https://api.together.xyz/v1"],
            "models": [
                "meta-llama/Llama-2-70b-chat-hf",
                "meta-llama/Llama-2-13b-chat-hf", 
                "meta-llama/Llama-2-7b-chat-hf"
            ]
        }
        
        self._set_cache_data(cache_key, config)
        return config
    
    def get_model_cost(self, model_name: str) -> Dict[str, float]:
        """Get cost information for a model"""
        return self.MODEL_COSTS.get(model_name, {'input': 0, 'output': 0, 'total': 0})
    
    def compare_costs(self, new_model: str, existing_models: List[str]) -> Tuple[float, str]:
        """Compare cost of new model vs existing models
        
        Returns:
            (percentage_difference, comparison_text)
        """
        new_cost = self.get_model_cost(new_model).get('total', 0)
        
        if not existing_models or new_cost == 0:
            return (0, "Unknown cost comparison")
        
        # Calculate average of existing models
        total_existing = sum(self.get_model_cost(m).get('total', 0) for m in existing_models)
        count_existing = sum(1 for m in existing_models if self.get_model_cost(m).get('total', 0) > 0)
        
        if count_existing == 0:
            return (0, "No cost data for existing models")
        
        avg_existing = total_existing / count_existing
        diff_percent = ((new_cost - avg_existing) / avg_existing) * 100
        
        if diff_percent > 20:
            return (diff_percent, f"⚠️  {diff_percent:.1f}% MORE expensive")
        elif diff_percent < -20:
            return (diff_percent, f"✅ {abs(diff_percent):.1f}% CHEAPER")
        else:
            return (diff_percent, f"Similar cost ({diff_percent:+.1f}%)")
    
    async def update_config_file(self, provider: str, new_models: List[str]) -> bool:
        """Auto-update model_config.py with new models
        
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            from .admin_logger import get_admin_logger
            admin_log = get_admin_logger()
            
            # Read current config
            config_content = self.config_file.read_text()
            
            # Find the provider's model list
            start_marker = f"'{provider}': ["
            end_marker = "],"
            
            start_idx = config_content.find(start_marker)
            if start_idx == -1:
                logger.error(f"Could not find {provider} in config file")
                return False
            
            # Find the end of this provider's list
            end_idx = config_content.find(end_marker, start_idx)
            if end_idx == -1:
                logger.error(f"Could not find end of {provider} list in config")
                return False
            
            # Build new model list string
            new_list_str = f"'{provider}': [\n"
            for i, model in enumerate(new_models):
                cost_info = self.get_model_cost(model)
                cost = cost_info.get('total', 0)
                comment = f"  # ${cost}/1M tokens" if cost > 0 else ""
                if i == 0:
                    comment += " ⭐ Primary"
                new_list_str += f"        '{model}',{comment}\n"
            new_list_str += "    ],"
            
            # Replace the old list with new one
            new_content = (
                config_content[:start_idx] +
                new_list_str +
                config_content[end_idx + len(end_marker):]
            )
            
            # Write back to file
            self.config_file.write_text(new_content)
            
            # Log the update
            admin_log.log_config_update(provider, new_models)
            logger.info(f"✅ Updated config file for {provider} with {len(new_models)} models")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update config file: {e}")
            return False
    
    async def discover_and_use_new_models(self, provider: str, api_key: str, 
                                         old_models: List[str]) -> Tuple[Optional[List[str]], Optional[str]]:
        """Discover new models when all fallbacks fail
        
        Returns:
            (new_model_list, working_model) if successful
            (None, None) if discovery failed
        """
        from .admin_logger import get_admin_logger
        admin_log = get_admin_logger()
        
        try:
            logger.info(f"🔍 Starting auto-discovery for {provider}...")
            admin_log.log_fallback_failure(provider, old_models, "All configured models failed")
            
            # Discover available models
            if provider == 'openai':
                new_models = await self.get_openai_models(api_key)
            elif provider == 'anthropic':
                new_models = await self.get_anthropic_models(api_key)
            elif provider == 'google':
                new_models = await self.get_google_models(api_key)
            elif provider == 'meta':
                config = await self.get_meta_config(api_key)
                new_models = config.get('models', [])
            else:
                logger.error(f"Unknown provider: {provider}")
                return (None, None)
            
            if not new_models:
                logger.error(f"No models discovered for {provider}")
                return (None, None)
            
            # Log discovery with cost comparison
            admin_log.log_model_discovery(
                provider, old_models, new_models, self.MODEL_COSTS
            )
            
            # Update config file
            await self.update_config_file(provider, new_models)
            
            # Return first model to try
            working_model = new_models[0] if new_models else None
            
            if working_model:
                admin_log.log_discovery_success(provider, working_model, len(old_models) + 1)
                logger.info(f"✅ Discovery successful: Will use {working_model}")
            
            return (new_models, working_model)
            
        except Exception as e:
            logger.error(f"Discovery failed for {provider}: {e}")
            return (None, None)


# Singleton instance
_discovery = None

def get_discovery() -> ModelDiscovery:
    """Get the singleton ModelDiscovery instance"""
    global _discovery
    if _discovery is None:
        _discovery = ModelDiscovery()
    return _discovery

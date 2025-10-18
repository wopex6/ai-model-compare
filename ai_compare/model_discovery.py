import asyncio
import aiohttp
from typing import List, Dict, Optional
import json
import os
import time
from dotenv import load_dotenv

load_dotenv(override=True)

class ModelDiscovery:
    _instance = None
    _initialized = False
    
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
            client = AsyncOpenAI(api_key=api_key)
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
        
        # Fast fallback to known working models
        known_models = [
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229", 
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]
        
        self._set_cache_data('anthropic', known_models)
        return known_models
    
    async def get_google_models(self, api_key: str) -> List[str]:
        """Get available Google models with caching."""
        # Check cache first
        cached_data = self._get_cached_data('google')
        if cached_data is not None:
            return cached_data
        
        # Fast fallback to known working models
        known_models = [
            'gemini-1.5-pro',
            'gemini-1.5-flash', 
            'gemini-pro',
            'gemini-pro-vision'
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

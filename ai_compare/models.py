from abc import ABC, abstractmethod
import os
import asyncio
import aiohttp
from typing import Optional
from dotenv import load_dotenv
from .model_discovery import ModelDiscovery
import httpx
import random
import logging

load_dotenv()

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}

async def _retry_with_backoff(coro_func, max_attempts: int = 3, base_delay: float = 1.0):
    """Retry an async callable with exponential backoff and jitter."""
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return await coro_func()
        except Exception as e:
            last_exc = e
            # Check if it's a retryable HTTP error
            status = getattr(e, 'status', None)
            if status and status not in RETRYABLE_STATUS_CODES:
                raise  # Non-retryable HTTP error
            if attempt < max_attempts - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed ({type(e).__name__}). Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
    raise last_exc

def get_api_key(key_name: str) -> Optional[str]:
    """Get API key if available, return None if not found or empty."""
    key = os.getenv(key_name)
    return key if key and key.strip() else None

class AIModel(ABC):
    @abstractmethod
    async def get_response(self, prompt: str) -> str:
        pass

class ChatGPTModel(AIModel):
    def __init__(self):
        api_key = get_api_key('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found")
        from openai import AsyncOpenAI
        # Add timeout to prevent 504 Gateway Timeout on PythonAnywhere
        self.client = AsyncOpenAI(
            api_key=api_key,
            timeout=20.0,  # 20 second timeout
            http_client=httpx.AsyncClient(
                timeout=20.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        )
        self.api_key = api_key
        self.discovery = ModelDiscovery()
        self.models = None
    
    async def _get_models(self):
        if self.models is None:
            self.models = await self.discovery.get_openai_models(self.api_key)
        return self.models
    
    async def get_response(self, prompt: str) -> str:
        models = await self._get_models()
        for model in models:
            try:
                async def _call():
                    response = await self.client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return response.choices[0].message.content
                return await _retry_with_backoff(_call)
            except Exception as e:
                if model == models[-1]:
                    raise e
                continue

class ClaudeModel(AIModel):
    def __init__(self):
        api_key = get_api_key('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("Anthropic API key not found")
        import anthropic
        # Add timeout to prevent 504 Gateway Timeout on PythonAnywhere
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key,
            timeout=20.0,  # 20 second timeout
            http_client=httpx.AsyncClient(
                timeout=20.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        )
        self.api_key = api_key
        self.discovery = ModelDiscovery()
        self.models = None
    
    async def _get_models(self):
        if self.models is None:
            self.models = await self.discovery.get_anthropic_models(self.api_key)
        return self.models
    
    async def get_response(self, prompt: str, max_tokens: int = 4000) -> str:
        models = await self._get_models()
        for model in models:
            try:
                async def _call():
                    response = await self.client.messages.create(
                        model=model,
                        max_tokens=max_tokens,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return response.content[0].text
                return await _retry_with_backoff(_call)
            except Exception as e:
                if model == models[-1]:
                    raise e
                continue

class GeminiModel(AIModel):
    def __init__(self):
        api_key = get_api_key('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Google API key not found")
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.api_key = api_key
        self.discovery = ModelDiscovery()
        self.models = None
    
    async def _get_models(self):
        if self.models is None:
            self.models = await self.discovery.get_google_models(self.api_key)
        return self.models
    
    async def get_response(self, prompt: str) -> str:
        import google.generativeai as genai
        models = await self._get_models()
        for model_name in models:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                if model_name == models[-1]:
                    raise e
                continue

class MetaModel(AIModel):
    def __init__(self):
        api_key = get_api_key('META_API_KEY')
        if not api_key:
            raise ValueError("Meta API key not found")
        self.api_key = api_key
        self.discovery = ModelDiscovery()
        self.config = None
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Reuse a single session per instance instead of creating one per request."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def _get_config(self):
        if self.config is None:
            self.config = await self.discovery.get_meta_config(self.api_key)
        return self.config
    
    async def get_response(self, prompt: str) -> str:
        config = await self._get_config()
        endpoints = config['endpoints']
        models = config['models']
        
        session = await self._get_session()
        for api_url in endpoints:
            for model in models:
                try:
                    headers = {"Authorization": f"Bearer {self.api_key}"}
                    payload = {
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                    full_url = f"{api_url}/chat/completions" if not api_url.endswith('/chat/completions') else api_url
                    async def _call():
                        async with session.post(full_url, json=payload, headers=headers) as resp:
                            data = await resp.json()
                            if "choices" in data and len(data["choices"]) > 0:
                                return data["choices"][0]["message"]["content"]
                            elif "response" in data:
                                return data["response"]
                            else:
                                raise Exception(f"Unexpected response format: {data}")
                    return await _retry_with_backoff(_call)
                except Exception as e:
                    if api_url == endpoints[-1] and model == models[-1]:
                        raise e
                    continue

class GrokModel(AIModel):
    def __init__(self):
        api_key = get_api_key('GROK_API_KEY')
        if not api_key:
            raise ValueError("Grok API key not found")
        self.api_key = api_key
        self.discovery = ModelDiscovery()
        self.config = None
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Reuse a single session per instance instead of creating one per request."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _get_config(self):
        if self.config is None:
            self.config = await self.discovery.get_grok_config(self.api_key)
        return self.config
    
    async def get_response(self, prompt: str) -> str:
        config = await self._get_config()
        endpoints = config['endpoints']
        models = config['models']
        session = await self._get_session()
        
        for api_url in endpoints:
            for model in models:
                try:
                    headers = {"Authorization": f"Bearer {self.api_key}"}
                    payload = {
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                    full_url = f"{api_url}/chat/completions" if not api_url.endswith('/chat/completions') else api_url
                    async def _call():
                        async with session.post(full_url, json=payload, headers=headers) as resp:
                            data = await resp.json()
                            if "choices" in data and len(data["choices"]) > 0:
                                return data["choices"][0]["message"]["content"]
                            elif "response" in data:
                                return data["response"]
                            else:
                                raise Exception(f"Unexpected response format: {data}")
                    return await _retry_with_backoff(_call)
                except Exception as e:
                    if api_url == endpoints[-1] and model == models[-1]:
                        raise e
                    continue

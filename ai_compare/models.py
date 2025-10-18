from abc import ABC, abstractmethod
import os
import asyncio
import aiohttp
from typing import Optional
from dotenv import load_dotenv
from .model_discovery import ModelDiscovery

load_dotenv()

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
        self.client = AsyncOpenAI(api_key=api_key)
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
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content
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
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.api_key = api_key
        self.discovery = ModelDiscovery()
        self.models = None
    
    async def _get_models(self):
        if self.models is None:
            self.models = await self.discovery.get_anthropic_models(self.api_key)
        return self.models
    
    async def get_response(self, prompt: str) -> str:
        models = await self._get_models()
        for model in models:
            try:
                # Let Claude decide appropriate response length
                response = await self.client.messages.create(
                    model=model,
                    max_tokens=4000,  # Reasonable default, but could be model-specific
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
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
    
    async def _get_config(self):
        if self.config is None:
            self.config = await self.discovery.get_meta_config(self.api_key)
        return self.config
    
    async def get_response(self, prompt: str) -> str:
        config = await self._get_config()
        endpoints = config['endpoints']
        models = config['models']
        
        for api_url in endpoints:
            for model in models:
                try:
                    headers = {"Authorization": f"Bearer {self.api_key}"}
                    payload = {
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                    full_url = f"{api_url}/chat/completions" if not api_url.endswith('/chat/completions') else api_url
                    async with aiohttp.ClientSession() as session:
                        async with session.post(full_url, json=payload, headers=headers) as response:
                            data = await response.json()
                            # Handle different response formats
                            if "choices" in data and len(data["choices"]) > 0:
                                return data["choices"][0]["message"]["content"]
                            elif "response" in data:
                                return data["response"]
                            else:
                                raise Exception(f"Unexpected response format: {data}")
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
    
    async def _get_config(self):
        if self.config is None:
            self.config = await self.discovery.get_grok_config(self.api_key)
        return self.config
    
    async def get_response(self, prompt: str) -> str:
        config = await self._get_config()
        endpoints = config['endpoints']
        models = config['models']
        
        for api_url in endpoints:
            for model in models:
                try:
                    headers = {"Authorization": f"Bearer {self.api_key}"}
                    payload = {
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                    full_url = f"{api_url}/chat/completions" if not api_url.endswith('/chat/completions') else api_url
                    async with aiohttp.ClientSession() as session:
                        async with session.post(full_url, json=payload, headers=headers) as response:
                            data = await response.json()
                            # Handle different response formats
                            if "choices" in data and len(data["choices"]) > 0:
                                return data["choices"][0]["message"]["content"]
                            elif "response" in data:
                                return data["response"]
                            else:
                                raise Exception(f"Unexpected response format: {data}")
                except Exception as e:
                    if api_url == endpoints[-1] and model == models[-1]:
                        raise e
                    continue

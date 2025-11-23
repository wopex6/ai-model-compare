from abc import ABC, abstractmethod
import os
import asyncio
from typing_extensions import override
import aiohttp
from typing import Optional
from dotenv import load_dotenv
from .model_config import get_fallback_models, get_primary_model

# Load environment variables once at module import
load_dotenv(override=True)

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
        
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.models = get_fallback_models('openai')

    
    async def get_response(self, prompt: str) -> str:
        """Try models in order until one works"""
        last_error = None
        
        for model in self.models:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                # Try next model if this one fails
                continue
        
        # If all models failed, raise the last error
        raise last_error if last_error else Exception("All OpenAI models failed")

class ClaudeModel(AIModel):
    def __init__(self):
        api_key = get_api_key('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("Anthropic API key not found")
        import anthropic
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.models = get_fallback_models('anthropic')
    
    async def get_response(self, prompt: str) -> str:
        """Try models in order until one works"""
        last_error = None
        
        for model in self.models:
            try:
                response = await self.client.messages.create(
                    model=model,
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            except Exception as e:
                last_error = e
                continue
        
        raise last_error if last_error else Exception("All Anthropic models failed")

class GeminiModel(AIModel):
    def __init__(self):
        api_key = get_api_key('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Google API key not found")
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.genai = genai
        self.api_key = api_key
        self.models = get_fallback_models('google')
    
    async def get_response(self, prompt: str) -> str:
        """Try models in order until one works, auto-discover if all fail"""
        last_error = None
        
        # Try all configured fallback models
        for model_name in self.models:
            try:
                model = self.genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                last_error = e
                continue
        
        # All fallbacks failed - trigger auto-discovery
        try:
            from .model_discovery import get_discovery
            discovery = get_discovery()
            
            # Discover and update config with new models
            new_models, working_model = await discovery.discover_and_use_new_models(
                'google', self.api_key, self.models
            )
            
            if working_model:
                # Try the newly discovered model
                model = self.genai.GenerativeModel(working_model)
                response = model.generate_content(prompt)
                # Update local models list
                self.models = new_models
                return response.text
        except Exception as discovery_error:
            last_error = discovery_error
        
        raise last_error if last_error else Exception("All Google models failed, including auto-discovery")

class MetaModel(AIModel):
    def __init__(self):
        api_key = get_api_key('META_API_KEY')
        if not api_key:
            raise ValueError("Meta API key not found")
        self.api_key = api_key
        self.api_url = "https://api.together.xyz/v1/chat/completions"
        self.models = get_fallback_models('meta')
    
    async def get_response(self, prompt: str) -> str:
        """Try models in order until one works"""
        last_error = None
        
        for model_name in self.models:
            try:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}]
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.api_url, json=payload, headers=headers) as response:
                        data = await response.json()
                        
                        # Handle different response formats
                        if "choices" in data and len(data["choices"]) > 0:
                            return data["choices"][0]["message"]["content"]
                        elif "response" in data:
                            return data["response"]
                        elif "error" in data:
                            last_error = Exception(f"Meta API error: {data['error']}")
                            continue
                        else:
                            last_error = Exception(f"Unexpected Meta response format: {data}")
                            continue
            except Exception as e:
                last_error = e
                continue
        
        raise last_error if last_error else Exception("All Meta models failed")

class GrokModel(AIModel):
    def __init__(self):
        api_key = get_api_key('GROK_API_KEY')
        if not api_key:
            raise ValueError("Grok API key not found")
        self.api_key = api_key
        self.api_url = "https://api.x.ai/v1/chat/completions"
    
    async def get_response(self, prompt: str) -> str:
        # Try different Grok model names based on xAI documentation
        models_to_try = [
            "grok-4",
            "grok-3", 
            "grok-2",
            "grok-beta",
            "grok-vision-beta", 
            "grok-2-1212",
            "grok-2-vision-1212",
            "grok-2-latest",
            "grok-1"
        ]
        
        last_error = None
        
        for model in models_to_try:
            try:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.api_url, json=payload, headers=headers) as response:
                        data = await response.json()
                        
                        # If successful response, return it
                        if "choices" in data and len(data["choices"]) > 0:
                            return data["choices"][0]["message"]["content"]
                        elif "response" in data:
                            return data["response"]
                        elif "content" in data:
                            return data["content"]
                        elif "text" in data:
                            return data["text"]
                        elif "error" in data:
                            last_error = data["error"]
                            # If model doesn't exist, try next one
                            if "does not exist" in str(data["error"]) or "not found" in str(data["error"]):
                                continue
                            # For other errors, try next model too
                            continue
                        else:
                            last_error = f"Unexpected response format: {data}"
                            continue
                            
            except Exception as e:
                last_error = str(e)
                # Try next model for any error
                continue
        
        # If all models failed, provide helpful error message
        raise Exception(f"Grok API unavailable. Last error: {last_error}. Please check your API key or try again later.")

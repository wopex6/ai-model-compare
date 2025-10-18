from abc import ABC, abstractmethod
import os
import asyncio
from typing_extensions import override
import aiohttp
from typing import Optional
from dotenv import load_dotenv

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

    
    async def get_response(self, prompt: str) -> str:
        # Direct copy of gpt.py approach
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

class ClaudeModel(AIModel):
    def __init__(self):
        api_key = get_api_key('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("Anthropic API key not found")
        import anthropic
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
    
    async def get_response(self, prompt: str) -> str:
        response = await self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

class GeminiModel(AIModel):
    def __init__(self):
        api_key = get_api_key('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Google API key not found")
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def get_response(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text

class MetaModel(AIModel):
    def __init__(self):
        api_key = get_api_key('META_API_KEY')
        if not api_key:
            raise ValueError("Meta API key not found")
        self.api_key = api_key
        self.api_url = "https://api.together.xyz/v1/chat/completions"
    
    async def get_response(self, prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": "meta-llama/Llama-2-7b-chat-hf",
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
                    raise Exception(f"Meta API error: {data['error']}")
                else:
                    raise Exception(f"Unexpected Meta response format: {data}")

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

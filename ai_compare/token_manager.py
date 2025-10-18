"""Token management utilities for AI model input validation and truncation."""

import re
from typing import Dict, Tuple
from abc import ABC, abstractmethod

class TokenCounter(ABC):
    """Abstract base class for token counting strategies."""
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in the given text."""
        pass

class ApproximateTokenCounter(TokenCounter):
    """Approximate token counter using word-based estimation."""
    
    def count_tokens(self, text: str) -> int:
        # Rough approximation: 1 token ≈ 0.75 words for English text
        words = len(re.findall(r'\b\w+\b', text))
        return int(words / 0.75)

class TokenManager:
    """Manages token limits and input truncation for different AI models."""
    
    # Conservative input token limits for each model type
    MODEL_LIMITS = {
        'openai': {
            'gpt-4': 8000,
            'gpt-4-turbo': 128000,
            'gpt-3.5-turbo': 4000,
            'default': 4000
        },
        'anthropic': {
            'claude-3-opus': 200000,
            'claude-3-sonnet': 200000,
            'claude-3-haiku': 200000,
            'claude-2': 100000,
            'default': 100000
        },
        'google': {
            'gemini-pro': 30000,
            'gemini-1.5-pro': 1000000,
            'default': 30000
        },
        'meta': {
            'llama-2': 4000,
            'llama-3': 8000,
            'default': 4000
        },
        'grok': {
            'grok-1': 8000,
            'default': 8000
        }
    }
    
    def __init__(self, token_counter: TokenCounter = None):
        self.token_counter = token_counter or ApproximateTokenCounter()
        self._model_limits_cache = {}
    
    def get_model_limit(self, provider: str, model_name: str = None) -> int:
        """Get input token limit for a specific model."""
        provider_limits = self.MODEL_LIMITS.get(provider.lower(), {})
        
        if model_name:
            # Try exact match first
            if model_name in provider_limits:
                return provider_limits[model_name]
            
            # Try partial match for model families
            for limit_model, limit in provider_limits.items():
                if limit_model in model_name.lower() or model_name.lower() in limit_model:
                    return limit
        
        return provider_limits.get('default', 4000)
    
    def validate_and_truncate(self, text: str, provider: str, model_name: str = None) -> Tuple[str, bool]:
        """
        Validate input length and truncate if necessary.
        
        Returns:
            Tuple of (processed_text, was_truncated)
        """
        limit = self.get_model_limit(provider, model_name)
        current_tokens = self.token_counter.count_tokens(text)
        
        if current_tokens <= limit:
            return text, False
        
        # Need to truncate - use intelligent truncation
        return self._intelligent_truncate(text, limit), True
    
    def _intelligent_truncate(self, text: str, max_tokens: int) -> str:
        """
        Intelligently truncate text while preserving important content.
        
        Strategy:
        1. Keep the beginning (context/question)
        2. Keep the end (conclusion/specific request)
        3. Summarize or remove middle content if needed
        """
        current_tokens = self.token_counter.count_tokens(text)
        
        if current_tokens <= max_tokens:
            return text
        
        # Reserve tokens for truncation notice
        available_tokens = max_tokens - 50
        
        # Split into sentences for better truncation points
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        if len(sentences) <= 2:
            # Very short text, just truncate by words
            words = text.split()
            target_words = int(available_tokens * 0.75)  # Approximate conversion
            truncated = ' '.join(words[:target_words])
            return f"{truncated}... [Content truncated to fit model limits]"
        
        # Keep first and last sentences, truncate middle
        first_part = sentences[0]
        last_part = sentences[-1]
        
        first_tokens = self.token_counter.count_tokens(first_part)
        last_tokens = self.token_counter.count_tokens(last_part)
        
        # If first and last parts are too long, truncate them too
        if first_tokens + last_tokens > available_tokens:
            if first_tokens > available_tokens // 2:
                words = first_part.split()
                target_words = int((available_tokens // 2) * 0.75)
                first_part = ' '.join(words[:target_words]) + "..."
            
            if last_tokens > available_tokens // 2:
                words = last_part.split()
                target_words = int((available_tokens // 2) * 0.75)
                last_part = "..." + ' '.join(words[-target_words:])
            
            return f"{first_part} [Middle content truncated] {last_part}"
        
        # Try to fit some middle content
        remaining_tokens = available_tokens - first_tokens - last_tokens
        middle_sentences = sentences[1:-1]
        
        if remaining_tokens > 100 and middle_sentences:
            # Add some middle content
            middle_text = ""
            for sentence in middle_sentences:
                sentence_tokens = self.token_counter.count_tokens(sentence)
                if sentence_tokens <= remaining_tokens:
                    middle_text += sentence + " "
                    remaining_tokens -= sentence_tokens
                else:
                    break
            
            if middle_text.strip():
                return f"{first_part} {middle_text.strip()} [Some content truncated] {last_part}"
        
        return f"{first_part} [Middle content truncated to fit model limits] {last_part}"
    
    def get_all_limits(self) -> Dict[str, Dict[str, int]]:
        """Get all configured model limits."""
        return self.MODEL_LIMITS.copy()

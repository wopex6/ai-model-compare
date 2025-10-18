from abc import ABC, abstractmethod
import asyncio
from typing import Dict, List, Optional
from .models import ChatGPTModel, ClaudeModel, GeminiModel, MetaModel, GrokModel
from .token_manager import TokenManager

class AICompare:
    def __init__(self):
        self.models = {}
        self._models_initialized = False
        self.token_manager = TokenManager()
        self._model_providers = {}
        
    async def _ensure_models_initialized(self):
        """Initialize models only once per program run."""
        if not self._models_initialized:
            await self._initialize_available_models()
            self._models_initialized = True
        
    async def _initialize_available_models(self):
        """Initialize only the models that have valid API keys."""
        model_classes = {
            'chatgpt': ChatGPTModel,
            'claude': ClaudeModel,
            'gemini': GeminiModel,
            'meta': MetaModel,
            'grok': GrokModel
        }
        
        for name, model_class in model_classes.items():
            try:
                model_instance = model_class()
                # Store provider mapping for token management
                provider_map = {
                    'chatgpt': 'openai',
                    'claude': 'anthropic', 
                    'gemini': 'google',
                    'meta': 'meta',
                    'grok': 'grok'
                }
                self._model_providers[name] = provider_map[name]
                
                # Pre-initialize the model configurations to cache them
                if hasattr(model_instance, '_get_models'):
                    await model_instance._get_models()
                elif hasattr(model_instance, '_get_config'):
                    await model_instance._get_config()
                self.models[name] = model_instance
            except ValueError:
                pass  # Skip models with missing API keys
    
    async def get_available_models(self) -> List[str]:
        """Get list of available model names."""
        await self._ensure_models_initialized()
        return list(self.models.keys())
    
    async def ask_all(self, question: str) -> Dict[str, str]:
        """Ask the same question to all available AI models concurrently."""
        await self._ensure_models_initialized()
        
        if not self.models:
            raise ValueError("No AI models available. Please provide at least one valid API key.")
        
        tasks = []
        for model_name, model in self.models.items():
            tasks.append(self._safe_ask(model_name, model, question))
        
        responses = await asyncio.gather(*tasks)
        result = dict(responses)
        
        # Auto-generate summaries if multiple successful responses
        successful_responses = {k: v for k, v in result.items() if not v.startswith('Error:')}
        if len(successful_responses) > 1:
            # Generate both summary types automatically
            try:
                summary_task = self.summarize_responses(successful_responses)
                consolidate_task = self.consolidate_responses(successful_responses)
                
                summary, consolidated = await asyncio.gather(summary_task, consolidate_task)
                
                result['_auto_summary'] = summary[:4000] if len(summary) > 4000 else summary
                result['_auto_consolidated'] = consolidated[:4000] if len(consolidated) > 4000 else consolidated
            except Exception as e:
                # If auto-generation fails, continue without summaries
                pass
        
        return result
    
    async def _safe_ask(self, model_name: str, model, question: str) -> tuple:
        """Safely ask a question to a model with error handling and token validation."""
        try:
            # Validate and truncate input if necessary
            provider = self._model_providers.get(model_name, 'openai')
            processed_question, was_truncated = self.token_manager.validate_and_truncate(
                question, provider, model_name
            )
            
            # Add truncation notice if content was modified
            if was_truncated:
                processed_question += f"\n\n[Note: Input was automatically truncated to fit {provider} model limits]"
            
            response = await model.get_response(processed_question)
            
            # Add truncation info to response if applicable
            if was_truncated:
                response = f"[Input was truncated for token limits]\n\n{response}"
            
            return (model_name, response)
        except Exception as e:
            return (model_name, f"Error: {str(e)}")
    
    async def summarize_responses(self, responses: Dict[str, str], model_name: str = None) -> str:
        """Use specified model to summarize all responses."""
        await self._ensure_models_initialized()
        
        summary_prompt = f"""Analyze these AI responses and create a clear, comprehensive summary (maximum 4000 characters):

{self._format_responses_for_summary(responses)}

Create a well-structured summary that:
• Synthesizes the key insights from all models
• Highlights areas of consensus and disagreement
• Provides a balanced, comprehensive answer
• Uses clear formatting with bullet points or numbered lists where helpful
• Maintains a similar length and tone as the original responses
• Keep response under 4000 characters

Focus on creating a unified answer that combines the best elements from each response."""
        # Use first available model if none specified or specified model not available
        if not model_name or model_name not in self.models:
            model_name = next(iter(self.models))
        
        return await self.models[model_name].get_response(summary_prompt)
    
    async def consolidate_responses(self, responses: Dict[str, str], model_name: str = None) -> str:
        """Create a consolidated response that matches AI response format and length."""
        await self._ensure_models_initialized()
        
        consolidate_prompt = f"""Based on these multiple AI responses, write a single consolidated answer (maximum 4000 characters):

{self._format_responses_for_summary(responses)}

Requirements:
• Write as if you're giving the definitive answer to the original question
• Match the typical length and style of AI responses (2-4 paragraphs)
• Integrate the best insights from all responses seamlessly
• Don't mention that this is a summary or consolidation
• Use natural, conversational tone
• Include specific details and examples where multiple models agree
• Present conflicting viewpoints as "some considerations include..." or "alternatively..."
• Keep response under 4000 characters

Write the response as a complete, standalone answer."""
        # Use first available model if none specified or specified model not available
        if not model_name or model_name not in self.models:
            model_name = next(iter(self.models))
        
        return await self.models[model_name].get_response(consolidate_prompt)
    
    def _format_responses(self, responses: Dict[str, str]) -> str:
        return "\n\n".join([f"{name.upper()}:\n{response}" for name, response in responses.items()])
    
    def _format_responses_for_summary(self, responses: Dict[str, str]) -> str:
        """Format responses with better structure for summary generation."""
        formatted = []
        for name, response in responses.items():
            if not response.startswith('Error:'):
                formatted.append(f"=== {name.upper()} ===\n{response}")
        return "\n\n".join(formatted)

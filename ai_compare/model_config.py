"""
Model configuration with automatic fallbacks for deprecated models
Automatically tries alternative models if primary ones fail
"""

# Model versions with fallback options (ordered by preference)
MODEL_VERSIONS = {
    'openai': [
        'gpt-4o-mini',           # Current recommended
        'gpt-4o',                # Fallback 1
        'gpt-4-turbo',           # Fallback 2
        'gpt-4',                 # Fallback 3
        'gpt-3.5-turbo',         # Fallback 4
    ],
    'anthropic': [
        'claude-3-5-sonnet-20241022',  # Latest Sonnet
        'claude-3-5-haiku-20241022',   # Latest Haiku
        'claude-3-haiku-20240307',     # Current fallback
        'claude-3-sonnet-20240229',    # Older Sonnet
        'claude-3-opus-20240229',      # Most capable (expensive)
    ],
    'google': [
        'gemini-2.5-flash',      # Latest fast model (2025)
        'gemini-2.0-flash',      # Stable 2.0 version
        'gemini-2.5-pro',        # Most capable 2.5
        'gemini-flash-latest',   # Auto-updated to latest flash
        'gemini-pro-latest',     # Auto-updated to latest pro
        'gemini-2.0-flash-exp',  # Experimental 2.0
    ],
    'meta': [
        'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo',  # Current
        'meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo', # More capable
        'meta-llama/Llama-3-8b-chat-hf',                # Fallback 1
        'meta-llama/Llama-2-7b-chat-hf',                # Fallback 2
    ]
}

# Model cost information (approximate, per 1M tokens)
MODEL_COSTS = {
    'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
    'gpt-4o': {'input': 2.50, 'output': 10.00},
    'claude-3-5-haiku-20241022': {'input': 1.00, 'output': 5.00},
    'claude-3-haiku-20240307': {'input': 0.25, 'output': 1.25},
    'gemini-1.5-flash': {'input': 0.075, 'output': 0.30},
    'gemini-1.5-pro': {'input': 1.25, 'output': 5.00},
}

def get_primary_model(provider: str) -> str:
    """Get the primary (recommended) model for a provider"""
    return MODEL_VERSIONS.get(provider, [''])[0]

def get_fallback_models(provider: str) -> list:
    """Get all models for a provider (for fallback logic)"""
    return MODEL_VERSIONS.get(provider, [])

def get_model_cost(model_name: str) -> dict:
    """Get cost information for a model"""
    return MODEL_COSTS.get(model_name, {'input': 0, 'output': 0})

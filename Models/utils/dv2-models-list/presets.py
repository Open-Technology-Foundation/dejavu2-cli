"""
Predefined filter presets for common use cases.
"""

# Filter presets as lists of filter expressions
FILTER_PRESETS = {
  'production': [
    'available:>=:8',
    'enabled:>=:5'
  ],
  
  'experimental': [
    'available:<=:3',
    'enabled:>=:1'
  ],
  
  'disabled': [
    'enabled:equals:0'
  ],
  
  'unavailable': [
    'available:equals:0'
  ],
  
  'vision': [
    'vision:>=:1'
  ],
  
  'llm': [
    'model_category:equals:LLM'
  ],
  
  'embedding': [
    'model_category:equals:embed'
  ],
  
  'anthropic': [
    'parent:equals:Anthropic'
  ],
  
  'openai': [
    'parent:equals:OpenAI'
  ],
  
  'google': [
    'parent:equals:Google'
  ],
  
  'latest': [
    'model:contains:latest'
  ],
  
  'large-context': [
    'context_window:>=:100000'
  ],
  
  'claude': [
    'model:starts_with:claude'
  ],
  
  'gpt': [
    'model:contains:gpt'
  ],
  
  'o1': [
    'model:starts_with:o1'
  ],
  
  'free': [
    'token_costs:contains:$0.00'
  ]
}

# Preset descriptions for help text
PRESET_DESCRIPTIONS = {
  'production': 'Production-ready models (available>=8, enabled>=5)',
  'experimental': 'Experimental models (available<=3, enabled>=1)',
  'disabled': 'Disabled models (enabled=0)',
  'unavailable': 'Unavailable models (available=0)',
  'vision': 'Vision-capable models',
  'llm': 'Language models only',
  'embedding': 'Embedding models only',
  'anthropic': 'Anthropic models',
  'openai': 'OpenAI models',
  'google': 'Google models',
  'latest': 'Latest model versions',
  'large-context': 'Models with 100k+ context window',
  'claude': 'Claude family models',
  'gpt': 'GPT family models',
  'o1': 'OpenAI O1 reasoning models',
  'free': 'Free tier models'
}
#fin
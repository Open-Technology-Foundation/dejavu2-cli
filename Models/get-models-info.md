# Get Models Information

## ANTHROPIC

### Models Information

https://docs.anthropic.com/en/api/models-list

```bash
source .venv/bin/activate
```

```python
import anthropic

client = anthropic.Anthropic()

print(client.models.list(limit=100))

```

Example output:

```
SyncPage[ModelInfo](data=[ModelInfo(id='claude-3-7-sonnet-20250219', created_at=datetime.datetime(2025, 2, 24, 0, 0, tzinfo=datetime.timezone.utc), display_name='Claude 3.7 Sonnet', type='model'), ModelInfo(id='claude-3-5-sonnet-20241022', created_at=datetime.datetime(2024, 10, 22, 0, 0, tzinfo=datetime.timezone.utc), display_name='Claude 3.5 Sonnet (New)', type='model'), ModelInfo(id='claude-3-5-haiku-20241022', created_at=datetime.datetime(2024, 10, 22, 0, 0, tzinfo=datetime.timezone.utc), display_name='Claude 3.5 Haiku', type='model'), ModelInfo(id='claude-3-5-sonnet-20240620', created_at=datetime.datetime(2024, 6, 20, 0, 0, tzinfo=datetime.timezone.utc), display_name='Claude 3.5 Sonnet (Old)', type='model'), ModelInfo(id='claude-3-haiku-20240307', created_at=datetime.datetime(2024, 3, 7, 0, 0, tzinfo=datetime.timezone.utc), display_name='Claude 3 Haiku', type='model'), ModelInfo(id='claude-3-opus-20240229', created_at=datetime.datetime(2024, 2, 29, 0, 0, tzinfo=datetime.timezone.utc), display_name='Claude 3 Opus', type='model'), ModelInfo(id='claude-3-sonnet-20240229', created_at=datetime.datetime(2024, 2, 29, 0, 0, tzinfo=datetime.timezone.utc), display_name='Claude 3 Sonnet', type='model'), ModelInfo(id='claude-2.1', created_at=datetime.datetime(2023, 11, 21, 0, 0, tzinfo=datetime.timezone.utc), display_name='Claude 2.1', type='model'), ModelInfo(id='claude-2.0', created_at=datetime.datetime(2023, 7, 11, 0, 0, tzinfo=datetime.timezone.utc), display_name='Claude 2.0', type='model')], has_more=False, first_id='claude-3-7-sonnet-20250219', last_id='claude-2.0')
```

https://docs.anthropic.com/en/docs/about-claude/models/all-models


## OPENAI

### Models Information

```bash
source .venv/bin/activate
```

```
from openai import OpenAI
client = OpenAI()

print(client.models.list())
```


https://openai.com/api/pricing/


## Example Output Format

{
  "claude-3-7-sonnet-latest": {
    "model": "claude-3-7-sonnet-latest",
    "alias": "sonnet",
    "parent": "Anthropic",
    "model_category": "LLM",
    "family": "claude3",
    "series": "claude3",
    "description": "Highest level of intelligence and capability with toggleable extended thinking",
    "training_data": "2024-10",
    "data_cutoff_date": "2024-10",
    "url": "https://api.anthropic.com/v1",
    "apikey": "ANTHROPIC_API_KEY",
    "context_window": 200000,
    "max_output_tokens": 128000,
    "token_costs": "$3.00/$15.00",
    "vision": 1,
    "available": 9,
    "enabled": 1
  },
  "claude-3-5-sonnet-latest": {
    "model": "claude-3-5-sonnet-latest",
    "alias": "sonnet35",
    "parent": "Anthropic",
    "model_category": "LLM",
    "family": "claude3",
    "series": "claude3",
    "description": "Claude 3.5 Sonnet with extended 8K tokens output",
    "training_data": "2024-04",
    "data_cutoff_date": "2024-04",
    "url": "https://api.anthropic.com/v1",
    "apikey": "ANTHROPIC_API_KEY",
    "context_window": 200000,
    "max_output_tokens": 8192,
    "token_costs": "$3.00/$15.00",
    "vision": 1,
    "available": 9,
    "enabled": 1
  },
  "claude-3-5-haiku-latest": {
    "model": "claude-3-5-haiku-latest",
    "alias": "haiku",
    "parent": "Anthropic",
    "model_category": "LLM",
    "family": "claude3",
    "series": "claude3",
    "description": "Claude 3 Haiku. Most basic Claude model. Very fast, not always very smart.",
    "training_data": "2024-07",
    "data_cutoff_date": "2024-07",
    "url": "https://api.anthropic.com/v1",
    "apikey": "ANTHROPIC_API_KEY",
    "context_window": 200000,
    "max_output_tokens": 4000,
    "token_costs": "$1.00/$5.00",
    "vision": 1,
    "available": 9,
    "enabled": 1
  },
}

You are permitted to use `curl` to obtain information from websites.

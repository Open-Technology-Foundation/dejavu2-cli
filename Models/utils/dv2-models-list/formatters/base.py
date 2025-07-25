"""
Base formatter class for output formatting.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class ModelFormatter(ABC):
  """Abstract base class for all output formatters."""
  
  @abstractmethod
  def format(self, models: Dict[str, Any], **kwargs) -> str:
    """
    Format the models data for output.
    
    Args:
      models: Dictionary of model name to model data
      **kwargs: Additional formatting options
      
    Returns:
      Formatted string output
    """
    pass
  
  def get_all_fields(self, models: Dict[str, Any]) -> List[str]:
    """Get all unique fields across all models."""
    fields = set()
    for model_data in models.values():
      fields.update(model_data.keys())
    return sorted(fields)
  
  def get_default_columns(self) -> List[str]:
    """Get default columns for display."""
    return ['model', 'alias', 'parent', 'model_category', 'available', 'enabled']
  
  def prepare_model_data(self, name: str, data: Dict[str, Any], columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """Prepare model data for display with selected columns."""
    result = {'model': name}  # Always include model name
    
    if columns:
      for col in columns:
        if col == 'model':
          continue  # Already added
        result[col] = data.get(col, '')
    else:
      result.update(data)
    
    return result
#fin
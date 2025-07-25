"""
String-based filter implementations.
"""
import re
from typing import Any, Dict
from .base import Filter, FilterOperator

class StringFilter(Filter):
  """Filter for string-based comparisons."""
  
  def matches(self, model_data: Dict[str, Any]) -> bool:
    """Check if the model data matches this string filter."""
    field_value = self.get_field_value(model_data)
    
    # Handle None/missing values
    if field_value is None:
      if self.operator == FilterOperator.NOT_EXISTS:
        return True
      elif self.operator == FilterOperator.EXISTS:
        return False
      else:
        field_value = ""
    else:
      field_value = str(field_value)
    
    # Convert to string for comparison
    compare_value = str(self.value)
    
    # Handle case sensitivity
    if not self.case_sensitive:
      field_value = field_value.lower()
      compare_value = compare_value.lower()
    
    # Apply operator
    if self.operator == FilterOperator.EQUALS:
      return field_value == compare_value
    
    elif self.operator == FilterOperator.NOT_EQUALS:
      return field_value != compare_value
    
    elif self.operator == FilterOperator.CONTAINS:
      return compare_value in field_value
    
    elif self.operator == FilterOperator.NOT_CONTAINS:
      return compare_value not in field_value
    
    elif self.operator == FilterOperator.STARTS_WITH:
      return field_value.startswith(compare_value)
    
    elif self.operator == FilterOperator.ENDS_WITH:
      return field_value.endswith(compare_value)
    
    elif self.operator == FilterOperator.REGEX:
      flags = 0 if self.case_sensitive else re.IGNORECASE
      pattern = re.compile(self.value, flags)  # Use original value for regex
      return bool(pattern.search(field_value))
    
    elif self.operator == FilterOperator.IN:
      # Value should be a list
      if isinstance(self.value, str):
        values = [v.strip() for v in self.value.split(',')]
      else:
        values = self.value
      
      if not self.case_sensitive:
        values = [str(v).lower() for v in values]
      
      return field_value in values
    
    elif self.operator == FilterOperator.NOT_IN:
      # Value should be a list
      if isinstance(self.value, str):
        values = [v.strip() for v in self.value.split(',')]
      else:
        values = self.value
      
      if not self.case_sensitive:
        values = [str(v).lower() for v in values]
      
      return field_value not in values
    
    elif self.operator == FilterOperator.EXISTS:
      return self.get_field_value(model_data) is not None
    
    elif self.operator == FilterOperator.NOT_EXISTS:
      return self.get_field_value(model_data) is None
    
    else:
      raise ValueError(f"Unsupported string operator: {self.operator}")
#fin
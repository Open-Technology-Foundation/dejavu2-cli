"""
Base filter classes and operators.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict

class FilterOperator(Enum):
  """Available filter operators."""
  # String operators
  EQUALS = "equals"
  NOT_EQUALS = "not_equals"
  CONTAINS = "contains"
  NOT_CONTAINS = "not_contains"
  STARTS_WITH = "starts_with"
  ENDS_WITH = "ends_with"
  REGEX = "regex"
  
  # Numeric operators
  EQ = "=="
  NE = "!="
  LT = "<"
  LE = "<="
  GT = ">"
  GE = ">="
  BETWEEN = "between"
  
  # Special operators
  IN = "in"
  NOT_IN = "not_in"
  EXISTS = "exists"
  NOT_EXISTS = "not_exists"

class Filter(ABC):
  """Abstract base class for all filters."""
  
  def __init__(self, field: str, operator: FilterOperator, value: Any, case_sensitive: bool = False):
    self.field = field
    self.operator = operator
    self.value = value
    self.case_sensitive = case_sensitive
  
  @abstractmethod
  def matches(self, model_data: Dict[str, Any]) -> bool:
    """Check if the model data matches this filter."""
    pass
  
  def get_field_value(self, model_data: Dict[str, Any]) -> Any:
    """Extract field value from model data, handling nested fields."""
    if '.' not in self.field:
      return model_data.get(self.field)
    
    # Handle nested fields like "token_costs.input"
    parts = self.field.split('.')
    value = model_data
    for part in parts:
      if isinstance(value, dict):
        value = value.get(part)
      else:
        return None
    return value
  
  def __repr__(self):
    return f"{self.__class__.__name__}(field={self.field}, op={self.operator.value}, value={self.value})"
#fin
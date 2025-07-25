"""
Filter chaining logic for combining multiple filters.
"""
from typing import List, Dict, Any, Optional
from .base import Filter, FilterOperator
from .string_filters import StringFilter
from .numeric_filters import NumericFilter

class FilterChain:
  """Combines multiple filters with AND/OR logic."""
  
  def __init__(self, use_or: bool = False, negate: bool = False):
    self.filters: List[Filter] = []
    self.use_or = use_or
    self.negate = negate
  
  def add_filter(self, field: str, operator: str, value: Any, case_sensitive: bool = False):
    """Add a filter to the chain."""
    # Determine filter type based on operator or field type
    filter_obj = self._create_filter(field, operator, value, case_sensitive)
    self.filters.append(filter_obj)
  
  def _create_filter(self, field: str, operator: str, value: Any, case_sensitive: bool) -> Filter:
    """Create appropriate filter type based on operator."""
    # Map string operators to enum
    operator_map = {
      'equals': FilterOperator.EQUALS,
      'eq': FilterOperator.EQUALS,
      '==': FilterOperator.EQ,
      'not_equals': FilterOperator.NOT_EQUALS,
      'ne': FilterOperator.NOT_EQUALS,
      '!=': FilterOperator.NE,
      'contains': FilterOperator.CONTAINS,
      'not_contains': FilterOperator.NOT_CONTAINS,
      'starts_with': FilterOperator.STARTS_WITH,
      'ends_with': FilterOperator.ENDS_WITH,
      'regex': FilterOperator.REGEX,
      '<': FilterOperator.LT,
      '<=': FilterOperator.LE,
      '>': FilterOperator.GT,
      '>=': FilterOperator.GE,
      'between': FilterOperator.BETWEEN,
      'in': FilterOperator.IN,
      'not_in': FilterOperator.NOT_IN,
      'exists': FilterOperator.EXISTS,
      'not_exists': FilterOperator.NOT_EXISTS,
    }
    
    # Get operator enum
    op_enum = operator_map.get(operator.lower())
    if not op_enum:
      raise ValueError(f"Unknown operator: {operator}")
    
    # Determine filter class based on operator
    numeric_operators = {
      FilterOperator.EQ, FilterOperator.NE,
      FilterOperator.LT, FilterOperator.LE,
      FilterOperator.GT, FilterOperator.GE,
      FilterOperator.BETWEEN
    }
    
    string_operators = {
      FilterOperator.EQUALS, FilterOperator.NOT_EQUALS,
      FilterOperator.CONTAINS, FilterOperator.NOT_CONTAINS,
      FilterOperator.STARTS_WITH, FilterOperator.ENDS_WITH,
      FilterOperator.REGEX
    }
    
    # Check if it's a known numeric field
    numeric_fields = {
      'available', 'enabled', 'context_window', 'max_output_tokens',
      'vision', 'max_tokens', 'temperature', 'top_p'
    }
    
    if op_enum in numeric_operators or field in numeric_fields:
      # Try numeric filter first
      try:
        return NumericFilter(field, op_enum, value, case_sensitive)
      except ValueError:
        # Fall back to string filter if numeric parsing fails
        return StringFilter(field, op_enum, value, case_sensitive)
    else:
      return StringFilter(field, op_enum, value, case_sensitive)
  
  def matches(self, model_data: Dict[str, Any]) -> bool:
    """Check if model data matches the filter chain."""
    if not self.filters:
      return True  # No filters means match all
    
    if self.use_or:
      # OR logic: match if any filter matches
      result = any(f.matches(model_data) for f in self.filters)
    else:
      # AND logic: match only if all filters match
      result = all(f.matches(model_data) for f in self.filters)
    
    # Apply negation if requested
    return not result if self.negate else result
  
  def clear(self):
    """Clear all filters."""
    self.filters.clear()
  
  def __len__(self):
    return len(self.filters)
  
  def __repr__(self):
    logic = "OR" if self.use_or else "AND"
    neg = "NOT " if self.negate else ""
    return f"FilterChain({neg}{logic}, filters={self.filters})"
#fin
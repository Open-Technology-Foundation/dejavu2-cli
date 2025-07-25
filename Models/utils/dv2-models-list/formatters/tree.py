"""
Tree/hierarchy formatter for displaying models grouped by field.
"""
from typing import Dict, Any, List, Optional
from collections import defaultdict
from .base import ModelFormatter

class TreeFormatter(ModelFormatter):
  """Format models as a tree structure grouped by field."""
  
  def format(self, models: Dict[str, Any], group_by: Optional[str] = None,
             show_count: bool = True, **kwargs) -> str:
    """Format models as a tree grouped by specified field."""
    if not models:
      return "No models found."
    
    if not group_by:
      group_by = 'parent'  # Default grouping
    
    # Group models
    groups = defaultdict(list)
    ungrouped = []
    
    for name, data in models.items():
      group_value = data.get(group_by)
      if group_value is None or group_value == '':
        ungrouped.append((name, data))
      else:
        groups[str(group_value)].append((name, data))
    
    # Build output
    lines = []
    lines.append(f"Models grouped by '{group_by}':")
    lines.append("")
    
    # Display grouped models
    for group_name in sorted(groups.keys()):
      group_models = groups[group_name]
      if show_count:
        lines.append(f"📁 {group_name} ({len(group_models)} models)")
      else:
        lines.append(f"📁 {group_name}")
      
      # Sort models within group
      group_models.sort(key=lambda x: x[0])
      
      for i, (name, data) in enumerate(group_models):
        is_last = (i == len(group_models) - 1)
        prefix = "  └─" if is_last else "  ├─"
        
        # Build model display
        alias = data.get('alias', '')
        enabled = data.get('enabled', 0)
        available = data.get('available', 0)
        
        status_parts = []
        if enabled > 0:
          status_parts.append(f"enabled={enabled}")
        if available > 0:
          status_parts.append(f"available={available}")
        
        status = f" [{', '.join(status_parts)}]" if status_parts else ""
        alias_str = f" ({alias})" if alias else ""
        
        lines.append(f"{prefix} {name}{alias_str}{status}")
    
    # Display ungrouped models if any
    if ungrouped:
      lines.append("")
      if show_count:
        lines.append(f"📁 [No {group_by}] ({len(ungrouped)} models)")
      else:
        lines.append(f"📁 [No {group_by}]")
      
      ungrouped.sort(key=lambda x: x[0])
      
      for i, (name, data) in enumerate(ungrouped):
        is_last = (i == len(ungrouped) - 1)
        prefix = "  └─" if is_last else "  ├─"
        
        alias = data.get('alias', '')
        alias_str = f" ({alias})" if alias else ""
        
        lines.append(f"{prefix} {name}{alias_str}")
    
    # Summary
    lines.append("")
    lines.append(f"Total: {len(models)} models in {len(groups) + (1 if ungrouped else 0)} groups")
    
    return '\n'.join(lines)
#fin
# adapters/tools.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class ProjectContext(BaseModel):
    """Extracted conventions from curated repo paths."""
    naming_conventions: Dict[str, str] = Field(default_factory=dict)
    module_boundaries: List[Dict[str, str]] = Field(default_factory=list)
    auth_patterns: List[Dict[str, str]] = Field(default_factory=list)
    db_schema_snippet: Optional[str] = None

class TaskGraph(BaseModel):
    """Planner output: deterministic step sequence."""
    steps: List[Dict[str, str]] = Field(..., description="Ordered subtasks")
    context_dependencies: List[str] = Field(default_factory=list)

class CodeDiffBundle(BaseModel):
    """Generated code in unified diff format."""
    diffs: List[Dict[str, str]] = Field(..., min_items=1)
    target_paths: List[str] = Field(...)
    estimated_impact: str = "medium"  # low/medium/high

class ValidationResult(BaseModel):
    """Deterministic validation results."""
    passed: bool = False
    errors: List[Dict[str, str]] = Field(default_factory=list)
    suggestions: Optional[List[str]] = None
    confidence_score: float = 0.0
